"""
Community Safety Network Module
Handles crowdsourced safety ratings, safe zones, volunteer guardians
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class IncidentType(Enum):
    """Types of safety incidents"""
    HARASSMENT = "harassment"
    STALKING = "stalking"
    ASSAULT = "assault"
    ROBBERY = "robbery"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNSAFE_AREA = "unsafe_area"
    POOR_LIGHTING = "poor_lighting"
    OTHER = "other"


class GuardianStatus(Enum):
    """Volunteer guardian status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    RESPONDING = "responding"


@dataclass
class SafetyRating:
    """Safety rating for a location"""
    location_id: str
    latitude: float
    longitude: float
    overall_rating: float  # 1-5 scale
    total_ratings: int
    safety_score: float  # 0-1 normalized
    incident_count: int
    last_updated: datetime
    rating_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class IncidentReport:
    """User-submitted incident report"""
    id: str
    reporter_id: Optional[str]  # None for anonymous
    incident_type: IncidentType
    latitude: float
    longitude: float
    description: Optional[str]
    severity: int  # 1-5
    occurred_at: datetime
    reported_at: datetime
    is_anonymous: bool = True
    is_verified: bool = False
    upvotes: int = 0
    media_urls: List[str] = field(default_factory=list)


@dataclass 
class VolunteerGuardian:
    """Community volunteer guardian"""
    id: str
    user_id: str
    name: str
    phone: str
    status: GuardianStatus
    latitude: float
    longitude: float
    coverage_radius: float  # meters
    is_verified: bool
    rating: float
    response_count: int
    availability_schedule: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)


@dataclass
class SafeZoneInfo:
    """Verified safe zone information"""
    id: str
    name: str
    zone_type: str
    latitude: float
    longitude: float
    address: str
    contact_phone: Optional[str]
    operating_hours: Dict[str, str]
    services: List[str]
    is_24_hours: bool
    rating: float
    verified_by: str
    verified_at: datetime


class CommunityRatingSystem:
    """
    Crowdsourced safety rating system
    Aggregates user ratings and incident reports
    """
    
    def __init__(self, grid_size: float = 0.001):
        """
        Args:
            grid_size: Size of rating grid cells in degrees (~100m)
        """
        self.grid_size = grid_size
        self.ratings: Dict[str, SafetyRating] = {}
        self.incidents: Dict[str, List[IncidentReport]] = {}
    
    def _get_grid_id(self, latitude: float, longitude: float) -> str:
        """Get grid cell ID for coordinates"""
        lat_grid = int(latitude / self.grid_size)
        lon_grid = int(longitude / self.grid_size)
        return f"{lat_grid}:{lon_grid}"
    
    def submit_rating(
        self,
        latitude: float,
        longitude: float,
        rating: float,
        categories: Optional[Dict[str, float]] = None
    ) -> SafetyRating:
        """
        Submit a safety rating for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude  
            rating: Overall rating (1-5)
            categories: Category-specific ratings
            
        Returns:
            Updated SafetyRating for the location
        """
        grid_id = self._get_grid_id(latitude, longitude)
        
        if grid_id not in self.ratings:
            self.ratings[grid_id] = SafetyRating(
                location_id=grid_id,
                latitude=latitude,
                longitude=longitude,
                overall_rating=rating,
                total_ratings=1,
                safety_score=rating / 5.0,
                incident_count=0,
                last_updated=datetime.utcnow()
            )
        else:
            existing = self.ratings[grid_id]
            # Calculate running average
            total = existing.total_ratings
            new_rating = (existing.overall_rating * total + rating) / (total + 1)
            
            existing.overall_rating = new_rating
            existing.total_ratings = total + 1
            existing.safety_score = new_rating / 5.0
            existing.last_updated = datetime.utcnow()
            
            if categories:
                for cat, cat_rating in categories.items():
                    if cat in existing.rating_breakdown:
                        existing.rating_breakdown[cat] = (
                            existing.rating_breakdown[cat] * total + cat_rating
                        ) / (total + 1)
                    else:
                        existing.rating_breakdown[cat] = cat_rating
        
        return self.ratings[grid_id]
    
    def get_rating(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[SafetyRating]:
        """Get safety rating for a location"""
        grid_id = self._get_grid_id(latitude, longitude)
        return self.ratings.get(grid_id)
    
    def get_area_ratings(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float
    ) -> List[SafetyRating]:
        """Get all ratings within radius of center point"""
        # Convert km to degrees (approximate)
        degree_radius = radius_km / 111
        
        results = []
        for rating in self.ratings.values():
            lat_diff = abs(rating.latitude - center_lat)
            lon_diff = abs(rating.longitude - center_lon)
            
            if lat_diff <= degree_radius and lon_diff <= degree_radius:
                results.append(rating)
        
        return results
    
    def report_incident(self, incident: IncidentReport) -> None:
        """Submit an incident report"""
        grid_id = self._get_grid_id(incident.latitude, incident.longitude)
        
        if grid_id not in self.incidents:
            self.incidents[grid_id] = []
        
        self.incidents[grid_id].append(incident)
        
        # Update safety rating based on incident
        if grid_id in self.ratings:
            self.ratings[grid_id].incident_count += 1
            # Reduce safety score based on incident severity
            penalty = incident.severity * 0.02
            self.ratings[grid_id].safety_score = max(
                0,
                self.ratings[grid_id].safety_score - penalty
            )
    
    def get_incidents(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        days: int = 30
    ) -> List[IncidentReport]:
        """Get recent incidents near a location"""
        degree_radius = radius_km / 111
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        results = []
        for grid_id, incidents in self.incidents.items():
            # Check each incident in grid
            for incident in incidents:
                if incident.occurred_at < cutoff:
                    continue
                
                lat_diff = abs(incident.latitude - latitude)
                lon_diff = abs(incident.longitude - longitude)
                
                if lat_diff <= degree_radius and lon_diff <= degree_radius:
                    results.append(incident)
        
        return sorted(results, key=lambda x: x.occurred_at, reverse=True)


class GuardianNetwork:
    """
    Volunteer guardian coordination system
    """
    
    def __init__(self):
        self.guardians: Dict[str, VolunteerGuardian] = {}
        self.active_responses: Dict[str, str] = {}  # emergency_id -> guardian_id
    
    def register_guardian(
        self,
        user_id: str,
        name: str,
        phone: str,
        latitude: float,
        longitude: float,
        coverage_radius: float = 1000
    ) -> VolunteerGuardian:
        """Register a new volunteer guardian"""
        guardian_id = str(uuid.uuid4())
        
        guardian = VolunteerGuardian(
            id=guardian_id,
            user_id=user_id,
            name=name,
            phone=phone,
            status=GuardianStatus.OFFLINE,
            latitude=latitude,
            longitude=longitude,
            coverage_radius=coverage_radius,
            is_verified=False,
            rating=0.0,
            response_count=0
        )
        
        self.guardians[guardian_id] = guardian
        return guardian
    
    def update_guardian_location(
        self,
        guardian_id: str,
        latitude: float,
        longitude: float
    ) -> None:
        """Update guardian's current location"""
        if guardian_id in self.guardians:
            self.guardians[guardian_id].latitude = latitude
            self.guardians[guardian_id].longitude = longitude
    
    def set_guardian_status(
        self,
        guardian_id: str,
        status: GuardianStatus
    ) -> None:
        """Update guardian's availability status"""
        if guardian_id in self.guardians:
            self.guardians[guardian_id].status = status
    
    def find_nearby_guardians(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        available_only: bool = True
    ) -> List[VolunteerGuardian]:
        """Find guardians near a location"""
        results = []
        
        for guardian in self.guardians.values():
            if available_only and guardian.status != GuardianStatus.AVAILABLE:
                continue
            
            # Calculate approximate distance
            lat_diff = abs(guardian.latitude - latitude) * 111  # km per degree
            lon_diff = abs(guardian.longitude - longitude) * 111
            distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
            
            if distance <= radius_km:
                results.append(guardian)
        
        # Sort by distance
        results.sort(key=lambda g: (
            (g.latitude - latitude) ** 2 + (g.longitude - longitude) ** 2
        ))
        
        return results
    
    async def alert_guardians(
        self,
        emergency_id: str,
        latitude: float,
        longitude: float,
        description: str
    ) -> List[str]:
        """
        Alert nearby guardians about an emergency
        
        Returns:
            List of guardian IDs who were alerted
        """
        nearby = self.find_nearby_guardians(latitude, longitude)
        alerted = []
        
        for guardian in nearby[:5]:  # Alert up to 5 nearest guardians
            # In production, this would send push notification
            logger.info(f"Alerting guardian {guardian.id} about emergency {emergency_id}")
            alerted.append(guardian.id)
        
        return alerted
    
    def guardian_respond(
        self,
        guardian_id: str,
        emergency_id: str
    ) -> bool:
        """Record guardian response to emergency"""
        if guardian_id not in self.guardians:
            return False
        
        guardian = self.guardians[guardian_id]
        guardian.status = GuardianStatus.RESPONDING
        guardian.response_count += 1
        
        self.active_responses[emergency_id] = guardian_id
        
        return True
    
    def complete_response(
        self,
        emergency_id: str,
        rating: float
    ) -> None:
        """Complete guardian response and update rating"""
        if emergency_id in self.active_responses:
            guardian_id = self.active_responses[emergency_id]
            if guardian_id in self.guardians:
                guardian = self.guardians[guardian_id]
                
                # Update running average rating
                total = guardian.response_count
                guardian.rating = (
                    guardian.rating * (total - 1) + rating
                ) / total
                
                guardian.status = GuardianStatus.AVAILABLE
            
            del self.active_responses[emergency_id]


class SafeZoneManager:
    """
    Manages verified safe zones and safe places
    """
    
    ZONE_TYPES = [
        "police_station",
        "hospital",
        "fire_station",
        "metro_station",
        "bus_stop",
        "shopping_mall",
        "atm",
        "women_shelter",
        "community_center",
        "pharmacy_24h"
    ]
    
    def __init__(self):
        self.safe_zones: Dict[str, SafeZoneInfo] = {}
    
    def add_safe_zone(
        self,
        name: str,
        zone_type: str,
        latitude: float,
        longitude: float,
        address: str,
        contact_phone: Optional[str] = None,
        operating_hours: Optional[Dict[str, str]] = None,
        services: Optional[List[str]] = None,
        verified_by: str = "system"
    ) -> SafeZoneInfo:
        """Add a new verified safe zone"""
        zone_id = str(uuid.uuid4())
        
        zone = SafeZoneInfo(
            id=zone_id,
            name=name,
            zone_type=zone_type,
            latitude=latitude,
            longitude=longitude,
            address=address,
            contact_phone=contact_phone,
            operating_hours=operating_hours or {},
            services=services or [],
            is_24_hours="24" in (operating_hours or {}).get("all", ""),
            rating=0.0,
            verified_by=verified_by,
            verified_at=datetime.utcnow()
        )
        
        self.safe_zones[zone_id] = zone
        return zone
    
    def find_nearby_zones(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        zone_type: Optional[str] = None
    ) -> List[Tuple[SafeZoneInfo, float]]:
        """
        Find safe zones near a location
        
        Returns:
            List of (SafeZoneInfo, distance_km) tuples sorted by distance
        """
        results = []
        
        for zone in self.safe_zones.values():
            if zone_type and zone.zone_type != zone_type:
                continue
            
            # Calculate distance
            lat_diff = (zone.latitude - latitude) * 111
            lon_diff = (zone.longitude - longitude) * 111
            distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
            
            if distance <= radius_km:
                results.append((zone, distance))
        
        results.sort(key=lambda x: x[1])
        return results
    
    def get_nearest_zone(
        self,
        latitude: float,
        longitude: float,
        zone_type: Optional[str] = None
    ) -> Optional[Tuple[SafeZoneInfo, float]]:
        """Get the nearest safe zone"""
        nearby = self.find_nearby_zones(
            latitude, longitude,
            radius_km=10.0,
            zone_type=zone_type
        )
        return nearby[0] if nearby else None
    
    def rate_zone(self, zone_id: str, rating: float) -> None:
        """Submit a rating for a safe zone"""
        if zone_id in self.safe_zones:
            zone = self.safe_zones[zone_id]
            # Simple running average (would need rating count in real system)
            zone.rating = (zone.rating + rating) / 2


class CommunitySafetyNetwork:
    """
    Main community safety coordination system
    Integrates ratings, incidents, guardians, and safe zones
    """
    
    def __init__(self):
        self.rating_system = CommunityRatingSystem()
        self.guardian_network = GuardianNetwork()
        self.safe_zone_manager = SafeZoneManager()
    
    def get_area_safety_summary(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0
    ) -> Dict:
        """Get comprehensive safety summary for an area"""
        # Get ratings
        ratings = self.rating_system.get_area_ratings(
            latitude, longitude, radius_km
        )
        avg_rating = (
            sum(r.overall_rating for r in ratings) / len(ratings)
            if ratings else 3.0
        )
        
        # Get incidents
        incidents = self.rating_system.get_incidents(
            latitude, longitude, radius_km
        )
        
        # Get safe zones
        safe_zones = self.safe_zone_manager.find_nearby_zones(
            latitude, longitude, radius_km
        )
        
        # Get available guardians
        guardians = self.guardian_network.find_nearby_guardians(
            latitude, longitude, radius_km
        )
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "safety_rating": avg_rating,
            "rating_count": len(ratings),
            "recent_incidents": len(incidents),
            "incident_types": list(set(i.incident_type.value for i in incidents)),
            "safe_zones_nearby": len(safe_zones),
            "nearest_safe_zone": safe_zones[0][0].name if safe_zones else None,
            "guardians_available": len(guardians),
            "overall_safety_score": self._calculate_safety_score(
                avg_rating, len(incidents), len(safe_zones), len(guardians)
            )
        }
    
    def _calculate_safety_score(
        self,
        rating: float,
        incidents: int,
        safe_zones: int,
        guardians: int
    ) -> float:
        """Calculate overall safety score (0-1)"""
        base_score = rating / 5.0
        
        # Penalty for incidents
        incident_penalty = min(0.3, incidents * 0.05)
        
        # Bonus for safe zones and guardians
        safe_zone_bonus = min(0.15, safe_zones * 0.03)
        guardian_bonus = min(0.1, guardians * 0.02)
        
        return max(0, min(1, base_score - incident_penalty + safe_zone_bonus + guardian_bonus))
    
    async def handle_emergency_community_response(
        self,
        emergency_id: str,
        latitude: float,
        longitude: float,
        description: str
    ) -> Dict:
        """
        Coordinate community response to emergency
        
        Returns:
            Response coordination details
        """
        # Alert nearby guardians
        alerted_guardians = await self.guardian_network.alert_guardians(
            emergency_id, latitude, longitude, description
        )
        
        # Find nearest safe zones
        safe_zones = self.safe_zone_manager.find_nearby_zones(
            latitude, longitude, radius_km=2.0
        )
        
        return {
            "emergency_id": emergency_id,
            "guardians_alerted": len(alerted_guardians),
            "guardian_ids": alerted_guardians,
            "nearest_safe_zones": [
                {
                    "name": z[0].name,
                    "type": z[0].zone_type,
                    "distance_km": z[1],
                    "address": z[0].address,
                    "phone": z[0].contact_phone
                }
                for z in safe_zones[:3]
            ]
        }


# Factory function
def create_community_network() -> CommunitySafetyNetwork:
    """Create community safety network instance"""
    return CommunitySafetyNetwork()
