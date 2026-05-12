"""
Visual Threat Recognition Module
YOLO-based weapon detection and pose-based threat identification
Supports: Weapon detection, Aggressive gestures, Stalking behavior
"""

import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import mediapipe as mp
except ImportError:
    mp = None

logger = logging.getLogger(__name__)


class VisualThreatType(Enum):
    """Types of visual threats"""
    NONE = 0
    WEAPON_KNIFE = 1
    WEAPON_GUN = 2
    WEAPON_BAT = 3
    WEAPON_OTHER = 4
    AGGRESSIVE_POSE = 5
    STALKING_BEHAVIOR = 6
    SUSPICIOUS_APPROACH = 7
    MULTIPLE_THREATS = 8


@dataclass
class BoundingBox:
    """Bounding box for detected objects"""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def area(self) -> float:
        return (self.x2 - self.x1) * (self.y2 - self.y1)


@dataclass
class PoseData:
    """Human pose landmark data"""
    landmarks: List[Tuple[float, float, float]]  # x, y, visibility
    confidence: float
    bbox: Optional[BoundingBox] = None


@dataclass
class VisualDetectionResult:
    """Result from visual threat detection"""
    threat_type: VisualThreatType
    confidence: float
    detections: List[BoundingBox] = field(default_factory=list)
    poses: List[PoseData] = field(default_factory=list)
    frame_timestamp: float = 0.0
    is_threat: bool = False
    risk_level: int = 0
    threat_details: Dict = field(default_factory=dict)


class LowLightEnhancer:
    """
    Image enhancement for low-light conditions
    Uses histogram equalization and denoising
    """
    
    def __init__(self, clip_limit: float = 2.0, tile_size: int = 8):
        self.clip_limit = clip_limit
        self.tile_size = tile_size
        if cv2 is not None:
            self.clahe = cv2.createCLAHE(
                clipLimit=clip_limit,
                tileGridSize=(tile_size, tile_size)
            )
    
    def enhance(self, image: np.ndarray) -> np.ndarray:
        """Enhance low-light image"""
        if cv2 is None:
            return image
        
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        l_enhanced = self.clahe.apply(l)
        
        # Merge and convert back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Denoise
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return enhanced
    
    def needs_enhancement(self, image: np.ndarray) -> bool:
        """Check if image needs low-light enhancement"""
        if cv2 is None:
            return False
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return mean_brightness < 60


class WeaponDetector:
    """
    YOLO-based weapon detection
    Detects: Knives, guns, bats, bottles, and other threatening objects
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.7,
        nms_threshold: float = 0.45
    ):
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.model = None
        
        # Weapon class mapping
        self.weapon_classes = {
            'knife': VisualThreatType.WEAPON_KNIFE,
            'gun': VisualThreatType.WEAPON_GUN,
            'pistol': VisualThreatType.WEAPON_GUN,
            'rifle': VisualThreatType.WEAPON_GUN,
            'bat': VisualThreatType.WEAPON_BAT,
            'rod': VisualThreatType.WEAPON_OTHER,
            'bottle': VisualThreatType.WEAPON_OTHER
        }
        
        if model_path and YOLO is not None:
            self.load_model(model_path)
    
    def load_model(self, path: str) -> None:
        """Load YOLO model"""
        if YOLO is None:
            raise ImportError("ultralytics package required for YOLO")
        
        try:
            self.model = YOLO(path)
            logger.info(f"Weapon detection model loaded from {path}")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            # Fall back to pre-trained YOLOv8n
            self.model = YOLO('yolov8n.pt')
    
    def detect(self, frame: np.ndarray) -> List[BoundingBox]:
        """
        Detect weapons in frame
        
        Args:
            frame: BGR image
            
        Returns:
            List of bounding boxes for detected weapons
        """
        if self.model is None:
            return []
        
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.nms_threshold,
            verbose=False
        )[0]
        
        detections = []
        for box in results.boxes:
            class_id = int(box.cls[0])
            class_name = results.names[class_id]
            conf = float(box.conf[0])
            
            # Check if this is a weapon class
            if class_name.lower() in self.weapon_classes or class_name.lower() == 'person':
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(BoundingBox(
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    confidence=conf,
                    class_id=class_id,
                    class_name=class_name
                ))
        
        return detections
    
    def get_threat_type(self, class_name: str) -> VisualThreatType:
        """Get threat type from class name"""
        return self.weapon_classes.get(
            class_name.lower(),
            VisualThreatType.WEAPON_OTHER
        )


class PoseAnalyzer:
    """
    Pose-based threat detection using MediaPipe
    Analyzes body language for aggressive or threatening behavior
    """
    
    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        self.pose = None
        if mp is not None:
            self.pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
        
        # Landmark indices for analysis
        self.LANDMARKS = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26
        }
    
    def extract_pose(self, frame: np.ndarray) -> Optional[PoseData]:
        """Extract pose landmarks from frame"""
        if self.pose is None:
            return None
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        if results.pose_landmarks:
            landmarks = [
                (lm.x, lm.y, lm.visibility)
                for lm in results.pose_landmarks.landmark
            ]
            return PoseData(
                landmarks=landmarks,
                confidence=np.mean([lm[2] for lm in landmarks])
            )
        return None
    
    def analyze_aggression(self, pose: PoseData) -> Tuple[bool, float, str]:
        """
        Analyze pose for aggressive behavior
        
        Returns:
            Tuple of (is_aggressive, confidence, description)
        """
        if not pose or len(pose.landmarks) < 25:
            return False, 0.0, ""
        
        landmarks = pose.landmarks
        
        # Get key landmarks
        left_wrist = landmarks[self.LANDMARKS['left_wrist']]
        right_wrist = landmarks[self.LANDMARKS['right_wrist']]
        left_shoulder = landmarks[self.LANDMARKS['left_shoulder']]
        right_shoulder = landmarks[self.LANDMARKS['right_shoulder']]
        nose = landmarks[self.LANDMARKS['nose']]
        
        aggressive_indicators = []
        confidence_scores = []
        
        # Check for raised arms (potential striking pose)
        if left_wrist[1] < left_shoulder[1]:  # Wrist above shoulder
            aggressive_indicators.append("raised_left_arm")
            confidence_scores.append(left_wrist[2])
        
        if right_wrist[1] < right_shoulder[1]:
            aggressive_indicators.append("raised_right_arm")
            confidence_scores.append(right_wrist[2])
        
        # Check for wide stance (confrontational)
        left_hip = landmarks[self.LANDMARKS['left_hip']]
        right_hip = landmarks[self.LANDMARKS['right_hip']]
        hip_width = abs(left_hip[0] - right_hip[0])
        shoulder_width = abs(left_shoulder[0] - right_shoulder[0])
        
        if hip_width > shoulder_width * 1.3:
            aggressive_indicators.append("wide_stance")
            confidence_scores.append(0.7)
        
        # Check for forward lean
        shoulder_center = (left_shoulder[1] + right_shoulder[1]) / 2
        hip_center = (left_hip[1] + right_hip[1]) / 2
        
        if nose[1] > shoulder_center and shoulder_center < hip_center * 0.9:
            aggressive_indicators.append("forward_lean")
            confidence_scores.append(0.6)
        
        # Determine overall aggression
        is_aggressive = len(aggressive_indicators) >= 2
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        description = ", ".join(aggressive_indicators)
        
        return is_aggressive, overall_confidence, description
    
    def detect_following_behavior(
        self,
        target_poses: List[PoseData],
        follower_poses: List[PoseData],
        frames_threshold: int = 30
    ) -> Tuple[bool, float]:
        """
        Detect stalking/following behavior over time
        
        Args:
            target_poses: Sequence of target person poses
            follower_poses: Sequence of potential follower poses
            frames_threshold: Minimum frames to establish pattern
            
        Returns:
            Tuple of (is_following, confidence)
        """
        if len(target_poses) < frames_threshold or len(follower_poses) < frames_threshold:
            return False, 0.0
        
        # Calculate movement correlation
        target_movements = []
        follower_movements = []
        
        for i in range(1, min(len(target_poses), len(follower_poses))):
            if target_poses[i] and target_poses[i-1]:
                t_nose = target_poses[i].landmarks[0]
                t_prev = target_poses[i-1].landmarks[0]
                target_movements.append((t_nose[0] - t_prev[0], t_nose[1] - t_prev[1]))
            
            if follower_poses[i] and follower_poses[i-1]:
                f_nose = follower_poses[i].landmarks[0]
                f_prev = follower_poses[i-1].landmarks[0]
                follower_movements.append((f_nose[0] - f_prev[0], f_nose[1] - f_prev[1]))
        
        if len(target_movements) < 10 or len(follower_movements) < 10:
            return False, 0.0
        
        # Calculate correlation coefficient
        min_len = min(len(target_movements), len(follower_movements))
        target_x = [m[0] for m in target_movements[:min_len]]
        follower_x = [m[0] for m in follower_movements[:min_len]]
        
        correlation = np.corrcoef(target_x, follower_x)[0, 1]
        
        is_following = correlation > 0.7
        confidence = max(0, correlation) if not np.isnan(correlation) else 0.0
        
        return is_following, confidence


class VisualThreatDetector:
    """
    Main visual threat detection system
    Integrates weapon detection, pose analysis, and behavior recognition
    """
    
    def __init__(
        self,
        weapon_model_path: Optional[str] = None,
        confidence_threshold: float = 0.7,
        enable_low_light: bool = True,
        enable_pose: bool = True
    ):
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        self.weapon_detector = WeaponDetector(
            model_path=weapon_model_path,
            confidence_threshold=confidence_threshold
        )
        
        self.low_light_enhancer = LowLightEnhancer() if enable_low_light else None
        self.pose_analyzer = PoseAnalyzer() if enable_pose else None
        
        # Tracking for behavior analysis
        self.pose_history: Dict[int, List[PoseData]] = {}
        self.detection_history: List[VisualDetectionResult] = []
        
        # Risk level mapping
        self.threat_risk_levels = {
            VisualThreatType.NONE: 0,
            VisualThreatType.SUSPICIOUS_APPROACH: 2,
            VisualThreatType.STALKING_BEHAVIOR: 3,
            VisualThreatType.AGGRESSIVE_POSE: 3,
            VisualThreatType.WEAPON_BAT: 3,
            VisualThreatType.WEAPON_OTHER: 3,
            VisualThreatType.WEAPON_KNIFE: 4,
            VisualThreatType.WEAPON_GUN: 4,
            VisualThreatType.MULTIPLE_THREATS: 4
        }
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame including low-light enhancement"""
        if self.low_light_enhancer and self.low_light_enhancer.needs_enhancement(frame):
            return self.low_light_enhancer.enhance(frame)
        return frame
    
    def detect_threats(
        self,
        frame: np.ndarray,
        timestamp: float = 0.0
    ) -> VisualDetectionResult:
        """
        Detect all visual threats in frame
        
        Args:
            frame: BGR image
            timestamp: Frame timestamp
            
        Returns:
            VisualDetectionResult with all detected threats
        """
        # Preprocess
        processed_frame = self.preprocess_frame(frame)
        
        # Detect weapons
        weapon_detections = self.weapon_detector.detect(processed_frame)
        
        # Extract poses and analyze
        poses = []
        aggressive_detected = False
        aggression_confidence = 0.0
        
        if self.pose_analyzer:
            pose = self.pose_analyzer.extract_pose(processed_frame)
            if pose:
                poses.append(pose)
                aggressive, conf, _ = self.pose_analyzer.analyze_aggression(pose)
                if aggressive:
                    aggressive_detected = True
                    aggression_confidence = conf
        
        # Determine overall threat
        threats_found = []
        confidences = []
        
        # Process weapon detections
        for det in weapon_detections:
            if det.class_name.lower() != 'person':
                threat_type = self.weapon_detector.get_threat_type(det.class_name)
                threats_found.append(threat_type)
                confidences.append(det.confidence)
        
        # Add aggression if detected
        if aggressive_detected:
            threats_found.append(VisualThreatType.AGGRESSIVE_POSE)
            confidences.append(aggression_confidence)
        
        # Determine final threat type
        if len(threats_found) == 0:
            final_threat = VisualThreatType.NONE
            final_confidence = 0.0
        elif len(threats_found) > 1:
            final_threat = VisualThreatType.MULTIPLE_THREATS
            final_confidence = max(confidences)
        else:
            final_threat = threats_found[0]
            final_confidence = confidences[0]
        
        is_threat = final_threat != VisualThreatType.NONE
        risk_level = self.threat_risk_levels.get(final_threat, 0)
        
        result = VisualDetectionResult(
            threat_type=final_threat,
            confidence=final_confidence,
            detections=weapon_detections,
            poses=poses,
            frame_timestamp=timestamp,
            is_threat=is_threat,
            risk_level=risk_level,
            threat_details={
                'weapon_count': len([d for d in weapon_detections if d.class_name != 'person']),
                'person_count': len([d for d in weapon_detections if d.class_name == 'person']),
                'aggressive_pose': aggressive_detected,
                'individual_threats': [t.name for t in threats_found]
            }
        )
        
        # Add to history
        self.detection_history.append(result)
        if len(self.detection_history) > 100:
            self.detection_history.pop(0)
        
        return result
    
    def get_threat_summary(self) -> Dict:
        """Get summary of recent threat detections"""
        if not self.detection_history:
            return {'total_frames': 0, 'threats_detected': 0}
        
        threats = [r for r in self.detection_history if r.is_threat]
        
        return {
            'total_frames': len(self.detection_history),
            'threats_detected': len(threats),
            'max_risk_level': max((r.risk_level for r in self.detection_history), default=0),
            'threat_types': list(set(r.threat_type.name for r in threats)),
            'average_confidence': np.mean([r.confidence for r in threats]) if threats else 0
        }


class RealtimeVisualProcessor:
    """
    Real-time video processing for continuous threat detection
    """
    
    def __init__(
        self,
        detector: VisualThreatDetector,
        camera_id: int = 0,
        frame_skip: int = 2
    ):
        self.detector = detector
        self.camera_id = camera_id
        self.frame_skip = frame_skip
        self.cap = None
        self.running = False
        
    def start_capture(self) -> bool:
        """Start video capture"""
        if cv2 is None:
            logger.error("OpenCV not installed")
            return False
        
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            logger.error("Could not open camera")
            return False
        
        self.running = True
        return True
    
    def process_frame(self) -> Optional[VisualDetectionResult]:
        """Process a single frame"""
        if not self.cap or not self.running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        return self.detector.detect_threats(frame, time.time())
    
    def stop(self) -> None:
        """Stop capture"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None


def create_visual_detector(
    model_path: Optional[str] = None,
    config: Optional[Dict] = None
) -> VisualThreatDetector:
    """Factory function to create visual threat detector"""
    params = {
        'weapon_model_path': model_path,
        'confidence_threshold': 0.7,
        'enable_low_light': True,
        'enable_pose': True
    }
    if config:
        params.update(config)
    
    return VisualThreatDetector(**params)
