"""
Contextual Risk Assessment Module
Evaluates risk based on location, time, crime statistics, and behavior patterns
Outputs: Dynamic risk level (Low, Medium, High, Critical)
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Location:
    """Geographic location data"""
    latitude: float
    longitude: float
    accuracy: float = 0.0
    altitude: Optional[float] = None
    timestamp: float = 0.0
    address: Optional[str] = None
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location in meters (Haversine formula)"""
        R = 6371000  # Earth's radius in meters
        
        lat1, lat2 = np.radians(self.latitude), np.radians(other.latitude)
        dlat = np.radians(other.latitude - self.latitude)
        dlon = np.radians(other.longitude - self.longitude)
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c


@dataclass
class CrimeStatistics:
    """Crime statistics for an area"""
    area_id: str
    total_incidents: int = 0
    assault_count: int = 0
    harassment_count: int = 0
    robbery_count: int = 0
    stalking_count: int = 0
    last_incident_date: Optional[datetime] = None
    risk_score: float = 0.0  # Normalized 0-1
    
    def calculate_risk_score(self) -> float:
        """Calculate normalized risk score"""
        # Weighted scoring
        weights = {
            'assault': 0.35,
            'harassment': 0.25,
            'robbery': 0.25,
            'stalking': 0.15
        }
        
        total = self.assault_count + self.harassment_count + self.robbery_count + self.stalking_count
        if total == 0:
            return 0.0
        
        weighted_score = (
            weights['assault'] * self.assault_count +
            weights['harassment'] * self.harassment_count +
            weights['robbery'] * self.robbery_count +
            weights['stalking'] * self.stalking_count
        ) / total
        
        # Apply recency factor
        if self.last_incident_date:
            days_since = (datetime.now() - self.last_incident_date).days
            recency_factor = max(0.5, 1.0 - (days_since / 365))
            weighted_score *= recency_factor
        
        self.risk_score = min(1.0, weighted_score)
        return self.risk_score


@dataclass
class UserBehaviorProfile:
    """User behavior and route patterns"""
    user_id: str
    usual_routes: List[List[Location]] = field(default_factory=list)
    frequent_locations: List[Location] = field(default_factory=list)
    typical_times: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)  # day -> [(start_hour, end_hour)]
    movement_speed_avg: float = 1.5  # m/s (walking)
    last_known_location: Optional[Location] = None
    behavior_anomaly_threshold: float = 0.7


@dataclass
class RiskAssessmentResult:
    """Result of contextual risk assessment"""
    risk_level: RiskLevel
    overall_score: float  # 0-1 scale
    location_risk: float
    time_risk: float
    crime_risk: float
    behavior_risk: float
    audio_visual_risk: float
    contributing_factors: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    safe_zones_nearby: List[Dict] = field(default_factory=list)
    timestamp: float = 0.0


class TimeRiskAnalyzer:
    """
    Analyzes risk based on time of day and day of week
    """
    
    def __init__(self):
        # Risk multipliers for different hours (0-23)
        # Higher risk late night/early morning
        self.hourly_risk = {
            0: 0.9, 1: 0.95, 2: 0.95, 3: 0.9, 4: 0.85, 5: 0.7,
            6: 0.4, 7: 0.3, 8: 0.2, 9: 0.2, 10: 0.2, 11: 0.2,
            12: 0.2, 13: 0.2, 14: 0.2, 15: 0.25, 16: 0.3, 17: 0.35,
            18: 0.4, 19: 0.5, 20: 0.6, 21: 0.7, 22: 0.8, 23: 0.85
        }
        
        # Day of week multipliers (0=Monday)
        self.daily_multiplier = {
            0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.1,
            5: 1.2, 6: 1.15
        }
    
    def calculate_risk(self, dt: Optional[datetime] = None) -> Tuple[float, str]:
        """
        Calculate time-based risk score
        
        Returns:
            Tuple of (risk_score, reason)
        """
        if dt is None:
            dt = datetime.now()
        
        hour_risk = self.hourly_risk.get(dt.hour, 0.5)
        day_multiplier = self.daily_multiplier.get(dt.weekday(), 1.0)
        
        risk_score = hour_risk * day_multiplier
        
        # Determine reason
        if dt.hour >= 22 or dt.hour <= 4:
            reason = "late_night_hours"
        elif dt.hour >= 18 and dt.hour < 22:
            reason = "evening_hours"
        else:
            reason = "normal_hours"
        
        return min(1.0, risk_score), reason


class LocationRiskAnalyzer:
    """
    Analyzes risk based on location characteristics
    """
    
    def __init__(self):
        # Safe zone types
        self.safe_zone_types = [
            'police_station', 'hospital', 'fire_station',
            'mall', 'metro_station', 'bus_stop', 'atm'
        ]
        
        # High-risk area types
        self.high_risk_types = [
            'isolated_area', 'construction_site', 'abandoned_building',
            'poorly_lit_area', 'industrial_zone'
        ]
    
    def calculate_risk(
        self,
        location: Location,
        nearby_places: Optional[List[Dict]] = None
    ) -> Tuple[float, List[str]]:
        """
        Calculate location-based risk
        
        Args:
            location: Current location
            nearby_places: List of nearby places with type and distance
            
        Returns:
            Tuple of (risk_score, risk_factors)
        """
        risk_factors = []
        base_risk = 0.5  # Default unknown area risk
        
        if nearby_places:
            # Check for safe zones
            safe_zone_count = sum(
                1 for p in nearby_places
                if p.get('type') in self.safe_zone_types and p.get('distance', float('inf')) < 500
            )
            
            # Check for high-risk areas
            high_risk_count = sum(
                1 for p in nearby_places
                if p.get('type') in self.high_risk_types and p.get('distance', float('inf')) < 300
            )
            
            if safe_zone_count > 0:
                base_risk -= 0.1 * min(safe_zone_count, 3)
            
            if high_risk_count > 0:
                base_risk += 0.15 * min(high_risk_count, 3)
                risk_factors.append(f"near_high_risk_area")
            
            if safe_zone_count == 0:
                risk_factors.append("no_nearby_safe_zones")
        
        return max(0, min(1.0, base_risk)), risk_factors
    
    def find_nearby_safe_zones(
        self,
        location: Location,
        safe_zones: List[Dict],
        max_distance: float = 1000
    ) -> List[Dict]:
        """Find safe zones within specified distance"""
        nearby = []
        for zone in safe_zones:
            zone_loc = Location(
                latitude=zone['latitude'],
                longitude=zone['longitude']
            )
            distance = location.distance_to(zone_loc)
            if distance <= max_distance:
                nearby.append({
                    **zone,
                    'distance': distance
                })
        
        return sorted(nearby, key=lambda x: x['distance'])


class BehaviorAnomalyDetector:
    """
    Detects anomalies in user behavior patterns
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def detect_route_deviation(
        self,
        current_location: Location,
        expected_route: List[Location],
        tolerance: float = 100  # meters
    ) -> Tuple[bool, float]:
        """
        Detect if user has deviated from expected route
        
        Returns:
            Tuple of (is_deviating, deviation_score)
        """
        if not expected_route:
            return False, 0.0
        
        # Find minimum distance to route
        min_distance = float('inf')
        for waypoint in expected_route:
            dist = current_location.distance_to(waypoint)
            min_distance = min(min_distance, dist)
        
        is_deviating = min_distance > tolerance
        deviation_score = min(1.0, min_distance / (tolerance * 3))
        
        return is_deviating, deviation_score
    
    def detect_speed_anomaly(
        self,
        locations: List[Location],
        normal_speed: float = 1.5,  # m/s
        time_window: float = 60  # seconds
    ) -> Tuple[bool, str]:
        """
        Detect unusual movement speed (too fast or stopped)
        
        Returns:
            Tuple of (is_anomaly, anomaly_type)
        """
        if len(locations) < 2:
            return False, ""
        
        # Calculate recent speed
        recent = [l for l in locations if l.timestamp > locations[-1].timestamp - time_window]
        if len(recent) < 2:
            return False, ""
        
        total_distance = sum(
            recent[i].distance_to(recent[i+1])
            for i in range(len(recent) - 1)
        )
        time_elapsed = recent[-1].timestamp - recent[0].timestamp
        
        if time_elapsed <= 0:
            return False, ""
        
        current_speed = total_distance / time_elapsed
        
        # Check for anomalies
        if current_speed > normal_speed * 3:
            return True, "moving_too_fast"
        elif current_speed < normal_speed * 0.1 and time_elapsed > 300:
            return True, "stationary_extended"
        
        return False, ""
    
    def detect_unusual_time(
        self,
        profile: UserBehaviorProfile,
        current_time: datetime
    ) -> Tuple[bool, float]:
        """
        Detect if current activity time is unusual for user
        
        Returns:
            Tuple of (is_unusual, confidence)
        """
        day_name = current_time.strftime('%A').lower()
        typical_times = profile.typical_times.get(day_name, [])
        
        if not typical_times:
            return False, 0.0
        
        current_hour = current_time.hour
        
        for start_hour, end_hour in typical_times:
            if start_hour <= current_hour <= end_hour:
                return False, 0.0
        
        # Outside typical times
        return True, 0.7


class ContextualRiskAssessor:
    """
    Main contextual risk assessment system
    Combines all factors to produce dynamic risk level
    """
    
    def __init__(
        self,
        location_weight: float = 0.25,
        time_weight: float = 0.20,
        crime_weight: float = 0.25,
        behavior_weight: float = 0.15,
        audio_visual_weight: float = 0.15
    ):
        self.weights = {
            'location': location_weight,
            'time': time_weight,
            'crime': crime_weight,
            'behavior': behavior_weight,
            'audio_visual': audio_visual_weight
        }
        
        # Initialize analyzers
        self.time_analyzer = TimeRiskAnalyzer()
        self.location_analyzer = LocationRiskAnalyzer()
        self.behavior_detector = BehaviorAnomalyDetector()
        
        # Risk level thresholds
        self.thresholds = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.50,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 0.90
        }
        
        # Action recommendations
        self.recommendations = {
            RiskLevel.LOW: [
                "Continue with normal awareness",
                "Keep emergency contacts accessible"
            ],
            RiskLevel.MEDIUM: [
                "Stay alert to surroundings",
                "Consider sharing live location",
                "Identify nearest safe zones"
            ],
            RiskLevel.HIGH: [
                "Share live location with trusted contacts",
                "Move toward populated/safe areas",
                "Keep phone ready for emergency",
                "Consider fake call feature"
            ],
            RiskLevel.CRITICAL: [
                "Activate emergency SOS",
                "Move to nearest safe zone immediately",
                "Contact emergency services",
                "Alert trusted contacts"
            ]
        }
    
    def assess_risk(
        self,
        location: Location,
        user_profile: Optional[UserBehaviorProfile] = None,
        crime_stats: Optional[CrimeStatistics] = None,
        nearby_places: Optional[List[Dict]] = None,
        safe_zones: Optional[List[Dict]] = None,
        audio_visual_risk: float = 0.0,
        recent_locations: Optional[List[Location]] = None
    ) -> RiskAssessmentResult:
        """
        Perform comprehensive risk assessment
        
        Args:
            location: Current location
            user_profile: User's behavior profile
            crime_stats: Crime statistics for area
            nearby_places: Nearby places/POIs
            safe_zones: Known safe zones
            audio_visual_risk: Risk from audio/visual detection (0-1)
            recent_locations: Recent location history
            
        Returns:
            RiskAssessmentResult with comprehensive risk analysis
        """
        import time
        
        contributing_factors = []
        
        # Time-based risk
        time_risk, time_reason = self.time_analyzer.calculate_risk()
        if time_risk > 0.5:
            contributing_factors.append(f"time_risk:{time_reason}")
        
        # Location-based risk
        location_risk, location_factors = self.location_analyzer.calculate_risk(
            location, nearby_places
        )
        contributing_factors.extend([f"location:{f}" for f in location_factors])
        
        # Crime statistics risk
        crime_risk = 0.0
        if crime_stats:
            crime_risk = crime_stats.calculate_risk_score()
            if crime_risk > 0.5:
                contributing_factors.append(f"crime_stats_high:{crime_stats.area_id}")
        
        # Behavior anomaly risk
        behavior_risk = 0.0
        if user_profile and recent_locations:
            # Check route deviation
            if user_profile.usual_routes:
                is_deviating, dev_score = self.behavior_detector.detect_route_deviation(
                    location, user_profile.usual_routes[0]
                )
                if is_deviating:
                    behavior_risk = max(behavior_risk, dev_score)
                    contributing_factors.append("route_deviation")
            
            # Check speed anomaly
            is_speed_anomaly, anomaly_type = self.behavior_detector.detect_speed_anomaly(
                recent_locations
            )
            if is_speed_anomaly:
                behavior_risk = max(behavior_risk, 0.7)
                contributing_factors.append(f"speed_anomaly:{anomaly_type}")
            
            # Check unusual time
            is_unusual_time, conf = self.behavior_detector.detect_unusual_time(
                user_profile, datetime.now()
            )
            if is_unusual_time:
                behavior_risk = max(behavior_risk, conf)
                contributing_factors.append("unusual_activity_time")
        
        # Audio-visual risk contribution
        if audio_visual_risk > 0.5:
            contributing_factors.append("audio_visual_threat_detected")
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['location'] * location_risk +
            self.weights['time'] * time_risk +
            self.weights['crime'] * crime_risk +
            self.weights['behavior'] * behavior_risk +
            self.weights['audio_visual'] * audio_visual_risk
        )
        
        # Apply boost for multiple high-risk factors
        high_risk_count = sum(1 for r in [
            location_risk, time_risk, crime_risk, behavior_risk, audio_visual_risk
        ] if r > 0.6)
        
        if high_risk_count >= 3:
            overall_score = min(1.0, overall_score * 1.3)
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        for level, threshold in sorted(self.thresholds.items(), key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                risk_level = level
                break
        
        # Find nearby safe zones
        nearby_safe = []
        if safe_zones:
            nearby_safe = self.location_analyzer.find_nearby_safe_zones(
                location, safe_zones
            )[:5]  # Top 5 closest
        
        return RiskAssessmentResult(
            risk_level=risk_level,
            overall_score=overall_score,
            location_risk=location_risk,
            time_risk=time_risk,
            crime_risk=crime_risk,
            behavior_risk=behavior_risk,
            audio_visual_risk=audio_visual_risk,
            contributing_factors=contributing_factors,
            recommended_actions=self.recommendations.get(risk_level, []),
            safe_zones_nearby=nearby_safe,
            timestamp=time.time()
        )
    
    def get_safe_route(
        self,
        start: Location,
        end: Location,
        crime_data: Dict[str, CrimeStatistics],
        safe_zones: List[Dict]
    ) -> List[Location]:
        """
        Calculate safest route between two points
        Prioritizes routes through safe areas and near safe zones
        """
        # This would integrate with a routing API (Google Maps, etc.)
        # For now, return direct path with waypoints near safe zones
        
        waypoints = [start]
        
        # Find safe zones along the path
        for zone in safe_zones:
            zone_loc = Location(
                latitude=zone['latitude'],
                longitude=zone['longitude']
            )
            # Check if zone is roughly along the path
            d_start = start.distance_to(zone_loc)
            d_end = end.distance_to(zone_loc)
            direct_dist = start.distance_to(end)
            
            if d_start + d_end < direct_dist * 1.5:  # Allow 50% deviation
                waypoints.append(zone_loc)
        
        waypoints.append(end)
        return waypoints


def create_risk_assessor(config: Optional[Dict] = None) -> ContextualRiskAssessor:
    """Factory function to create risk assessor"""
    params = {
        'location_weight': 0.25,
        'time_weight': 0.20,
        'crime_weight': 0.25,
        'behavior_weight': 0.15,
        'audio_visual_weight': 0.15
    }
    if config:
        params.update(config)
    
    return ContextualRiskAssessor(**params)
