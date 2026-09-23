from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

LEFT_EYE_INDICES: List[int] = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES: List[int] = [33, 160, 158, 133, 153, 144]


@dataclass
class TelemetryData:
    ear_left: float = 0.0
    ear_right: float = 0.0
    ear_avg: float = 0.0
    eyes_closed: bool = False
    closed_duration: float = 0.0
    is_drowsy: bool = False
    face_detected: bool = False
    left_eye_coords: List[Tuple[int, int]] = field(default_factory=list)
    right_eye_coords: List[Tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ear_left": round(self.ear_left, 3),
            "ear_right": round(self.ear_right, 3),
            "ear_avg": round(self.ear_avg, 3),
            "eyes_closed": self.eyes_closed,
            "closed_duration": round(self.closed_duration, 1),
            "is_drowsy": self.is_drowsy,
            "face_detected": self.face_detected,
            "left_eye_coords": self.left_eye_coords,
            "right_eye_coords": self.right_eye_coords,
        }


class DrowsinessDetector:
    def __init__(
        self,
        ear_threshold: float = 0.18,
        drowsy_time_threshold: float = 2.0,
    ) -> None:
        self.ear_threshold = ear_threshold
        self.drowsy_time_threshold = drowsy_time_threshold

        self._eyes_closed_since: Optional[float] = None
        self._mp_face_mesh = None
        self._face_mesh = None
        self._use_fallback = False

        self._init_mediapipe()

    def _init_mediapipe(self) -> None:
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
                self._mp_face_mesh = mp.solutions.face_mesh
                self._face_mesh = self._mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                return
        except Exception:
            pass

        try:
            from mediapipe.python.solutions import face_mesh as mp_face_mesh
            self._mp_face_mesh = mp_face_mesh
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            return
        except Exception:
            pass

        self._use_fallback = True
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    @staticmethod
    def calculate_ear(
        landmarks: Any,
        eye_indices: List[int],
        frame_w: int,
        frame_h: int,
    ) -> Tuple[float, List[Tuple[int, int]]]:
        coords: List[Tuple[int, int]] = []
        for idx in eye_indices:
            lm = landmarks[idx]
            coords.append((int(lm.x * frame_w), int(lm.y * frame_h)))

        p1, p2, p3, p4, p5, p6 = coords
        v1 = math.dist(p2, p6)
        v2 = math.dist(p3, p5)
        h = math.dist(p1, p4)

        if h < 1e-6:
            return 0.0, coords

        ear = (v1 + v2) / (2.0 * h)
        return ear, coords

    def process_frame(self, bgr_frame: np.ndarray) -> TelemetryData:
        telemetry = TelemetryData()
        h, w, _ = bgr_frame.shape

        if not self._use_fallback and self._face_mesh is not None:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            results = self._face_mesh.process(rgb)

            if results.multi_face_landmarks:
                telemetry.face_detected = True
                landmarks = results.multi_face_landmarks[0].landmark

                ear_l, left_pts = self.calculate_ear(landmarks, LEFT_EYE_INDICES, w, h)
                ear_r, right_pts = self.calculate_ear(landmarks, RIGHT_EYE_INDICES, w, h)
                ear_avg = (ear_l + ear_r) / 2.0

                telemetry.ear_left = ear_l
                telemetry.ear_right = ear_r
                telemetry.ear_avg = ear_avg
                telemetry.left_eye_coords = left_pts
                telemetry.right_eye_coords = right_pts
            else:
                self._eyes_closed_since = None
                return telemetry
        else:
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                telemetry.face_detected = True
                fx, fy, fw, fh = faces[0]
                roi_gray = gray[fy : fy + int(fh * 0.6), fx : fx + fw]
                eyes = self._eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
                ear_avg = 0.12 if len(eyes) == 0 else 0.28

                telemetry.ear_avg = ear_avg
                telemetry.ear_left = ear_avg
                telemetry.ear_right = ear_avg
            else:
                self._eyes_closed_since = None
                return telemetry

        now = time.monotonic()
        if telemetry.ear_avg < self.ear_threshold:
            telemetry.eyes_closed = True
            if self._eyes_closed_since is None:
                self._eyes_closed_since = now
            telemetry.closed_duration = now - self._eyes_closed_since

            if telemetry.closed_duration >= self.drowsy_time_threshold:
                telemetry.is_drowsy = True
        else:
            self._eyes_closed_since = None
            telemetry.eyes_closed = False
            telemetry.closed_duration = 0.0
            telemetry.is_drowsy = False

        return telemetry

    def release(self) -> None:
        if self._face_mesh is not None:
            try:
                self._face_mesh.close()
            except Exception:
                pass
