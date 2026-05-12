"""
Real-time Audio Processor
Handles microphone input and streaming audio analysis
Optimized for low-latency, battery-efficient processing
"""

import numpy as np
import threading
import queue
import time
import logging
from typing import Callable, Optional, List
from dataclasses import dataclass

try:
    import pyaudio
except ImportError:
    pyaudio = None

from .audio_threat_detector import (
    AudioThreatDetector,
    AudioDetectionResult,
    AudioThreatCategory
)

logger = logging.getLogger(__name__)


@dataclass
class AudioStreamConfig:
    """Configuration for audio streaming"""
    sample_rate: int = 22050
    chunk_size: int = 1024
    channels: int = 1
    format_bits: int = 16
    buffer_duration: float = 3.0
    overlap: float = 0.5
    vad_threshold: float = 0.01  # Voice Activity Detection threshold


class VoiceActivityDetector:
    """
    Voice Activity Detection for power efficiency
    Only triggers full analysis when audio activity is detected
    """
    
    def __init__(self, threshold: float = 0.01, min_duration: float = 0.5):
        self.threshold = threshold
        self.min_duration = min_duration
        self.sample_rate = 22050
        
    def is_active(self, audio: np.ndarray) -> bool:
        """Check if audio contains significant activity"""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Check zero crossing rate (high for speech)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / 2
        zcr = zero_crossings / len(audio)
        
        # Combined activity check
        return rms > self.threshold or zcr > 0.1


class AudioBuffer:
    """
    Circular buffer for streaming audio
    Maintains fixed-size buffer with overlap for analysis
    """
    
    def __init__(
        self,
        sample_rate: int,
        buffer_duration: float,
        overlap: float = 0.5
    ):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        self.overlap_size = int(self.buffer_size * overlap)
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self.write_pos = 0
        self.filled = False
        
    def write(self, audio_chunk: np.ndarray) -> bool:
        """
        Write audio chunk to buffer
        Returns True when buffer is ready for analysis
        """
        chunk_len = len(audio_chunk)
        
        if self.write_pos + chunk_len >= self.buffer_size:
            # Buffer full - copy remaining to fill
            remaining = self.buffer_size - self.write_pos
            self.buffer[self.write_pos:] = audio_chunk[:remaining]
            self.filled = True
            
            # Shift buffer with overlap and continue writing
            self.buffer[:self.overlap_size] = self.buffer[-self.overlap_size:]
            self.write_pos = self.overlap_size
            
            if remaining < chunk_len:
                leftover = audio_chunk[remaining:]
                self.buffer[self.write_pos:self.write_pos + len(leftover)] = leftover
                self.write_pos += len(leftover)
            
            return True
        else:
            self.buffer[self.write_pos:self.write_pos + chunk_len] = audio_chunk
            self.write_pos += chunk_len
            return False
    
    def get_buffer(self) -> np.ndarray:
        """Get current buffer contents"""
        return self.buffer.copy()
    
    def clear(self) -> None:
        """Clear the buffer"""
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self.write_pos = 0
        self.filled = False


class RealtimeAudioProcessor:
    """
    Real-time audio processing pipeline
    Captures microphone input and performs continuous threat detection
    """
    
    def __init__(
        self,
        detector: AudioThreatDetector,
        config: Optional[AudioStreamConfig] = None,
        on_threat_detected: Optional[Callable[[AudioDetectionResult], None]] = None
    ):
        self.detector = detector
        self.config = config or AudioStreamConfig()
        self.on_threat_detected = on_threat_detected
        
        # Audio interface
        self.audio = None
        self.stream = None
        
        # Processing components
        self.buffer = AudioBuffer(
            self.config.sample_rate,
            self.config.buffer_duration,
            self.config.overlap
        )
        self.vad = VoiceActivityDetector(self.config.vad_threshold)
        
        # Threading
        self.audio_queue = queue.Queue(maxsize=100)
        self.result_queue = queue.Queue(maxsize=100)
        self.running = False
        self.capture_thread = None
        self.process_thread = None
        
        # Statistics
        self.stats = {
            'chunks_processed': 0,
            'threats_detected': 0,
            'false_positives_filtered': 0,
            'average_latency_ms': 0,
            'vad_skipped': 0
        }
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for audio capture"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        audio_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)
        audio_data /= 32768.0  # Normalize to [-1, 1]
        
        try:
            self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            logger.warning("Audio queue full, dropping frame")
        
        return (None, pyaudio.paContinue if self.running else pyaudio.paComplete)
    
    def _capture_loop(self) -> None:
        """Audio capture thread (alternative to callback)"""
        while self.running:
            try:
                if self.stream and self.stream.is_active():
                    data = self.stream.read(
                        self.config.chunk_size,
                        exception_on_overflow=False
                    )
                    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    audio_data /= 32768.0
                    
                    try:
                        self.audio_queue.put_nowait(audio_data)
                    except queue.Full:
                        pass
            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.01)
    
    def _process_loop(self) -> None:
        """Audio processing thread"""
        latencies = []
        
        while self.running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Voice Activity Detection for power saving
                if not self.vad.is_active(audio_chunk):
                    self.stats['vad_skipped'] += 1
                    continue
                
                # Add to buffer
                buffer_ready = self.buffer.write(audio_chunk)
                
                if buffer_ready:
                    start_time = time.time()
                    
                    # Get buffer and run detection
                    buffer_data = self.buffer.get_buffer()
                    result = self.detector.detect_threat(
                        buffer_data,
                        timestamp=time.time()
                    )
                    
                    # Calculate latency
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                    if len(latencies) > 100:
                        latencies.pop(0)
                    self.stats['average_latency_ms'] = np.mean(latencies)
                    
                    self.stats['chunks_processed'] += 1
                    
                    # Handle threat detection
                    if result.is_threat:
                        self.stats['threats_detected'] += 1
                        self.result_queue.put(result)
                        
                        if self.on_threat_detected:
                            self.on_threat_detected(result)
                            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def start(self) -> bool:
        """Start real-time audio processing"""
        if pyaudio is None:
            logger.error("PyAudio not installed")
            return False
        
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find suitable input device
            device_index = None
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_index = i
                    break
            
            if device_index is None:
                logger.error("No audio input device found")
                return False
            
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.config.chunk_size
            )
            
            self.running = True
            
            # Start threads
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.process_thread = threading.Thread(
                target=self._process_loop,
                daemon=True
            )
            
            self.capture_thread.start()
            self.process_thread.start()
            
            logger.info("Real-time audio processing started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio processing: {e}")
            self.stop()
            return False
    
    def stop(self) -> None:
        """Stop audio processing"""
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        if self.process_thread:
            self.process_thread.join(timeout=1.0)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        logger.info("Audio processing stopped")
    
    def get_latest_results(self, max_results: int = 10) -> List[AudioDetectionResult]:
        """Get latest detection results"""
        results = []
        while not self.result_queue.empty() and len(results) < max_results:
            try:
                results.append(self.result_queue.get_nowait())
            except queue.Empty:
                break
        return results
    
    def get_stats(self) -> dict:
        """Get processing statistics"""
        return self.stats.copy()


class EdgeOptimizedProcessor:
    """
    Edge-optimized audio processor for mobile/IoT devices
    Implements power management and adaptive processing
    """
    
    def __init__(
        self,
        detector: AudioThreatDetector,
        low_power_mode: bool = True
    ):
        self.detector = detector
        self.low_power_mode = low_power_mode
        self.processor = None
        self.activity_level = 0.0  # Adaptive processing trigger
        
    def configure_for_device(self, device_type: str) -> AudioStreamConfig:
        """Configure settings based on device capabilities"""
        configs = {
            'smartphone': AudioStreamConfig(
                sample_rate=22050,
                chunk_size=1024,
                buffer_duration=3.0,
                overlap=0.5
            ),
            'smartwatch': AudioStreamConfig(
                sample_rate=16000,
                chunk_size=512,
                buffer_duration=2.0,
                overlap=0.3
            ),
            'iot_device': AudioStreamConfig(
                sample_rate=16000,
                chunk_size=256,
                buffer_duration=2.0,
                overlap=0.25
            )
        }
        return configs.get(device_type, configs['smartphone'])
    
    def adaptive_processing(
        self,
        audio: np.ndarray,
        battery_level: float
    ) -> Optional[AudioDetectionResult]:
        """
        Adaptive processing based on battery and activity
        
        Args:
            audio: Audio data to process
            battery_level: Current battery level (0-1)
            
        Returns:
            Detection result or None if skipped
        """
        # Calculate current activity level
        rms = np.sqrt(np.mean(audio ** 2))
        self.activity_level = 0.9 * self.activity_level + 0.1 * rms
        
        # Skip processing in low power mode if activity is low
        if self.low_power_mode and battery_level < 0.2:
            if self.activity_level < 0.02:
                return None
        
        # Full processing
        return self.detector.detect_threat(audio)
