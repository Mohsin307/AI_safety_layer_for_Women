"""
Emergency API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio

from ...database import get_db, User, EmergencyDB, EmergencyContactDB, Evidence
from ..schemas import (
    EmergencyTrigger, EmergencyUpdate, EmergencyResolve,
    EmergencyResponse, EvidenceResponse, FakeCallRequest, FakeCallResponse,
    LocationCreate, APIResponse
)
from ..auth import get_current_user
from ai_modules.emergency_response import (
    EmergencyResponseEngine, EmergencyType, EmergencyContact,
    LocationData, create_emergency_engine
)

router = APIRouter(prefix="/emergency", tags=["Emergency"])

# Initialize emergency engine
emergency_engine = create_emergency_engine()


@router.post("/trigger", response_model=EmergencyResponse)
async def trigger_emergency(
    data: EmergencyTrigger,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger an emergency SOS"""
    
    # Get user's emergency contacts
    db_contacts = db.query(EmergencyContactDB).filter(
        EmergencyContactDB.user_id == current_user.id,
        EmergencyContactDB.notify_on_sos == True
    ).all()
    
    contacts = [
        EmergencyContact(
            id=c.id,
            name=c.name,
            phone=c.phone,
            email=c.email,
            relationship=c.relationship or "",
            is_primary=c.is_primary,
            notify_on_sos=c.notify_on_sos,
            share_location=c.share_location
        )
        for c in db_contacts
    ]
    
    # Prepare location data
    location = None
    if data.location:
        location = LocationData(
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            accuracy=data.location.accuracy or 0.0,
            altitude=data.location.altitude,
            speed=data.location.speed,
            heading=data.location.heading,
            address=data.location.address
        )
    
    # Map emergency type
    emergency_type_map = {
        "audio_threat": EmergencyType.AUDIO_THREAT,
        "visual_threat": EmergencyType.VISUAL_THREAT,
        "manual_sos": EmergencyType.MANUAL_SOS,
        "silent_sos": EmergencyType.SILENT_SOS,
        "auto_detected": EmergencyType.AUTO_DETECTED,
        "panic_button": EmergencyType.PANIC_BUTTON
    }
    
    emergency_type = emergency_type_map.get(
        data.emergency_type.value,
        EmergencyType.MANUAL_SOS
    )
    
    # Trigger emergency through engine
    event = await emergency_engine.trigger_emergency(
        user_id=current_user.id,
        emergency_type=emergency_type,
        risk_level=3,  # Default to HIGH
        trigger_reason=data.trigger_reason or emergency_type.value,
        location=location,
        contacts=contacts,
        silent_mode=data.silent_mode
    )
    
    # Save to database
    emergency_db = EmergencyDB(
        id=event.id,
        user_id=current_user.id,
        emergency_type=event.emergency_type.value,
        status=event.status.value,
        risk_level=event.risk_level,
        trigger_reason=event.trigger_reason,
        latitude=location.latitude if location else None,
        longitude=location.longitude if location else None,
        address=location.address if location else None,
        contacts_notified=event.contacts_notified,
        authorities_contacted=event.authorities_contacted,
        created_at=datetime.fromtimestamp(event.created_at),
        updated_at=datetime.fromtimestamp(event.updated_at)
    )
    
    db.add(emergency_db)
    db.commit()
    db.refresh(emergency_db)
    
    return emergency_db


@router.get("/active", response_model=List[EmergencyResponse])
async def get_active_emergencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active emergencies"""
    emergencies = db.query(EmergencyDB).filter(
        EmergencyDB.user_id == current_user.id,
        EmergencyDB.status.in_(["initiated", "alerting_contacts", "capturing_evidence", "active"])
    ).order_by(EmergencyDB.created_at.desc()).all()
    
    return emergencies


@router.get("/history", response_model=List[EmergencyResponse])
async def get_emergency_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's emergency history"""
    emergencies = db.query(EmergencyDB).filter(
        EmergencyDB.user_id == current_user.id
    ).order_by(EmergencyDB.created_at.desc()).offset(offset).limit(limit).all()
    
    return emergencies


@router.get("/{emergency_id}", response_model=EmergencyResponse)
async def get_emergency(
    emergency_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific emergency details"""
    emergency = db.query(EmergencyDB).filter(
        EmergencyDB.id == emergency_id,
        EmergencyDB.user_id == current_user.id
    ).first()
    
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found"
        )
    
    return emergency


@router.put("/{emergency_id}/location", response_model=APIResponse)
async def update_emergency_location(
    emergency_id: str,
    location: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update location for active emergency"""
    emergency = db.query(EmergencyDB).filter(
        EmergencyDB.id == emergency_id,
        EmergencyDB.user_id == current_user.id,
        EmergencyDB.status.in_(["initiated", "active"])
    ).first()
    
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active emergency not found"
        )
    
    # Update database
    emergency.latitude = location.latitude
    emergency.longitude = location.longitude
    emergency.address = location.address
    emergency.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Update engine
    await emergency_engine.update_location(
        emergency_id,
        LocationData(
            latitude=location.latitude,
            longitude=location.longitude,
            accuracy=location.accuracy or 0.0,
            address=location.address
        )
    )
    
    return APIResponse(
        success=True,
        message="Location updated"
    )


@router.post("/{emergency_id}/resolve", response_model=EmergencyResponse)
async def resolve_emergency(
    emergency_id: str,
    data: EmergencyResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve an active emergency"""
    emergency = db.query(EmergencyDB).filter(
        EmergencyDB.id == emergency_id,
        EmergencyDB.user_id == current_user.id
    ).first()
    
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found"
        )
    
    if emergency.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency already resolved/cancelled"
        )
    
    # Resolve in engine
    await emergency_engine.resolve_emergency(
        emergency_id,
        data.resolution_note or ""
    )
    
    # Update database
    emergency.status = "resolved"
    emergency.resolved_at = datetime.utcnow()
    emergency.updated_at = datetime.utcnow()
    
    if data.resolution_note:
        notes = emergency.notes or []
        notes.append(f"Resolution: {data.resolution_note}")
        emergency.notes = notes
    
    db.commit()
    db.refresh(emergency)
    
    return emergency


@router.post("/{emergency_id}/cancel", response_model=EmergencyResponse)
async def cancel_emergency(
    emergency_id: str,
    reason: str = "User cancelled",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an emergency (false alarm)"""
    emergency = db.query(EmergencyDB).filter(
        EmergencyDB.id == emergency_id,
        EmergencyDB.user_id == current_user.id
    ).first()
    
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found"
        )
    
    if emergency.status in ["resolved", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency already resolved/cancelled"
        )
    
    # Cancel in engine
    await emergency_engine.cancel_emergency(emergency_id, reason)
    
    # Update database
    emergency.status = "cancelled"
    emergency.updated_at = datetime.utcnow()
    notes = emergency.notes or []
    notes.append(f"Cancelled: {reason}")
    emergency.notes = notes
    
    db.commit()
    db.refresh(emergency)
    
    return emergency


@router.get("/{emergency_id}/evidence", response_model=List[EvidenceResponse])
async def get_emergency_evidence(
    emergency_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evidence for an emergency"""
    emergency = db.query(EmergencyDB).filter(
        EmergencyDB.id == emergency_id,
        EmergencyDB.user_id == current_user.id
    ).first()
    
    if not emergency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency not found"
        )
    
    evidence = db.query(Evidence).filter(
        Evidence.emergency_id == emergency_id
    ).all()
    
    return evidence


@router.post("/fake-call", response_model=FakeCallResponse)
async def trigger_fake_call(
    data: FakeCallRequest,
    current_user: User = Depends(get_current_user)
):
    """Trigger a fake incoming call"""
    result = await emergency_engine.trigger_fake_call(
        delay=data.delay_seconds,
        contact_name=data.contact_name
    )
    
    return FakeCallResponse(
        type=result["type"],
        caller_name=result["caller_name"],
        caller_number=result["caller_number"],
        timestamp=datetime.fromtimestamp(result["timestamp"])
    )
