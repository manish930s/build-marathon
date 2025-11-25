from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles

"""
PROJECT: AI Elderly Health Companion
COMPONENT: Health Data Processing API (FastAPI Backend)

DESCRIPTION:
This API serves as the central hub for the Health Companion application.
It handles:
1.  Health Data Ingestion: Receives vital signs (HR, BP, SpO2) from the frontend.
2.  Data Processing: Analyzes vitals for abnormalities and triggers alerts.
3.  AI Integration: Routes chat messages to the Gemini Health Agent.
4.  User Management: Handles authentication for elderly users and caregivers.

ENDPOINTS:
-   POST /api/v1/ingest: Process new health data.
-   POST /api/v1/chat: Interact with the AI Health Companion.
-   GET /api/v1/dashboard/{username}: Retrieve processed health insights.
"""

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import database
from database import get_db, User, Vital, Alert
from gemini_health_agent import agent

app = FastAPI(title="AI Elderly Health Companion")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# --- Pydantic Models ---
class VitalInput(BaseModel):
    username: str
    type: str
    value: float
    unit: str

class ChatRequest(BaseModel):
    username: str
    message: str

class ChatResponse(BaseModel):
    response: str

class SignupRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "elderly"

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    full_name: str
    role: str

# --- Startup ---
@app.on_event("startup")
def startup():
    database.init_db()
    # Seed data if empty (simplified)
    db = database.SessionLocal()
    if not db.query(User).first():
        # Create default users with hashed passwords
        hashed_pw = pwd_context.hash("password123")
        db.add(User(username="grandpa_joe", password_hash=hashed_pw, role="elderly", full_name="Joe Smith"))
        db.add(User(username="nurse_sarah", password_hash=hashed_pw, role="caregiver", full_name="Sarah Jones"))
        db.commit()
    db.close()

# --- Endpoints ---



# Authentication Endpoints
@app.post("/api/v1/auth/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    hashed_password = pwd_context.hash(request.password)
    
    # Create new user
    new_user = User(
        username=request.username,
        password_hash=hashed_password,
        full_name=request.full_name,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "username": new_user.username}

@app.post("/api/v1/auth/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return UserResponse(
        username=user.username,
        full_name=user.full_name,
        role=user.role
    )

@app.post("/api/v1/ingest")
def ingest_vital(data: VitalInput, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # ==========================================
    # ALERT GENERATION LOGIC
    # ==========================================
    # Checks thresholds for HR, BP, SpO2, Glucose, Temp
    # Generates Alert records if abnormal
    # ==========================================
    # Basic Threshold Check (Mock Logic)
    is_abnormal = False
    alert_msg = ""
    
    if data.type == "heart_rate" and (data.value < 50 or data.value > 100):
        is_abnormal = True
        alert_msg = f"Abnormal HR detected ({data.value} bpm)"
    elif data.type == "blood_pressure_sys" and (data.value < 90 or data.value > 140):
        is_abnormal = True
        alert_msg = f"Abnormal BP (Sys) detected ({data.value} mmHg)"
    elif data.type == "blood_pressure_dia" and (data.value < 60 or data.value > 90):
        is_abnormal = True
        alert_msg = f"Abnormal BP (Dia) detected ({data.value} mmHg)"
    elif data.type == "spo2" and data.value < 95:
        is_abnormal = True
        alert_msg = f"Low SpO2 detected ({data.value}%)"
    elif data.type == "glucose" and data.value > 140:
        is_abnormal = True
        alert_msg = f"High Glucose detected ({data.value} mg/dL)"
    elif data.type == "temperature" and data.value > 99.5:
        is_abnormal = True
        alert_msg = f"High Temperature detected ({data.value}°F)"

    if is_abnormal:
        alert = Alert(
            user_id=user.id, 
            severity="medium", 
            message=alert_msg
        )
        db.add(alert)
    
    new_vital = Vital(
        user_id=user.id,
        type=data.type,
        value=data.value,
        unit=data.unit,
        is_abnormal=is_abnormal
    )
    db.add(new_vital)
    db.commit()
    
    return {"status": "recorded", "abnormal": is_abnormal}

@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    response_text = agent.chat(request.message, request.username)
    return {"response": response_text}

@app.get("/api/v1/dashboard/{username}")
def get_dashboard(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    recent_vitals = db.query(Vital).filter(Vital.user_id == user.id).order_by(Vital.timestamp.desc()).limit(50).all()
    recent_alerts = db.query(Alert).filter(Alert.user_id == user.id).order_by(Alert.created_at.desc()).limit(5).all()
    
    # Format alerts with proper UTC timestamps
    formatted_alerts = []
    for alert in recent_alerts:
        formatted_alerts.append({
            "id": alert.id,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat() + 'Z' if alert.created_at else None,  # Add 'Z' for UTC
            "resolved": alert.resolved
        })
    
    return {
        "user": user.full_name,
        "vitals": recent_vitals,
        "alerts": formatted_alerts
    }


# Mount static files (Frontend)
app.mount('/', StaticFiles(directory='static', html=True), name='static')

