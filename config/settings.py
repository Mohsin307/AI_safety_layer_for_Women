"""
AI Safety Layer for Women - Configuration Settings
Central configuration file for all system parameters
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models" / "weights"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ThreatType(Enum):
    """Types of threats detected"""
    SCREAM = "scream"
    CRY_FOR_HELP = "cry_for_help"
    AGGRESSIVE_VOICE = "aggressive_voice"
    GLASS_BREAKING = "glass_breaking"
    GUNSHOT = "gunshot"
    WEAPON_DETECTED = "weapon_detected"
    AGGRESSIVE_GESTURE = "aggressive_gesture"
    STALKING = "stalking"
    ABNORMAL_BEHAVIOR = "abnormal_behavior"


@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int = 22050
    n_mfcc: int = 40
    n_fft: int = 2048
    hop_length: int = 512
    max_duration: float = 3.0  # seconds
    chunk_size: int = 1024
    channels: int = 1
    inference_threshold: float = 0.85
    max_latency_ms: int = 500
    supported_languages: List[str] = field(default_factory=lambda: [
        "en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"
    ])


@dataclass
class VisualConfig:
    """Visual processing configuration"""
    model_type: str = "yolov8n"  # Lightweight for edge deployment
    input_size: tuple = (640, 640)
    confidence_threshold: float = 0.7
    nms_threshold: float = 0.45
    max_latency_ms: int = 500
    enable_low_light_enhancement: bool = True
    pose_estimation_enabled: bool = True
    weapon_classes: List[str] = field(default_factory=lambda: [
        "knife", "gun", "bat", "rod", "bottle"
    ])
    aggressive_pose_threshold: float = 0.8


@dataclass
class RiskAssessmentConfig:
    """Contextual risk assessment configuration"""
    location_weight: float = 0.25
    time_weight: float = 0.20
    crime_stats_weight: float = 0.25
    behavior_weight: float = 0.15
    audio_visual_weight: float = 0.15
    anomaly_threshold: float = 0.75
    risk_update_interval: int = 30  # seconds
    geofence_radius: int = 100  # meters


@dataclass
class EmergencyConfig:
    """Emergency response configuration"""
    auto_sos_threshold: RiskLevel = RiskLevel.HIGH
    silent_mode_default: bool = True
    evidence_capture_duration: int = 30  # seconds
    location_share_interval: int = 5  # seconds
    fake_call_delay: int = 3  # seconds
    max_trusted_contacts: int = 5
    police_api_endpoint: str = ""
    ambulance_api_endpoint: str = ""
    women_helpline: str = "1091"
    emergency_number: str = "112"


@dataclass
class PrivacyConfig:
    """Privacy and security configuration"""
    enable_local_processing: bool = True
    encrypt_evidence: bool = True
    evidence_retention_days: int = 30
    anonymize_location_history: bool = True
    secure_transmission: bool = True
    encryption_algorithm: str = "AES-256-GCM"


@dataclass
class SystemConfig:
    """Main system configuration"""
    audio: AudioConfig = field(default_factory=AudioConfig)
    visual: VisualConfig = field(default_factory=VisualConfig)
    risk: RiskAssessmentConfig = field(default_factory=RiskAssessmentConfig)
    emergency: EmergencyConfig = field(default_factory=EmergencyConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/safety_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/safety_incidents")
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Notification settings
    fcm_server_key: str = os.getenv("FCM_SERVER_KEY", "")
    websocket_enabled: bool = True
    
    # Model paths
    audio_model_path: str = str(MODELS_DIR / "audio_threat_model.h5")
    visual_model_path: str = str(MODELS_DIR / "yolov8_weapon_detector.pt")
    pose_model_path: str = str(MODELS_DIR / "pose_estimator.pt")


# Global configuration instance
config = SystemConfig()
