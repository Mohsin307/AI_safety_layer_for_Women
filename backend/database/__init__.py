"""Database module initialization"""
from .models import (
    Base,
    User,
    EmergencyContactDB,
    EmergencyDB,
    Evidence,
    LocationHistory,
    BehaviorProfile,
    SafeZone,
    CrimeReport,
    VolunteerGuardian,
    UserStatus,
    EmergencyStatusDB
)
from .connection import DatabaseManager, db_manager, get_db

__all__ = [
    "Base",
    "User",
    "EmergencyContactDB",
    "EmergencyDB",
    "Evidence",
    "LocationHistory",
    "BehaviorProfile",
    "SafeZone",
    "CrimeReport",
    "VolunteerGuardian",
    "UserStatus",
    "EmergencyStatusDB",
    "DatabaseManager",
    "db_manager",
    "get_db"
]
