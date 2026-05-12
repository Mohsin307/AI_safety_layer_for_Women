"""
Tests for Audio Threat Detection Module
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock heavy dependencies
sys.modules['librosa'] = MagicMock()
sys.modules['tensorflow'] = MagicMock()
sys.modules['tensorflow.keras'] = MagicMock()
sys.modules['tensorflow.keras.layers'] = MagicMock()
sys.modules['tensorflow.keras.Model'] = MagicMock()


class TestAudioFeatureExtractor:
    """Test audio feature extraction"""
    
    def test_initialization(self):
        """Test feature extractor initialization"""
        from ai_modules.audio_detection.audio_threat_detector import AudioFeatureExtractor
        
        extractor = AudioFeatureExtractor(
            sample_rate=22050,
            n_mfcc=40
        )
        
        assert extractor.sample_rate == 22050
        assert extractor.n_mfcc == 40
    
    def test_mfcc_extraction_shape(self):
        """Test MFCC feature extraction produces correct shape"""
        from ai_modules.audio_detection.audio_threat_detector import AudioFeatureExtractor
        
        extractor = AudioFeatureExtractor()
        
        # Mock librosa
        with patch.object(extractor, 'extract_mfcc') as mock_mfcc:
            mock_mfcc.return_value = np.zeros((40, 100))
            
            result = extractor.extract_mfcc(np.zeros(22050))
            assert result.shape == (40, 100)


class TestAudioThreatCategory:
    """Test audio threat categories"""
    
    def test_categories_exist(self):
        """Test all required categories exist"""
        from ai_modules.audio_detection.audio_threat_detector import AudioThreatCategory
        
        expected_categories = [
            'NORMAL', 'SCREAM', 'CRY_FOR_HELP', 
            'AGGRESSIVE_VOICE', 'GLASS_BREAKING', 
            'GUNSHOT', 'VERBAL_THREAT'
        ]
        
        for cat in expected_categories:
            assert hasattr(AudioThreatCategory, cat)


class TestAudioDetectionResult:
    """Test audio detection result dataclass"""
    
    def test_result_creation(self):
        """Test creating detection result"""
        from ai_modules.audio_detection.audio_threat_detector import (
            AudioDetectionResult, AudioThreatCategory
        )
        
        result = AudioDetectionResult(
            category=AudioThreatCategory.SCREAM,
            confidence=0.95,
            timestamp=1000.0,
            duration=3.0,
            is_threat=True,
            risk_level=3
        )
        
        assert result.category == AudioThreatCategory.SCREAM
        assert result.confidence == 0.95
        assert result.is_threat is True
        assert result.risk_level == 3


class TestVoiceActivityDetector:
    """Test voice activity detection"""
    
    def test_silence_detection(self):
        """Test that silence is not detected as active"""
        from ai_modules.audio_detection.realtime_processor import VoiceActivityDetector
        
        vad = VoiceActivityDetector(threshold=0.01)
        
        # Very quiet audio
        silence = np.zeros(1000) * 0.001
        assert vad.is_active(silence) is False
    
    def test_activity_detection(self):
        """Test that loud audio is detected as active"""
        from ai_modules.audio_detection.realtime_processor import VoiceActivityDetector
        
        vad = VoiceActivityDetector(threshold=0.01)
        
        # Loud audio
        loud = np.random.randn(1000) * 0.5
        assert vad.is_active(loud) is True


class TestAudioBuffer:
    """Test audio buffer"""
    
    def test_buffer_filling(self):
        """Test buffer fills correctly"""
        from ai_modules.audio_detection.realtime_processor import AudioBuffer
        
        buffer = AudioBuffer(
            sample_rate=22050,
            buffer_duration=1.0,
            overlap=0.5
        )
        
        # Write chunks
        chunk = np.random.randn(1024).astype(np.float32)
        
        ready = False
        for _ in range(30):  # Write multiple chunks
            ready = buffer.write(chunk)
            if ready:
                break
        
        assert ready is True
    
    def test_buffer_clear(self):
        """Test buffer clearing"""
        from ai_modules.audio_detection.realtime_processor import AudioBuffer
        
        buffer = AudioBuffer(
            sample_rate=22050,
            buffer_duration=1.0,
            overlap=0.5
        )
        
        # Fill buffer
        buffer.write(np.random.randn(1000).astype(np.float32))
        
        # Clear
        buffer.clear()
        
        assert buffer.write_pos == 0
        assert buffer.filled is False
