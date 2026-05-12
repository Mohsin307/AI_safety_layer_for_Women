"""
Database Models for AI Safety Layer
SQLAlchemy models for PostgreSQL
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class EmergencyStatusDB(enum.Enum):
    INITIATED = "initiated"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Profile
    date_of_birth = Column(DateTime, nullable=True)
    profile_photo = Column(String(500), nullable=True)
    blood_group = Column(String(5), nullable=True)
    medical_conditions = Column(Text, nullable=True)
    
    # Settings
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    silent_mode_enabled = Column(Boolean, default=True)
    auto_sos_enabled = Column(Boolean, default=True)
    location_sharing_enabled = Column(Boolean, default=True)
    
    # Device info
    device_token = Column(String(500), nullable=True)
    device_type = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    emergency_contacts = relationship("EmergencyContactDB", back_populates="user")
    emergencies = relationship("EmergencyDB", back_populates="user")
    locations = relationship("LocationHistory", back_populates="user")
    behavior_profile = relationship("BehaviorProfile", back_populates="user", uselist=False)


class EmergencyContactDB(Base):
    """Emergency contacts model"""
    __tablename__ = "emergency_contacts"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    relation_type = Column(String(100), nullable=True)  # Renamed from 'relationship' to avoid conflict
    
    is_primary = Column(Boolean, default=False)
    notify_on_sos = Column(Boolean, default=True)
    share_location = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="emergency_contacts")


class EmergencyDB(Base):
    """Emergency events model"""
    __tablename__ = "emergencies"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    emergency_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(EmergencyStatusDB), default=EmergencyStatusDB.INITIATED)
    risk_level = Column(Integer, default=1)
    trigger_reason = Column(Text, nullable=True)
    
    # Location at trigger
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    
    # Response tracking
    contacts_notified = Column(JSON, default=list)
    authorities_contacted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(JSON, default=list)
    
    user = relationship("User", back_populates="emergencies")
    evidence = relationship("Evidence", back_populates="emergency")


class Evidence(Base):
    """Evidence captured during emergencies"""
    __tablename__ = "evidence"
    
    id = Column(String(36), primary_key=True)
    emergency_id = Column(String(36), ForeignKey("emergencies.id"), nullable=False)
    
    evidence_type = Column(String(50), nullable=False)  # audio, video, photo, location
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100), nullable=True)
    
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    captured_at = Column(DateTime, default=datetime.utcnow)
    
    emergency = relationship("EmergencyDB", back_populates="evidence")


class LocationHistory(Base):
    """User location history"""
    __tablename__ = "location_history"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    
    address = Column(Text, nullable=True)
    place_type = Column(String(100), nullable=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="locations")


class BehaviorProfile(Base):
    """User behavior profile for anomaly detection"""
    __tablename__ = "behavior_profiles"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    
    usual_routes = Column(JSON, default=list)
    frequent_locations = Column(JSON, default=list)
    typical_times = Column(JSON, default=dict)
    
    avg_walking_speed = Column(Float, default=1.5)
    anomaly_threshold = Column(Float, default=0.7)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="behavior_profile")


class SafeZone(Base):
    """Safe zones / safe places"""
    __tablename__ = "safe_zones"
    
    id = Column(String(36), primary_key=True)
    
    name = Column(String(255), nullable=False)
    zone_type = Column(String(100), nullable=False)  # police_station, hospital, etc.
    
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text, nullable=True)
    
    contact_phone = Column(String(20), nullable=True)
    operating_hours = Column(JSON, default=dict)
    
    is_verified = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrimeReport(Base):
    """Crime/incident reports for area analysis"""
    __tablename__ = "crime_reports"
    
    id = Column(String(36), primary_key=True)
    
    incident_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    area_id = Column(String(100), nullable=True, index=True)
    
    severity = Column(Integer, default=1)  # 1-5 scale
    
    reported_by = Column(String(36), nullable=True)  # User ID if reported by user
    is_verified = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=True)
    
    incident_date = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)


class VolunteerGuardian(Base):
    """Community volunteer guardians"""
    __tablename__ = "volunteer_guardians"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Coverage area
    coverage_latitude = Column(Float, nullable=True)
    coverage_longitude = Column(Float, nullable=True)
    coverage_radius = Column(Float, default=1000)  # meters
    
    # Availability
    available_now = Column(Boolean, default=False)
    availability_schedule = Column(JSON, default=dict)
    
    # Stats
    responses_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
