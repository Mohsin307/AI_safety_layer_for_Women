"""
Pydantic Schemas for API Request/Response
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmergencyTypeEnum(str, Enum):
    AUDIO_THREAT = "audio_threat"
    VISUAL_THREAT = "visual_threat"
    MANUAL_SOS = "manual_sos"
    SILENT_SOS = "silent_sos"
    AUTO_DETECTED = "auto_detected"
    PANIC_BUTTON = "panic_button"


class EmergencyStatusEnum(str, Enum):
    INITIATED = "initiated"
    ALERTING = "alerting_contacts"
    CAPTURING = "capturing_evidence"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    blood_group: Optional[str] = None
    medical_conditions: Optional[str] = None
    silent_mode_enabled: Optional[bool] = None
    auto_sos_enabled: Optional[bool] = None
    location_sharing_enabled: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    date_of_birth: Optional[datetime] = None
    blood_group: Optional[str] = None
    silent_mode_enabled: bool = True
    auto_sos_enabled: bool = True
    location_sharing_enabled: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# Emergency Contact Schemas
class EmergencyContactBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None


class EmergencyContactCreate(EmergencyContactBase):
    is_primary: bool = False
    notify_on_sos: bool = True
    share_location: bool = True


class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None
    notify_on_sos: Optional[bool] = None
    share_location: Optional[bool] = None


class EmergencyContactResponse(EmergencyContactBase):
    id: str
    is_primary: bool
    notify_on_sos: bool
    share_location: bool
    verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Location Schemas
class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None


class LocationCreate(LocationBase):
    address: Optional[str] = None


class LocationResponse(LocationBase):
    id: str
    address: Optional[str] = None
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# Emergency Schemas
class EmergencyTrigger(BaseModel):
    emergency_type: EmergencyTypeEnum
    location: Optional[LocationCreate] = None
    trigger_reason: Optional[str] = None
    silent_mode: bool = True


class EmergencyUpdate(BaseModel):
    location: Optional[LocationCreate] = None
    notes: Optional[str] = None


class EmergencyResolve(BaseModel):
    resolution_note: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: str
    evidence_type: str
    file_path: Optional[str] = None
    is_encrypted: bool
    captured_at: datetime
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class EmergencyResponse(BaseModel):
    id: str
    user_id: str
    emergency_type: str
    status: EmergencyStatusEnum
    risk_level: int
    trigger_reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    contacts_notified: List[str] = []
    authorities_contacted: bool = False
    evidence: List[EvidenceResponse] = []
    notes: List[str] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Risk Assessment Schemas
class RiskAssessmentRequest(BaseModel):
    location: LocationCreate
    include_safe_zones: bool = True


class SafeZoneResponse(BaseModel):
    id: str
    name: str
    zone_type: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    distance: Optional[float] = None
    rating: float = 0.0
    
    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    risk_level: RiskLevelEnum
    overall_score: float = Field(..., ge=0, le=1)
    location_risk: float
    time_risk: float
    crime_risk: float
    behavior_risk: float
    audio_visual_risk: float
    contributing_factors: List[str] = []
    recommended_actions: List[str] = []
    safe_zones_nearby: List[SafeZoneResponse] = []
    timestamp: datetime


# Safe Zone Schemas
class SafeZoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    zone_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    operating_hours: Optional[Dict] = None


class SafeZoneUpdate(BaseModel):
    name: Optional[str] = None
    contact_phone: Optional[str] = None
    operating_hours: Optional[Dict] = None


# Crime Report Schemas
class CrimeReportCreate(BaseModel):
    incident_type: str
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: int = Field(1, ge=1, le=5)
    incident_date: Optional[datetime] = None
    is_anonymous: bool = True


class CrimeReportResponse(BaseModel):
    id: str
    incident_type: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    severity: int
    is_verified: bool
    incident_date: Optional[datetime] = None
    reported_at: datetime
    
    class Config:
        from_attributes = True


# Fake Call Schemas
class FakeCallRequest(BaseModel):
    delay_seconds: int = Field(3, ge=0, le=60)
    contact_name: Optional[str] = None


class FakeCallResponse(BaseModel):
    type: str
    caller_name: str
    caller_number: str
    timestamp: datetime


# Detection Results Schemas
class AudioDetectionResponse(BaseModel):
    category: str
    confidence: float
    is_threat: bool
    risk_level: int
    timestamp: datetime


class VisualDetectionResponse(BaseModel):
    threat_type: str
    confidence: float
    is_threat: bool
    risk_level: int
    detections_count: int
    threat_details: Dict[str, Any] = {}
    timestamp: datetime


# WebSocket Schemas
class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSLocationUpdate(BaseModel):
    type: str = "location_update"
    location: LocationCreate


class WSEmergencyAlert(BaseModel):
    type: str = "emergency_alert"
    emergency_id: str
    emergency_type: str
    risk_level: int
    location: Optional[LocationCreate] = None


# API Response Wrapper
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
