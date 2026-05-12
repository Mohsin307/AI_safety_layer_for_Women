"""
Risk Assessment and Safety API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import time

from ...database import get_db, User, SafeZone, CrimeReport, LocationHistory
from ..schemas import (
    RiskAssessmentRequest, RiskAssessmentResponse, RiskLevelEnum,
    SafeZoneCreate, SafeZoneUpdate, SafeZoneResponse,
    CrimeReportCreate, CrimeReportResponse,
    LocationCreate, LocationResponse,
    APIResponse
)
from ..auth import get_current_user
from ai_modules.risk_assessment import (
    ContextualRiskAssessor, Location, CrimeStatistics,
    UserBehaviorProfile, RiskLevel, create_risk_assessor
)

router = APIRouter(prefix="/safety", tags=["Safety"])

# Initialize risk assessor
risk_assessor = create_risk_assessor()


def map_risk_level(level: RiskLevel) -> RiskLevelEnum:
    """Map internal risk level to API enum"""
    mapping = {
        RiskLevel.LOW: RiskLevelEnum.LOW,
        RiskLevel.MEDIUM: RiskLevelEnum.MEDIUM,
        RiskLevel.HIGH: RiskLevelEnum.HIGH,
        RiskLevel.CRITICAL: RiskLevelEnum.CRITICAL
    }
    return mapping.get(level, RiskLevelEnum.LOW)


@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_risk(
    data: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess current risk level based on location and context"""
    
    # Build location object
    location = Location(
        latitude=data.location.latitude,
        longitude=data.location.longitude,
        accuracy=data.location.accuracy or 0.0,
        timestamp=time.time()
    )
    
    # Get nearby safe zones
    safe_zones = []
    if data.include_safe_zones:
        # Find safe zones within 2km
        db_zones = db.query(SafeZone).filter(
            SafeZone.latitude.between(location.latitude - 0.02, location.latitude + 0.02),
            SafeZone.longitude.between(location.longitude - 0.02, location.longitude + 0.02)
        ).all()
        
        safe_zones = [
            {
                'id': z.id,
                'name': z.name,
                'type': z.zone_type,
                'latitude': z.latitude,
                'longitude': z.longitude,
                'address': z.address,
                'contact_phone': z.contact_phone
            }
            for z in db_zones
        ]
    
    # Get crime statistics for area
    # Simplified: count recent incidents in area
    incident_count = db.query(CrimeReport).filter(
        CrimeReport.latitude.between(location.latitude - 0.01, location.latitude + 0.01),
        CrimeReport.longitude.between(location.longitude - 0.01, location.longitude + 0.01)
    ).count()
    
    crime_stats = CrimeStatistics(
        area_id=f"{location.latitude:.2f},{location.longitude:.2f}",
        total_incidents=incident_count
    ) if incident_count > 0 else None
    
    # Get user's recent locations for behavior analysis
    recent_locations = db.query(LocationHistory).filter(
        LocationHistory.user_id == current_user.id
    ).order_by(LocationHistory.recorded_at.desc()).limit(20).all()
    
    recent_locs = [
        Location(
            latitude=l.latitude,
            longitude=l.longitude,
            accuracy=l.accuracy or 0.0,
            timestamp=l.recorded_at.timestamp()
        )
        for l in recent_locations
    ]
    
    # Perform risk assessment
    result = risk_assessor.assess_risk(
        location=location,
        crime_stats=crime_stats,
        safe_zones=safe_zones,
        recent_locations=recent_locs
    )
    
    # Build safe zones response with distance
    safe_zones_response = []
    for zone_data in result.safe_zones_nearby[:5]:
        safe_zones_response.append(SafeZoneResponse(
            id=zone_data.get('id', ''),
            name=zone_data.get('name', ''),
            zone_type=zone_data.get('type', ''),
            latitude=zone_data.get('latitude', 0),
            longitude=zone_data.get('longitude', 0),
            address=zone_data.get('address'),
            contact_phone=zone_data.get('contact_phone'),
            distance=zone_data.get('distance', 0),
            rating=zone_data.get('rating', 0.0)
        ))
    
    return RiskAssessmentResponse(
        risk_level=map_risk_level(result.risk_level),
        overall_score=result.overall_score,
        location_risk=result.location_risk,
        time_risk=result.time_risk,
        crime_risk=result.crime_risk,
        behavior_risk=result.behavior_risk,
        audio_visual_risk=result.audio_visual_risk,
        contributing_factors=result.contributing_factors,
        recommended_actions=result.recommended_actions,
        safe_zones_nearby=safe_zones_response,
        timestamp=datetime.fromtimestamp(result.timestamp)
    )


# Safe Zones
@router.get("/safe-zones", response_model=List[SafeZoneResponse])
async def get_safe_zones(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(2.0, description="Radius in km"),
    zone_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get safe zones near a location"""
    # Convert radius to approximate degrees (1 degree ≈ 111km)
    degree_radius = radius / 111
    
    query = db.query(SafeZone).filter(
        SafeZone.latitude.between(latitude - degree_radius, latitude + degree_radius),
        SafeZone.longitude.between(longitude - degree_radius, longitude + degree_radius)
    )
    
    if zone_type:
        query = query.filter(SafeZone.zone_type == zone_type)
    
    zones = query.all()
    
    # Calculate distances and add to response
    user_loc = Location(latitude=latitude, longitude=longitude)
    result = []
    for zone in zones:
        zone_loc = Location(latitude=zone.latitude, longitude=zone.longitude)
        distance = user_loc.distance_to(zone_loc)
        
        result.append(SafeZoneResponse(
            id=zone.id,
            name=zone.name,
            zone_type=zone.zone_type,
            latitude=zone.latitude,
            longitude=zone.longitude,
            address=zone.address,
            contact_phone=zone.contact_phone,
            distance=distance,
            rating=zone.rating
        ))
    
    # Sort by distance
    result.sort(key=lambda x: x.distance or 0)
    return result


@router.post("/safe-zones", response_model=SafeZoneResponse)
async def create_safe_zone(
    data: SafeZoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new safe zone (admin/verified users)"""
    zone = SafeZone(
        id=str(uuid.uuid4()),
        name=data.name,
        zone_type=data.zone_type,
        latitude=data.latitude,
        longitude=data.longitude,
        address=data.address,
        contact_phone=data.contact_phone,
        operating_hours=data.operating_hours or {}
    )
    
    db.add(zone)
    db.commit()
    db.refresh(zone)
    
    return SafeZoneResponse(
        id=zone.id,
        name=zone.name,
        zone_type=zone.zone_type,
        latitude=zone.latitude,
        longitude=zone.longitude,
        address=zone.address,
        contact_phone=zone.contact_phone,
        rating=zone.rating
    )


# Crime Reports
@router.get("/crime-reports", response_model=List[CrimeReportResponse])
async def get_crime_reports(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(2.0, description="Radius in km"),
    incident_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get crime reports near a location"""
    degree_radius = radius / 111
    
    query = db.query(CrimeReport).filter(
        CrimeReport.latitude.between(latitude - degree_radius, latitude + degree_radius),
        CrimeReport.longitude.between(longitude - degree_radius, longitude + degree_radius)
    )
    
    if incident_type:
        query = query.filter(CrimeReport.incident_type == incident_type)
    
    reports = query.order_by(CrimeReport.reported_at.desc()).limit(50).all()
    return reports


@router.post("/crime-reports", response_model=CrimeReportResponse)
async def create_crime_report(
    data: CrimeReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report a crime/incident"""
    report = CrimeReport(
        id=str(uuid.uuid4()),
        incident_type=data.incident_type,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        severity=data.severity,
        incident_date=data.incident_date,
        reported_by=None if data.is_anonymous else current_user.id,
        is_anonymous=data.is_anonymous
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report


# Location Tracking
@router.post("/location", response_model=LocationResponse)
async def update_location(
    data: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's current location"""
    location = LocationHistory(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
        altitude=data.altitude,
        speed=data.speed,
        heading=data.heading,
        address=data.address
    )
    
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return location


@router.get("/location/history", response_model=List[LocationResponse])
async def get_location_history(
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's location history"""
    locations = db.query(LocationHistory).filter(
        LocationHistory.user_id == current_user.id
    ).order_by(LocationHistory.recorded_at.desc()).limit(limit).all()
    
    return locations


@router.get("/safe-route")
async def get_safe_route(
    start_lat: float = Query(..., ge=-90, le=90),
    start_lng: float = Query(..., ge=-180, le=180),
    end_lat: float = Query(..., ge=-90, le=90),
    end_lng: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db)
):
    """Get safest route between two points"""
    # Get safe zones along potential route
    min_lat = min(start_lat, end_lat) - 0.02
    max_lat = max(start_lat, end_lat) + 0.02
    min_lng = min(start_lng, end_lng) - 0.02
    max_lng = max(start_lng, end_lng) + 0.02
    
    safe_zones = db.query(SafeZone).filter(
        SafeZone.latitude.between(min_lat, max_lat),
        SafeZone.longitude.between(min_lng, max_lng)
    ).all()
    
    # Build safe zones list for route calculation
    zones_data = [
        {
            'latitude': z.latitude,
            'longitude': z.longitude,
            'type': z.zone_type,
            'name': z.name
        }
        for z in safe_zones
    ]
    
    start = Location(latitude=start_lat, longitude=start_lng)
    end = Location(latitude=end_lat, longitude=end_lng)
    
    # Get recommended waypoints through safe areas
    waypoints = risk_assessor.get_safe_route(start, end, {}, zones_data)
    
    return {
        "start": {"latitude": start_lat, "longitude": start_lng},
        "end": {"latitude": end_lat, "longitude": end_lng},
        "waypoints": [
            {"latitude": w.latitude, "longitude": w.longitude}
            for w in waypoints
        ],
        "safe_zones_on_route": zones_data
    }
