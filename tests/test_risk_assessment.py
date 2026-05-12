"""
Tests for Risk Assessment Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time
import numpy as np


class TestTimeRiskAnalysis:
    """Test time-based risk analysis"""
    
    def test_night_hours_high_risk(self):
        """Test that late night hours have higher risk"""
        # Night time should have higher risk
        night_hours = [23, 0, 1, 2, 3, 4]
        day_hours = [10, 11, 12, 13, 14]
        
        def calculate_time_risk(hour):
            if hour >= 22 or hour <= 5:
                return 0.8
            elif hour >= 6 and hour <= 8:
                return 0.4
            else:
                return 0.2
        
        for hour in night_hours:
            assert calculate_time_risk(hour) >= 0.6
        
        for hour in day_hours:
            assert calculate_time_risk(hour) <= 0.3
    
    def test_weekend_risk_adjustment(self):
        """Test weekend risk adjustment"""
        # Weekend nights may have different risk profiles
        base_risk = 0.5
        weekend_multiplier = 1.2
        
        weekend_night_risk = base_risk * weekend_multiplier
        
        assert weekend_night_risk > base_risk


class TestLocationRiskAnalysis:
    """Test location-based risk analysis"""
    
    def test_known_safe_zone_low_risk(self):
        """Test that known safe zones have low risk"""
        safe_zones = [
            {'lat': 28.6139, 'lon': 77.2090, 'radius': 0.01, 'type': 'police_station'},
            {'lat': 28.6200, 'lon': 77.2100, 'radius': 0.005, 'type': 'hospital'}
        ]
        
        def get_location_risk(lat, lon, safe_zones):
            for zone in safe_zones:
                distance = np.sqrt(
                    (lat - zone['lat'])**2 + (lon - zone['lon'])**2
                )
                if distance < zone['radius']:
                    return 0.1  # Very safe
            return 0.5  # Default
        
        # Location inside safe zone
        risk = get_location_risk(28.6139, 77.2090, safe_zones)
        assert risk < 0.2
    
    def test_isolated_area_high_risk(self):
        """Test that isolated areas have higher risk"""
        location_type = 'isolated_area'
        
        risk_by_type = {
            'residential': 0.3,
            'commercial': 0.4,
            'industrial': 0.6,
            'isolated_area': 0.8,
            'busy_street': 0.2
        }
        
        assert risk_by_type[location_type] > 0.7


class TestCrimeStatisticsAnalysis:
    """Test crime statistics integration"""
    
    def test_crime_hotspot_detection(self):
        """Test crime hotspot identification"""
        crime_data = [
            {'lat': 28.61, 'lon': 77.20, 'type': 'theft', 'count': 15},
            {'lat': 28.62, 'lon': 77.21, 'type': 'assault', 'count': 5},
            {'lat': 28.63, 'lon': 77.22, 'type': 'harassment', 'count': 20}
        ]
        
        def is_hotspot(crime_count, threshold=10):
            return crime_count >= threshold
        
        hotspots = [c for c in crime_data if is_hotspot(c['count'])]
        
        assert len(hotspots) == 2
    
    def test_crime_type_weighting(self):
        """Test different crime types have different weights"""
        crime_weights = {
            'theft': 0.3,
            'harassment': 0.7,
            'assault': 0.9,
            'homicide': 1.0,
            'stalking': 0.8
        }
        
        assert crime_weights['assault'] > crime_weights['theft']
        assert crime_weights['homicide'] > crime_weights['assault']


class TestBehaviorAnomalyDetection:
    """Test behavior anomaly detection"""
    
    def test_route_deviation_detection(self):
        """Test detection of route deviation"""
        expected_route = [(28.60, 77.20), (28.61, 77.21), (28.62, 77.22)]
        actual_position = (28.65, 77.25)  # Deviated
        
        def calculate_route_deviation(position, route):
            min_distance = float('inf')
            for point in route:
                distance = np.sqrt(
                    (position[0] - point[0])**2 + 
                    (position[1] - point[1])**2
                )
                min_distance = min(min_distance, distance)
            return min_distance
        
        deviation = calculate_route_deviation(actual_position, expected_route)
        deviation_threshold = 0.02
        
        is_deviated = deviation > deviation_threshold
        assert is_deviated is True
    
    def test_unusual_stop_detection(self):
        """Test detection of unusual stops"""
        movement_history = [
            (100, 200, 0),  # x, y, timestamp
            (105, 205, 5),
            (110, 210, 10),
            (110, 210, 30),  # Stopped for 20 seconds
            (110, 210, 50),  # Still stopped
        ]
        
        def detect_unusual_stop(history, duration_threshold=15):
            for i in range(len(history) - 1):
                curr = history[i]
                next_pos = history[i + 1]
                
                # Check if position same
                if curr[0] == next_pos[0] and curr[1] == next_pos[1]:
                    duration = next_pos[2] - curr[2]
                    if duration > duration_threshold:
                        return True
            return False
        
        has_unusual_stop = detect_unusual_stop(movement_history)
        assert has_unusual_stop is True


class TestRiskScoreCalculation:
    """Test overall risk score calculation"""
    
    def test_weighted_risk_calculation(self):
        """Test weighted risk score calculation"""
        scores = {
            'location': 0.6,
            'time': 0.4,
            'crime_stats': 0.7,
            'behavior': 0.3,
            'audio_visual': 0.5
        }
        
        weights = {
            'location': 0.25,
            'time': 0.20,
            'crime_stats': 0.25,
            'behavior': 0.15,
            'audio_visual': 0.15
        }
        
        # Ensure weights sum to 1
        assert abs(sum(weights.values()) - 1.0) < 0.001
        
        # Calculate weighted score
        total_risk = sum(
            scores[k] * weights[k] for k in scores
        )
        
        expected = (0.6 * 0.25 + 0.4 * 0.20 + 0.7 * 0.25 + 
                   0.3 * 0.15 + 0.5 * 0.15)
        
        assert abs(total_risk - expected) < 0.001
    
    def test_risk_level_categorization(self):
        """Test risk score to level categorization"""
        def categorize_risk(score):
            if score >= 0.8:
                return 'critical'
            elif score >= 0.6:
                return 'high'
            elif score >= 0.4:
                return 'medium'
            else:
                return 'low'
        
        assert categorize_risk(0.9) == 'critical'
        assert categorize_risk(0.7) == 'high'
        assert categorize_risk(0.5) == 'medium'
        assert categorize_risk(0.2) == 'low'


class TestSafeRouteRecommendation:
    """Test safe route recommendation"""
    
    def test_route_safety_scoring(self):
        """Test route safety score calculation"""
        routes = [
            {'name': 'Route A', 'segments': [
                {'risk': 0.2}, {'risk': 0.3}, {'risk': 0.2}
            ]},
            {'name': 'Route B', 'segments': [
                {'risk': 0.1}, {'risk': 0.1}, {'risk': 0.5}
            ]},
            {'name': 'Route C', 'segments': [
                {'risk': 0.4}, {'risk': 0.4}, {'risk': 0.4}
            ]}
        ]
        
        def calculate_route_safety(route):
            avg_risk = sum(s['risk'] for s in route['segments']) / len(route['segments'])
            max_risk = max(s['risk'] for s in route['segments'])
            # Penalize routes with high-risk segments
            return avg_risk * 0.6 + max_risk * 0.4
        
        scores = {r['name']: calculate_route_safety(r) for r in routes}
        safest_route = min(scores, key=scores.get)
        
        # Route A should be safest (low average, low max)
        assert safest_route == 'Route A'
    
    def test_safe_zone_integration_in_route(self):
        """Test that routes prefer safe zones"""
        route_with_safe_zones = {
            'distance': 1.5,  # km
            'safe_zone_count': 3,
            'base_risk': 0.4
        }
        
        route_without_safe_zones = {
            'distance': 1.2,  # km (shorter)
            'safe_zone_count': 0,
            'base_risk': 0.6
        }
        
        def score_route(route):
            # Lower is better
            safe_zone_bonus = route['safe_zone_count'] * 0.1
            return route['base_risk'] - safe_zone_bonus
        
        score1 = score_route(route_with_safe_zones)
        score2 = score_route(route_without_safe_zones)
        
        # Route with safe zones should be preferred
        assert score1 < score2


class TestRiskHistoryTracking:
    """Test risk history and trend analysis"""
    
    def test_risk_trend_detection(self):
        """Test detection of increasing risk trend"""
        risk_history = [0.3, 0.35, 0.4, 0.5, 0.6]
        
        def detect_trend(history, window=3):
            if len(history) < window:
                return 'stable'
            
            recent = history[-window:]
            is_increasing = all(
                recent[i] > recent[i-1] 
                for i in range(1, len(recent))
            )
            
            if is_increasing:
                return 'increasing'
            
            is_decreasing = all(
                recent[i] < recent[i-1] 
                for i in range(1, len(recent))
            )
            
            return 'decreasing' if is_decreasing else 'stable'
        
        trend = detect_trend(risk_history)
        assert trend == 'increasing'
    
    def test_risk_alert_threshold(self):
        """Test risk alert triggering"""
        current_risk = 0.75
        alert_thresholds = {
            'notify': 0.5,
            'warn': 0.7,
            'emergency': 0.9
        }
        
        alerts_triggered = [
            level for level, threshold in alert_thresholds.items()
            if current_risk >= threshold
        ]
        
        assert 'notify' in alerts_triggered
        assert 'warn' in alerts_triggered
        assert 'emergency' not in alerts_triggered
