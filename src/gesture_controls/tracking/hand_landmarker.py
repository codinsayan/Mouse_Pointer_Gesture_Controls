"""MediaPipe Tasks Hand Landmarker adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gesture_controls.config import AppConfig
from gesture_controls.errors import ModelAssetError, TrackerInitializationError
from gesture_controls.tracking.landmarks import Landmark


@dataclass(frozen=True, slots=True)
class TrackingResult:
    landmarks: tuple[Landmark, ...] = ()
    handedness: str | None = None
    confidence: float | None = None

    @property
    def hand_detected(self) -> bool:
        return bool(self.landmarks)


class HandLandmarkerTracker:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._landmarker: Any | None = None
        self._mp: Any | None = None

    def open(self) -> "HandLandmarkerTracker":
        model_path = Path(self._config.model_path)
        if not model_path.is_file():
            raise ModelAssetError(
                f"MediaPipe model not found: {model_path}. See assets/models/README.md."
            )
        try:
            import mediapipe as mp

            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=self._config.detection_confidence,
                min_hand_presence_confidence=self._config.presence_confidence,
                min_tracking_confidence=self._config.tracking_confidence,
            )
            self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
            self._mp = mp
        except Exception as exc:
            raise TrackerInitializationError(
                "MediaPipe Hand Landmarker initialization failed. Verify the "
                "dependency installation and official model asset."
            ) from exc
        return self

    def detect(self, rgb_frame: Any, timestamp_ms: int) -> TrackingResult:
        if self._landmarker is None or self._mp is None:
            raise RuntimeError("Hand tracker has not been opened.")
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return TrackingResult()
        points = tuple(
            Landmark(float(point.x), float(point.y), float(point.z))
            for point in result.hand_landmarks[0]
        )
        handedness = None
        confidence = None
        if result.handedness and result.handedness[0]:
            category = result.handedness[0][0]
            handedness = category.category_name or None
            confidence = float(category.score)
        return TrackingResult(points, handedness, confidence)

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
        self._mp = None

    def __enter__(self) -> "HandLandmarkerTracker":
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

