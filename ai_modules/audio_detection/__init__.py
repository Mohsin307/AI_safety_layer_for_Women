"""Audio detection module initialization"""
from .audio_threat_detector import (
    AudioThreatDetector,
    AudioThreatModel,
    AudioFeatureExtractor,
    AudioDetectionResult,
    AudioThreatCategory,
    create_audio_detector
)
from .realtime_processor import (
    RealtimeAudioProcessor,
    AudioStreamConfig,
    VoiceActivityDetector,
    AudioBuffer,
    EdgeOptimizedProcessor
)

__all__ = [
    "AudioThreatDetector",
    "AudioThreatModel",
    "AudioFeatureExtractor",
    "AudioDetectionResult",
    "AudioThreatCategory",
    "create_audio_detector",
    "RealtimeAudioProcessor",
    "AudioStreamConfig",
    "VoiceActivityDetector",
    "AudioBuffer",
    "EdgeOptimizedProcessor"
]
