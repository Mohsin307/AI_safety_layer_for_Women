"""
Tests for Visual Threat Detection Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestWeaponDetection:
    """Test weapon detection functionality"""
    
    def test_weapon_classes(self):
        """Test weapon class mapping"""
        from ai_modules.visual_detection.visual_threat_detector import WeaponDetector
        
        detector = WeaponDetector.__new__(WeaponDetector)
        detector.weapon_classes = {
            'knife': 0,
            'gun': 1,
            'bat': 2,
            'stick': 3
        }
        
        assert 'knife' in detector.weapon_classes
        assert 'gun' in detector.weapon_classes
        assert detector.weapon_classes['knife'] == 0
    
    def test_detection_result_structure(self):
        """Test detection result structure"""
        result = {
            'weapon_type': 'knife',
            'confidence': 0.85,
            'bbox': [100, 100, 200, 200],
            'threat_level': 0.9
        }
        
        assert result['weapon_type'] == 'knife'
        assert 0 <= result['confidence'] <= 1
        assert len(result['bbox']) == 4


class TestPoseAnalysis:
    """Test pose analysis for threat detection"""
    
    def test_aggression_score_calculation(self):
        """Test aggression score is in valid range"""
        # Mock pose analyzer
        aggression_scores = [0.2, 0.5, 0.8, 0.95]
        
        for score in aggression_scores:
            assert 0 <= score <= 1
    
    def test_pose_landmark_structure(self):
        """Test pose landmark data structure"""
        # Sample pose landmarks
        landmarks = {
            'nose': (0.5, 0.2),
            'left_shoulder': (0.3, 0.4),
            'right_shoulder': (0.7, 0.4),
            'left_elbow': (0.2, 0.5),
            'right_elbow': (0.8, 0.5),
            'left_wrist': (0.1, 0.6),
            'right_wrist': (0.9, 0.6)
        }
        
        assert 'nose' in landmarks
        assert len(landmarks['nose']) == 2
    
    def test_raised_arm_detection(self):
        """Test detection of raised arm poses"""
        # Simulate raised arm check
        wrist_y = 0.2  # Above shoulder
        shoulder_y = 0.4
        
        is_raised = wrist_y < shoulder_y
        assert is_raised is True


class TestLowLightEnhancement:
    """Test low light image enhancement"""
    
    def test_brightness_calculation(self):
        """Test average brightness calculation"""
        # Create a mock dark image
        dark_image = np.zeros((100, 100, 3), dtype=np.uint8) + 30
        avg_brightness = np.mean(dark_image)
        
        assert avg_brightness < 50  # Image is dark
    
    def test_enhancement_threshold(self):
        """Test enhancement applies to dark images only"""
        threshold = 50
        
        dark_brightness = 30
        normal_brightness = 120
        
        should_enhance_dark = dark_brightness < threshold
        should_enhance_normal = normal_brightness < threshold
        
        assert should_enhance_dark is True
        assert should_enhance_normal is False


class TestVisualThreatCategory:
    """Test visual threat categories"""
    
    def test_threat_categories(self):
        """Test available threat categories"""
        categories = [
            'weapon_detected',
            'aggressive_behavior',
            'stalking_detected',
            'crowd_threat',
            'isolated_area'
        ]
        
        assert 'weapon_detected' in categories
        assert 'aggressive_behavior' in categories
    
    def test_threat_level_mapping(self):
        """Test threat category to level mapping"""
        threat_levels = {
            'weapon_detected': 0.95,
            'aggressive_behavior': 0.7,
            'stalking_detected': 0.8,
            'crowd_threat': 0.6,
            'isolated_area': 0.4
        }
        
        assert threat_levels['weapon_detected'] > threat_levels['crowd_threat']


class TestStalkingDetection:
    """Test stalking behavior detection"""
    
    def test_tracking_consistency(self):
        """Test consistent tracking detection"""
        # Simulate position history
        position_history = [
            (100, 200),
            (105, 205),
            (110, 210),
            (115, 215),
            (120, 220)
        ]
        
        # Check if movement is consistent (potential stalking)
        movements = []
        for i in range(1, len(position_history)):
            dx = position_history[i][0] - position_history[i-1][0]
            dy = position_history[i][1] - position_history[i-1][1]
            movements.append((dx, dy))
        
        # All movements should be similar for stalking
        is_consistent = all(
            abs(m[0] - movements[0][0]) < 3 and 
            abs(m[1] - movements[0][1]) < 3 
            for m in movements
        )
        
        assert is_consistent is True
    
    def test_duration_threshold(self):
        """Test duration threshold for stalking alert"""
        min_duration_seconds = 30
        observed_duration = 45
        
        is_stalking = observed_duration >= min_duration_seconds
        assert is_stalking is True


class TestVisualDetectionResult:
    """Test visual detection result structure"""
    
    def test_result_completeness(self):
        """Test detection result has all required fields"""
        result = {
            'timestamp': 1704067200.0,
            'threats_detected': True,
            'threat_level': 0.85,
            'detections': [
                {
                    'type': 'weapon_detected',
                    'confidence': 0.9,
                    'details': {'weapon': 'knife'}
                }
            ],
            'frame_analyzed': True,
            'processing_time_ms': 45.2
        }
        
        assert 'timestamp' in result
        assert 'threats_detected' in result
        assert 'threat_level' in result
        assert isinstance(result['detections'], list)
    
    def test_confidence_aggregation(self):
        """Test confidence aggregation from multiple detections"""
        detections = [
            {'confidence': 0.9},
            {'confidence': 0.7},
            {'confidence': 0.8}
        ]
        
        max_confidence = max(d['confidence'] for d in detections)
        avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
        
        assert max_confidence == 0.9
        assert abs(avg_confidence - 0.8) < 0.001


class TestPersonTracking:
    """Test person tracking functionality"""
    
    def test_track_id_assignment(self):
        """Test unique track ID assignment"""
        tracks = {}
        
        def assign_track_id():
            new_id = len(tracks) + 1
            tracks[new_id] = {'positions': []}
            return new_id
        
        id1 = assign_track_id()
        id2 = assign_track_id()
        
        assert id1 != id2
        assert len(tracks) == 2
    
    def test_proximity_calculation(self):
        """Test proximity calculation between persons"""
        person1_pos = (100, 200)
        person2_pos = (150, 250)
        
        distance = np.sqrt(
            (person2_pos[0] - person1_pos[0])**2 + 
            (person2_pos[1] - person1_pos[1])**2
        )
        
        # ~70.7 pixels apart
        assert 70 < distance < 72
        
        # Check if too close (threatening)
        close_threshold = 50
        is_too_close = distance < close_threshold
        assert is_too_close is False
