"""
Emergency Response Engine
Orchestrates emergency responses based on detected threats
Handles: SOS activation, Evidence capture, Alerts, Fake calls
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EmergencyType(Enum):
    """Types of emergency situations"""
    AUDIO_THREAT = "audio_threat"
    VISUAL_THREAT = "visual_threat"
    MANUAL_SOS = "manual_sos"
    SILENT_SOS = "silent_sos"
    AUTO_DETECTED = "auto_detected"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    PANIC_BUTTON = "panic_button"


class EmergencyStatus(Enum):
    """Status of emergency response"""
    INITIATED = "initiated"
    ALERTING_CONTACTS = "alerting_contacts"
    CAPTURING_EVIDENCE = "capturing_evidence"
    CONTACTING_AUTHORITIES = "contacting_authorities"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


@dataclass
class EmergencyContact:
    """Trusted emergency contact"""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    relationship: str = "emergency_contact"
    is_primary: bool = False
    notify_on_sos: bool = True
    share_location: bool = True


@dataclass
class EvidenceData:
    """Captured evidence during emergency"""
    id: str
    emergency_id: str
    evidence_type: str  # audio, video, photo, location
    file_path: Optional[str] = None
    data: Optional[bytes] = None
    timestamp: float = 0.0
    metadata: Dict = field(default_factory=dict)
    is_encrypted: bool = True


@dataclass
class LocationData:
    """Location data for emergency"""
    latitude: float
    longitude: float
    accuracy: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: float = 0.0
    address: Optional[str] = None


@dataclass
class EmergencyEvent:
    """Complete emergency event record"""
    id: str
    user_id: str
    emergency_type: EmergencyType
    status: EmergencyStatus
    risk_level: int
    trigger_reason: str
    location: Optional[LocationData] = None
    evidence: List[EvidenceData] = field(default_factory=list)
    contacts_notified: List[str] = field(default_factory=list)
    authorities_contacted: bool = False
    created_at: float = 0.0
    updated_at: float = 0.0
    resolved_at: Optional[float] = None
    notes: List[str] = field(default_factory=list)


class NotificationService:
    """
    Handles sending notifications to contacts and authorities
    """
    
    def __init__(
        self,
        sms_provider: Optional[Any] = None,
        push_provider: Optional[Any] = None
    ):
        self.sms_provider = sms_provider
        self.push_provider = push_provider
    
    async def send_sms(
        self,
        phone: str,
        message: str,
        priority: str = "high"
    ) -> bool:
        """Send SMS notification"""
        try:
            logger.info(f"Sending SMS to {phone}: {message[:50]}...")
            # Integration with SMS provider (Twilio, etc.)
            if self.sms_provider:
                await self.sms_provider.send(phone, message, priority)
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False
    
    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """Send push notification via FCM"""
        try:
            logger.info(f"Sending push notification to {user_id}")
            if self.push_provider:
                await self.push_provider.send(user_id, title, body, data)
            return True
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    
    async def send_emergency_alert(
        self,
        contact: EmergencyContact,
        event: EmergencyEvent,
        location: Optional[LocationData] = None
    ) -> bool:
        """Send comprehensive emergency alert to contact"""
        # Construct message
        message = self._construct_emergency_message(event, location)
        
        # Send via multiple channels
        results = await asyncio.gather(
            self.send_sms(contact.phone, message),
            self.send_push_notification(
                contact.id,
                "🚨 EMERGENCY ALERT",
                message,
                {"event_id": event.id, "location": location.__dict__ if location else None}
            ),
            return_exceptions=True
        )
        
        return any(r is True for r in results)
    
    def _construct_emergency_message(
        self,
        event: EmergencyEvent,
        location: Optional[LocationData]
    ) -> str:
        """Construct emergency message"""
        msg = f"🚨 EMERGENCY ALERT\n"
        msg += f"Time: {datetime.fromtimestamp(event.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        msg += f"Type: {event.emergency_type.value}\n"
        msg += f"Risk Level: {'⚠️' * event.risk_level}\n"
        
        if location:
            msg += f"\n📍 Location:\n"
            msg += f"https://maps.google.com/?q={location.latitude},{location.longitude}\n"
            if location.address:
                msg += f"Address: {location.address}\n"
        
        msg += f"\nPlease respond immediately!"
        return msg


class EvidenceCaptureService:
    """
    Handles capturing and securing evidence during emergencies
    """
    
    def __init__(
        self,
        storage_path: str = "./evidence",
        encrypt: bool = True
    ):
        self.storage_path = storage_path
        self.encrypt = encrypt
        self.active_captures: Dict[str, bool] = {}
    
    async def start_audio_capture(
        self,
        emergency_id: str,
        duration: int = 30
    ) -> EvidenceData:
        """Start audio evidence capture"""
        evidence_id = str(uuid.uuid4())
        
        logger.info(f"Starting audio capture for emergency {emergency_id}")
        self.active_captures[evidence_id] = True
        
        # Simulated capture - would integrate with audio system
        await asyncio.sleep(min(duration, 5))  # Reduced for demo
        
        evidence = EvidenceData(
            id=evidence_id,
            emergency_id=emergency_id,
            evidence_type="audio",
            file_path=f"{self.storage_path}/{emergency_id}/audio_{evidence_id}.enc",
            timestamp=time.time(),
            metadata={
                "duration": duration,
                "sample_rate": 22050,
                "channels": 1
            },
            is_encrypted=self.encrypt
        )
        
        self.active_captures.pop(evidence_id, None)
        return evidence
    
    async def start_video_capture(
        self,
        emergency_id: str,
        duration: int = 30
    ) -> EvidenceData:
        """Start video evidence capture"""
        evidence_id = str(uuid.uuid4())
        
        logger.info(f"Starting video capture for emergency {emergency_id}")
        self.active_captures[evidence_id] = True
        
        # Simulated capture
        await asyncio.sleep(min(duration, 5))
        
        evidence = EvidenceData(
            id=evidence_id,
            emergency_id=emergency_id,
            evidence_type="video",
            file_path=f"{self.storage_path}/{emergency_id}/video_{evidence_id}.enc",
            timestamp=time.time(),
            metadata={
                "duration": duration,
                "resolution": "720p",
                "fps": 30
            },
            is_encrypted=self.encrypt
        )
        
        self.active_captures.pop(evidence_id, None)
        return evidence
    
    async def capture_photo(self, emergency_id: str) -> EvidenceData:
        """Capture photo evidence"""
        evidence_id = str(uuid.uuid4())
        
        evidence = EvidenceData(
            id=evidence_id,
            emergency_id=emergency_id,
            evidence_type="photo",
            file_path=f"{self.storage_path}/{emergency_id}/photo_{evidence_id}.enc",
            timestamp=time.time(),
            is_encrypted=self.encrypt
        )
        
        return evidence
    
    async def capture_location_trail(
        self,
        emergency_id: str,
        locations: List[LocationData]
    ) -> EvidenceData:
        """Capture location trail as evidence"""
        evidence_id = str(uuid.uuid4())
        
        evidence = EvidenceData(
            id=evidence_id,
            emergency_id=emergency_id,
            evidence_type="location_trail",
            file_path=f"{self.storage_path}/{emergency_id}/locations_{evidence_id}.enc",
            timestamp=time.time(),
            metadata={
                "point_count": len(locations),
                "start_time": locations[0].timestamp if locations else 0,
                "end_time": locations[-1].timestamp if locations else 0
            },
            is_encrypted=self.encrypt
        )
        
        return evidence
    
    def stop_capture(self, evidence_id: str) -> None:
        """Stop an active capture"""
        self.active_captures[evidence_id] = False


class FakeCallService:
    """
    Generates fake incoming calls for user safety
    """
    
    def __init__(self):
        self.fake_contacts = [
            {"name": "Mom", "number": "+1234567890"},
            {"name": "Dad", "number": "+1234567891"},
            {"name": "Office", "number": "+1234567892"},
            {"name": "Home", "number": "+1234567893"}
        ]
    
    async def trigger_fake_call(
        self,
        delay: int = 3,
        contact_name: Optional[str] = None
    ) -> Dict:
        """
        Trigger a fake incoming call after delay
        
        Args:
            delay: Seconds before fake call
            contact_name: Caller name to display
            
        Returns:
            Call details
        """
        await asyncio.sleep(delay)
        
        if contact_name:
            contact = next(
                (c for c in self.fake_contacts if c['name'] == contact_name),
                self.fake_contacts[0]
            )
        else:
            contact = self.fake_contacts[0]
        
        call_details = {
            "type": "fake_call",
            "caller_name": contact['name'],
            "caller_number": contact['number'],
            "timestamp": time.time()
        }
        
        logger.info(f"Triggering fake call from {contact['name']}")
        return call_details
    
    async def send_fake_message(
        self,
        message_template: str = "Hey, where are you? I'm waiting."
    ) -> Dict:
        """Send a fake message notification"""
        contact = self.fake_contacts[0]
        
        message_details = {
            "type": "fake_message",
            "sender_name": contact['name'],
            "message": message_template,
            "timestamp": time.time()
        }
        
        logger.info(f"Sending fake message from {contact['name']}")
        return message_details


class AuthorityContactService:
    """
    Handles contacting emergency authorities
    """
    
    def __init__(
        self,
        police_api: Optional[str] = None,
        ambulance_api: Optional[str] = None
    ):
        self.police_api = police_api
        self.ambulance_api = ambulance_api
        
        # Emergency numbers
        self.emergency_numbers = {
            "police": "100",
            "women_helpline": "1091",
            "ambulance": "108",
            "emergency": "112"
        }
    
    async def contact_police(
        self,
        event: EmergencyEvent,
        location: LocationData
    ) -> bool:
        """Contact police with emergency details"""
        try:
            logger.info(f"Contacting police for emergency {event.id}")
            
            # In production, this would integrate with police API
            # For now, log the contact attempt
            alert_data = {
                "emergency_id": event.id,
                "type": event.emergency_type.value,
                "location": {
                    "lat": location.latitude,
                    "lng": location.longitude,
                    "address": location.address
                },
                "timestamp": time.time(),
                "risk_level": event.risk_level
            }
            
            logger.info(f"Police alert data: {json.dumps(alert_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to contact police: {e}")
            return False
    
    async def contact_women_helpline(
        self,
        event: EmergencyEvent,
        location: LocationData
    ) -> bool:
        """Contact women's helpline"""
        try:
            logger.info(f"Contacting women helpline for emergency {event.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to contact women helpline: {e}")
            return False
    
    def get_emergency_number(self, service: str) -> str:
        """Get emergency number for service"""
        return self.emergency_numbers.get(service, "112")


class EmergencyResponseEngine:
    """
    Main emergency response orchestration engine
    Coordinates all emergency response actions
    """
    
    def __init__(
        self,
        notification_service: Optional[NotificationService] = None,
        evidence_service: Optional[EvidenceCaptureService] = None,
        fake_call_service: Optional[FakeCallService] = None,
        authority_service: Optional[AuthorityContactService] = None,
        auto_authority_contact: bool = False
    ):
        self.notification_service = notification_service or NotificationService()
        self.evidence_service = evidence_service or EvidenceCaptureService()
        self.fake_call_service = fake_call_service or FakeCallService()
        self.authority_service = authority_service or AuthorityContactService()
        
        self.auto_authority_contact = auto_authority_contact
        
        # Active emergencies
        self.active_emergencies: Dict[str, EmergencyEvent] = {}
        
        # Event callbacks
        self.on_emergency_started: Optional[Callable] = None
        self.on_emergency_updated: Optional[Callable] = None
        self.on_emergency_resolved: Optional[Callable] = None
    
    async def trigger_emergency(
        self,
        user_id: str,
        emergency_type: EmergencyType,
        risk_level: int,
        trigger_reason: str,
        location: Optional[LocationData] = None,
        contacts: Optional[List[EmergencyContact]] = None,
        silent_mode: bool = True
    ) -> EmergencyEvent:
        """
        Trigger a new emergency response
        
        Args:
            user_id: User ID triggering emergency
            emergency_type: Type of emergency
            risk_level: Risk level (1-4)
            trigger_reason: Reason for emergency trigger
            location: Current location data
            contacts: Emergency contacts to notify
            silent_mode: If True, no visible alerts on device
            
        Returns:
            EmergencyEvent object
        """
        emergency_id = str(uuid.uuid4())
        
        event = EmergencyEvent(
            id=emergency_id,
            user_id=user_id,
            emergency_type=emergency_type,
            status=EmergencyStatus.INITIATED,
            risk_level=risk_level,
            trigger_reason=trigger_reason,
            location=location,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.active_emergencies[emergency_id] = event
        logger.info(f"Emergency {emergency_id} initiated: {emergency_type.value}")
        
        if self.on_emergency_started:
            await self._safe_callback(self.on_emergency_started, event)
        
        # Start response workflow
        asyncio.create_task(self._execute_response_workflow(
            event, contacts, silent_mode
        ))
        
        return event
    
    async def _execute_response_workflow(
        self,
        event: EmergencyEvent,
        contacts: Optional[List[EmergencyContact]],
        silent_mode: bool
    ) -> None:
        """Execute the emergency response workflow"""
        try:
            # 1. Start evidence capture
            event.status = EmergencyStatus.CAPTURING_EVIDENCE
            event.updated_at = time.time()
            
            evidence_tasks = [
                self.evidence_service.start_audio_capture(event.id, duration=30),
                self.evidence_service.start_video_capture(event.id, duration=30)
            ]
            
            if event.location:
                evidence_tasks.append(
                    self.evidence_service.capture_photo(event.id)
                )
            
            # Don't wait for evidence - run in background
            asyncio.create_task(self._collect_evidence(event, evidence_tasks))
            
            # 2. Alert contacts
            if contacts:
                event.status = EmergencyStatus.ALERTING_CONTACTS
                event.updated_at = time.time()
                
                await self._notify_contacts(event, contacts)
            
            # 3. Contact authorities if high risk or auto-enabled
            if event.risk_level >= 4 or self.auto_authority_contact:
                event.status = EmergencyStatus.CONTACTING_AUTHORITIES
                event.updated_at = time.time()
                
                if event.location:
                    await self.authority_service.contact_police(event, event.location)
                    await self.authority_service.contact_women_helpline(event, event.location)
                    event.authorities_contacted = True
            
            # 4. Set active status
            event.status = EmergencyStatus.ACTIVE
            event.updated_at = time.time()
            
            if self.on_emergency_updated:
                await self._safe_callback(self.on_emergency_updated, event)
                
        except Exception as e:
            logger.error(f"Error in emergency workflow: {e}")
            event.notes.append(f"Workflow error: {str(e)}")
    
    async def _collect_evidence(
        self,
        event: EmergencyEvent,
        tasks: List
    ) -> None:
        """Collect evidence from capture tasks"""
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, EvidenceData):
                event.evidence.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Evidence capture error: {result}")
        
        event.updated_at = time.time()
    
    async def _notify_contacts(
        self,
        event: EmergencyEvent,
        contacts: List[EmergencyContact]
    ) -> None:
        """Notify all emergency contacts"""
        notification_tasks = []
        
        for contact in contacts:
            if contact.notify_on_sos:
                notification_tasks.append(
                    self.notification_service.send_emergency_alert(
                        contact, event, event.location
                    )
                )
        
        results = await asyncio.gather(*notification_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if result is True:
                event.contacts_notified.append(contacts[i].id)
    
    async def _safe_callback(
        self,
        callback: Callable,
        *args,
        **kwargs
    ) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Callback error: {e}")
    
    async def trigger_fake_call(
        self,
        delay: int = 3,
        contact_name: Optional[str] = None
    ) -> Dict:
        """Trigger a fake call for user safety"""
        return await self.fake_call_service.trigger_fake_call(delay, contact_name)
    
    async def update_location(
        self,
        emergency_id: str,
        location: LocationData
    ) -> None:
        """Update location for active emergency"""
        if emergency_id in self.active_emergencies:
            event = self.active_emergencies[emergency_id]
            event.location = location
            event.updated_at = time.time()
            
            # Capture location as evidence
            evidence = await self.evidence_service.capture_location_trail(
                emergency_id, [location]
            )
            event.evidence.append(evidence)
    
    async def resolve_emergency(
        self,
        emergency_id: str,
        resolution_note: str = ""
    ) -> Optional[EmergencyEvent]:
        """Resolve an active emergency"""
        if emergency_id not in self.active_emergencies:
            return None
        
        event = self.active_emergencies[emergency_id]
        event.status = EmergencyStatus.RESOLVED
        event.resolved_at = time.time()
        event.updated_at = time.time()
        
        if resolution_note:
            event.notes.append(f"Resolution: {resolution_note}")
        
        # Stop any active captures
        for evidence in event.evidence:
            self.evidence_service.stop_capture(evidence.id)
        
        if self.on_emergency_resolved:
            await self._safe_callback(self.on_emergency_resolved, event)
        
        # Remove from active
        del self.active_emergencies[emergency_id]
        
        logger.info(f"Emergency {emergency_id} resolved")
        return event
    
    async def cancel_emergency(
        self,
        emergency_id: str,
        reason: str = "User cancelled"
    ) -> Optional[EmergencyEvent]:
        """Cancel an emergency (false alarm)"""
        if emergency_id not in self.active_emergencies:
            return None
        
        event = self.active_emergencies[emergency_id]
        event.status = EmergencyStatus.CANCELLED
        event.updated_at = time.time()
        event.notes.append(f"Cancelled: {reason}")
        
        # Notify contacts about cancellation
        # ... notification logic ...
        
        del self.active_emergencies[emergency_id]
        
        logger.info(f"Emergency {emergency_id} cancelled: {reason}")
        return event
    
    def get_active_emergency(self, emergency_id: str) -> Optional[EmergencyEvent]:
        """Get active emergency by ID"""
        return self.active_emergencies.get(emergency_id)
    
    def get_all_active_emergencies(self, user_id: Optional[str] = None) -> List[EmergencyEvent]:
        """Get all active emergencies, optionally filtered by user"""
        events = list(self.active_emergencies.values())
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        return events


def create_emergency_engine(config: Optional[Dict] = None) -> EmergencyResponseEngine:
    """Factory function to create emergency response engine"""
    return EmergencyResponseEngine(
        notification_service=NotificationService(),
        evidence_service=EvidenceCaptureService(),
        fake_call_service=FakeCallService(),
        authority_service=AuthorityContactService(),
        auto_authority_contact=config.get('auto_authority_contact', False) if config else False
    )
