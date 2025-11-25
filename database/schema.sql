-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table (Elderly and Caregivers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('elderly', 'caregiver', 'admin')),
    full_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Health Vitals Table
CREATE TABLE vitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) NOT NULL, -- e.g., 'heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'spo2', 'glucose'
    value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(20),
    is_abnormal BOOLEAN DEFAULT FALSE
);

-- Alerts Table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Thresholds Configuration (Simple rules)
CREATE TABLE thresholds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    vital_type VARCHAR(50) NOT NULL,
    min_value NUMERIC(10, 2),
    max_value NUMERIC(10, 2),
    UNIQUE(user_id, vital_type)
);

-- Seed Data
INSERT INTO users (username, role, full_name) VALUES 
('grandpa_joe', 'elderly', 'Joe Smith'),
('nurse_sarah', 'caregiver', 'Sarah Jones');

-- Example Thresholds for Joe
INSERT INTO thresholds (user_id, vital_type, min_value, max_value) 
SELECT id, 'heart_rate', 50, 100 FROM users WHERE username = 'grandpa_joe';

INSERT INTO thresholds (user_id, vital_type, min_value, max_value) 
SELECT id, 'spo2', 90, 100 FROM users WHERE username = 'grandpa_joe';
