"""
Integrated Safety System
Main orchestrator that combines all AI modules for real-time threat detection and response
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from ai_modules.audio_detection import (
    AudioThreatDetector,
    AudioDetectionResult,
    RealtimeAudioProcessor,
    AudioStreamConfig,
    create_audio_detector
)
from ai_modules.visual_detection import (
    VisualThreatDetector,
    VisualDetectionResult,
    create_visual_detector
)
from ai_modules.risk_assessment import (
    ContextualRiskAssessor,
    RiskAssessmentResult,
    RiskLevel,
    Location,
    create_risk_assessor
)
from ai_modules.emergency_response import (
    EmergencyResponseEngine,
    EmergencyEvent,
    EmergencyType,
    EmergencyContact,
    LocationData,
    create_emergency_engine
)
from ai_modules.community import (
    CommunitySafetyNetwork,
    create_community_network
)
from config import config

logger = logging.getLogger(__name__)


@dataclass
class IntegratedDetectionResult:
    """Combined result from all detection systems"""
    timestamp: float
    
    # Individual results
    audio_result: Optional[AudioDetectionResult] = None
    visual_result: Optional[VisualDetectionResult] = None
    risk_result: Optional[RiskAssessmentResult] = None
    
    # Combined assessment
    is_threat: bool = False
    combined_risk_level: int = 0
    threat_sources: list = None
    recommended_action: str = ""
    
    def __post_init__(self):
        if self.threat_sources is None:
            self.threat_sources = []


class IntegratedSafetySystem:
    """
    Main integrated safety system that orchestrates all AI modules
    Provides real-time threat detection and automatic emergency response
    """
    
    def __init__(
        self,
        audio_model_path: Optional[str] = None,
        visual_model_path: Optional[str] = None,
        enable_audio: bool = True,
        enable_visual: bool = True,
        auto_emergency_threshold: int = 3  # Risk level to auto-trigger emergency
    ):
        """
        Initialize integrated safety system
        
        Args:
            audio_model_path: Path to audio detection model
            visual_model_path: Path to visual detection model
            enable_audio: Enable audio threat detection
            enable_visual: Enable visual threat detection
            auto_emergency_threshold: Risk level threshold for auto emergency
        """
        self.enable_audio = enable_audio
        self.enable_visual = enable_visual
        self.auto_emergency_threshold = auto_emergency_threshold
        
        # Initialize AI modules
        self.audio_detector = create_audio_detector(audio_model_path) if enable_audio else None
        self.visual_detector = create_visual_detector(visual_model_path) if enable_visual else None
        self.risk_assessor = create_risk_assessor()
        self.emergency_engine = create_emergency_engine()
        self.community_network = create_community_network()
        
        # Real-time processors
        self.audio_processor: Optional[RealtimeAudioProcessor] = None
        
        # State tracking
        self.is_running = False
        self.current_location: Optional[Location] = None
        self.user_id: Optional[str] = None
        self.emergency_contacts: list = []
        
        # Detection history
        self.recent_detections: list = []
        self.max_history = 100
        
        # Callbacks
        self.on_threat_detected: Optional[Callable[[IntegratedDetectionResult], Any]] = None
        self.on_emergency_triggered: Optional[Callable[[EmergencyEvent], Any]] = None
        self.on_risk_level_changed: Optional[Callable[[RiskLevel], Any]] = None
        
        # Current state
        self.current_risk_level = RiskLevel.LOW
        self.active_emergency: Optional[EmergencyEvent] = None
        
        logger.info("Integrated Safety System initialized")
    
    def configure_user(
        self,
        user_id: str,
        contacts: list,
        location: Optional[Location] = None
    ):
        """Configure user settings"""
        self.user_id = user_id
        self.emergency_contacts = [
            EmergencyContact(
                id=c.get('id', ''),
                name=c.get('name', ''),
                phone=c.get('phone', ''),
                email=c.get('email'),
                relationship=c.get('relationship', ''),
                is_primary=c.get('is_primary', False),
                notify_on_sos=c.get('notify_on_sos', True),
                share_location=c.get('share_location', True)
            )
            for c in contacts
        ]
        if location:
            self.current_location = location
    
    def update_location(self, latitude: float, longitude: float, accuracy: float = 0.0):
        """Update current location"""
        self.current_location = Location(
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            timestamp=time.time()
        )
    
    async def start(self):
        """Start the integrated safety system"""
        if self.is_running:
            logger.warning("System already running")
            return
        
        self.is_running = True
        logger.info("Starting Integrated Safety System...")
        
        # Start audio processing
        if self.enable_audio and self.audio_detector:
            self.audio_processor = RealtimeAudioProcessor(
                detector=self.audio_detector,
                config=AudioStreamConfig(),
                on_threat_detected=self._handle_audio_threat
            )
            if self.audio_processor.start():
                logger.info("Audio processing started")
            else:
                logger.warning("Failed to start audio processing")
        
        logger.info("Integrated Safety System started")
    
    async def stop(self):
        """Stop the integrated safety system"""
        self.is_running = False
        
        if self.audio_processor:
            self.audio_processor.stop()
            self.audio_processor = None
        
        logger.info("Integrated Safety System stopped")
    
    def _handle_audio_threat(self, result: AudioDetectionResult):
        """Handle detected audio threat"""
        asyncio.create_task(self._process_threat_detection(
            audio_result=result
        ))
    
    async def process_visual_frame(self, frame) -> Optional[VisualDetectionResult]:
        """Process a visual frame for threat detection"""
        if not self.enable_visual or not self.visual_detector:
            return None
        
        result = self.visual_detector.detect_threats(frame, time.time())
        
        if result.is_threat:
            await self._process_threat_detection(visual_result=result)
        
        return result
    
    async def _process_threat_detection(
        self,
        audio_result: Optional[AudioDetectionResult] = None,
        visual_result: Optional[VisualDetectionResult] = None
    ):
        """Process detected threats and coordinate response"""
        # Perform risk assessment
        risk_result = None
        if self.current_location:
            # Combine audio/visual risk into assessment
            av_risk = 0.0
            if audio_result and audio_result.is_threat:
                av_risk = max(av_risk, audio_result.risk_level / 4.0)
            if visual_result and visual_result.is_threat:
                av_risk = max(av_risk, visual_result.risk_level / 4.0)
            
            risk_result = self.risk_assessor.assess_risk(
                location=self.current_location,
                audio_visual_risk=av_risk
            )
        
        # Create integrated result
        threat_sources = []
        combined_risk = 0
        
        if audio_result and audio_result.is_threat:
            threat_sources.append(f"audio:{audio_result.category.name}")
            combined_risk = max(combined_risk, audio_result.risk_level)
        
        if visual_result and visual_result.is_threat:
            threat_sources.append(f"visual:{visual_result.threat_type.name}")
            combined_risk = max(combined_risk, visual_result.risk_level)
        
        if risk_result:
            combined_risk = max(
                combined_risk,
                {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, 
                 RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}[risk_result.risk_level]
            )
        
        is_threat = len(threat_sources) > 0
        
        # Determine recommended action
        if combined_risk >= 4:
            recommended_action = "trigger_emergency"
        elif combined_risk >= 3:
            recommended_action = "alert_contacts"
        elif combined_risk >= 2:
            recommended_action = "increase_monitoring"
        else:
            recommended_action = "continue_monitoring"
        
        integrated_result = IntegratedDetectionResult(
            timestamp=time.time(),
            audio_result=audio_result,
            visual_result=visual_result,
            risk_result=risk_result,
            is_threat=is_threat,
            combined_risk_level=combined_risk,
            threat_sources=threat_sources,
            recommended_action=recommended_action
        )
        
        # Add to history
        self.recent_detections.append(integrated_result)
        if len(self.recent_detections) > self.max_history:
            self.recent_detections.pop(0)
        
        # Check for risk level change
        new_risk_level = {
            1: RiskLevel.LOW,
            2: RiskLevel.MEDIUM,
            3: RiskLevel.HIGH,
            4: RiskLevel.CRITICAL
        }.get(combined_risk, RiskLevel.LOW)
        
        if new_risk_level != self.current_risk_level:
            self.current_risk_level = new_risk_level
            if self.on_risk_level_changed:
                await self._safe_callback(self.on_risk_level_changed, new_risk_level)
        
        # Trigger callback
        if is_threat and self.on_threat_detected:
            await self._safe_callback(self.on_threat_detected, integrated_result)
        
        # Auto-trigger emergency if threshold exceeded
        if combined_risk >= self.auto_emergency_threshold and not self.active_emergency:
            await self._auto_trigger_emergency(integrated_result)
    
    async def _auto_trigger_emergency(self, detection: IntegratedDetectionResult):
        """Automatically trigger emergency based on threat detection"""
        if not self.user_id:
            logger.warning("Cannot auto-trigger emergency: no user configured")
            return
        
        # Determine emergency type
        if detection.audio_result and detection.audio_result.is_threat:
            emergency_type = EmergencyType.AUDIO_THREAT
        elif detection.visual_result and detection.visual_result.is_threat:
            emergency_type = EmergencyType.VISUAL_THREAT
        else:
            emergency_type = EmergencyType.AUTO_DETECTED
        
        # Prepare location
        location = None
        if self.current_location:
            location = LocationData(
                latitude=self.current_location.latitude,
                longitude=self.current_location.longitude,
                accuracy=self.current_location.accuracy,
                timestamp=self.current_location.timestamp
            )
        
        # Trigger emergency
        trigger_reason = ", ".join(detection.threat_sources)
        
        self.active_emergency = await self.emergency_engine.trigger_emergency(
            user_id=self.user_id,
            emergency_type=emergency_type,
            risk_level=detection.combined_risk_level,
            trigger_reason=trigger_reason,
            location=location,
            contacts=self.emergency_contacts,
            silent_mode=True
        )
        
        logger.info(f"Auto-triggered emergency: {self.active_emergency.id}")
        
        # Coordinate community response
        if self.current_location:
            await self.community_network.handle_emergency_community_response(
                self.active_emergency.id,
                self.current_location.latitude,
                self.current_location.longitude,
                trigger_reason
            )
        
        if self.on_emergency_triggered:
            await self._safe_callback(self.on_emergency_triggered, self.active_emergency)
    
    async def manual_sos(self, silent: bool = True) -> EmergencyEvent:
        """Manually trigger SOS"""
        if not self.user_id:
            raise ValueError("User not configured")
        
        location = None
        if self.current_location:
            location = LocationData(
                latitude=self.current_location.latitude,
                longitude=self.current_location.longitude,
                accuracy=self.current_location.accuracy
            )
        
        self.active_emergency = await self.emergency_engine.trigger_emergency(
            user_id=self.user_id,
            emergency_type=EmergencyType.MANUAL_SOS if not silent else EmergencyType.SILENT_SOS,
            risk_level=4,  # CRITICAL
            trigger_reason="Manual SOS activation",
            location=location,
            contacts=self.emergency_contacts,
            silent_mode=silent
        )
        
        return self.active_emergency
    
    async def cancel_emergency(self, reason: str = "User cancelled"):
        """Cancel active emergency"""
        if self.active_emergency:
            await self.emergency_engine.cancel_emergency(
                self.active_emergency.id,
                reason
            )
            self.active_emergency = None
    
    async def resolve_emergency(self, note: str = ""):
        """Resolve active emergency"""
        if self.active_emergency:
            await self.emergency_engine.resolve_emergency(
                self.active_emergency.id,
                note
            )
            self.active_emergency = None
    
    async def trigger_fake_call(self, delay: int = 3) -> Dict:
        """Trigger a fake incoming call"""
        return await self.emergency_engine.trigger_fake_call(delay)
    
    def get_current_risk(self) -> RiskAssessmentResult:
        """Get current risk assessment"""
        if self.current_location:
            return self.risk_assessor.assess_risk(self.current_location)
        return RiskAssessmentResult(
            risk_level=RiskLevel.LOW,
            overall_score=0.0,
            location_risk=0.0,
            time_risk=0.0,
            crime_risk=0.0,
            behavior_risk=0.0,
            audio_visual_risk=0.0,
            timestamp=time.time()
        )
    
    def get_nearby_safe_zones(self, radius_km: float = 2.0) -> list:
        """Get nearby safe zones"""
        if not self.current_location:
            return []
        
        zones = self.community_network.safe_zone_manager.find_nearby_zones(
            self.current_location.latitude,
            self.current_location.longitude,
            radius_km
        )
        
        return [
            {
                'id': z[0].id,
                'name': z[0].name,
                'type': z[0].zone_type,
                'distance_km': z[1],
                'address': z[0].address,
                'phone': z[0].contact_phone
            }
            for z in zones
        ]
    
    def get_area_safety_summary(self) -> Dict:
        """Get safety summary for current area"""
        if not self.current_location:
            return {"error": "Location not available"}
        
        return self.community_network.get_area_safety_summary(
            self.current_location.latitude,
            self.current_location.longitude
        )
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        stats = {
            'is_running': self.is_running,
            'audio_enabled': self.enable_audio,
            'visual_enabled': self.enable_visual,
            'current_risk_level': self.current_risk_level.name,
            'active_emergency': self.active_emergency.id if self.active_emergency else None,
            'detections_count': len(self.recent_detections),
            'threats_detected': sum(1 for d in self.recent_detections if d.is_threat)
        }
        
        if self.audio_processor:
            stats['audio_stats'] = self.audio_processor.get_stats()
        
        return stats
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")


# Factory function
def create_integrated_system(
    audio_model_path: Optional[str] = None,
    visual_model_path: Optional[str] = None,
    **kwargs
) -> IntegratedSafetySystem:
    """Create integrated safety system instance"""
    return IntegratedSafetySystem(
        audio_model_path=audio_model_path,
        visual_model_path=visual_model_path,
        **kwargs
    )
