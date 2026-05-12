"""
User Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from ...database import get_db, User, EmergencyContactDB, BehaviorProfile
from ..schemas import (
    UserCreate, UserUpdate, UserResponse,
    EmergencyContactCreate, EmergencyContactUpdate, EmergencyContactResponse,
    APIResponse
)
from ..auth import get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=APIResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone exists
    if db.query(User).filter(User.phone == user_data.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password)
    )
    
    db.add(user)
    
    # Create behavior profile
    profile = BehaviorProfile(
        id=str(uuid.uuid4()),
        user_id=user.id
    )
    db.add(profile)
    
    db.commit()
    db.refresh(user)
    
    return APIResponse(
        success=True,
        message="User registered successfully",
        data=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.delete("/me", response_model=APIResponse)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    db.delete(current_user)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Account deleted successfully"
    )


# Emergency Contacts
@router.get("/contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's emergency contacts"""
    contacts = db.query(EmergencyContactDB).filter(
        EmergencyContactDB.user_id == current_user.id
    ).all()
    return contacts


@router.post("/contacts", response_model=EmergencyContactResponse)
async def add_emergency_contact(
    contact_data: EmergencyContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new emergency contact"""
    # Check limit (max 5)
    contact_count = db.query(EmergencyContactDB).filter(
        EmergencyContactDB.user_id == current_user.id
    ).count()
    
    if contact_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 emergency contacts allowed"
        )
    
    # If primary, unset other primaries
    if contact_data.is_primary:
        db.query(EmergencyContactDB).filter(
            EmergencyContactDB.user_id == current_user.id,
            EmergencyContactDB.is_primary == True
        ).update({"is_primary": False})
    
    contact = EmergencyContactDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **contact_data.model_dump()
    )
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return contact


@router.put("/contacts/{contact_id}", response_model=EmergencyContactResponse)
async def update_emergency_contact(
    contact_id: str,
    contact_data: EmergencyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an emergency contact"""
    contact = db.query(EmergencyContactDB).filter(
        EmergencyContactDB.id == contact_id,
        EmergencyContactDB.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    update_data = contact_data.model_dump(exclude_unset=True)
    
    # Handle primary contact switching
    if update_data.get("is_primary"):
        db.query(EmergencyContactDB).filter(
            EmergencyContactDB.user_id == current_user.id,
            EmergencyContactDB.is_primary == True
        ).update({"is_primary": False})
    
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/contacts/{contact_id}", response_model=APIResponse)
async def delete_emergency_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an emergency contact"""
    contact = db.query(EmergencyContactDB).filter(
        EmergencyContactDB.id == contact_id,
        EmergencyContactDB.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    db.delete(contact)
    db.commit()
    
    return APIResponse(
        success=True,
        message="Contact deleted successfully"
    )


@router.post("/device-token", response_model=APIResponse)
async def update_device_token(
    token: str,
    device_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's device token for push notifications"""
    current_user.device_token = token
    current_user.device_type = device_type
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return APIResponse(
        success=True,
        message="Device token updated"
    )
