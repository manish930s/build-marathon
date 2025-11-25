import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)  # For authentication
    role = Column(String)  # "elderly" or "caregiver"
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vitals = relationship("Vital", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class Vital(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String)
    value = Column(Float)
    unit = Column(String)
    is_abnormal = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="vitals")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    severity = Column(String)
    message = Column(Text)
    resolved = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="alerts")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
