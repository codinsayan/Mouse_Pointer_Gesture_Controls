"""Validated Iteration 1 configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    target_fps: int = 30
    model_path: Path = Path("assets/models/hand_landmarker.task")
    detection_confidence: float = 0.5
    presence_confidence: float = 0.5
    tracking_confidence: float = 0.5
    cursor_region_left: float = 0.12
    cursor_region_top: float = 0.10
    cursor_region_right: float = 0.88
    cursor_region_bottom: float = 0.90
    cursor_smoothing_seconds: float = 0.08
    cursor_minimum_movement: float = 0.002
    window_title: str = "Gesture Controls - Iteration 2 (Dry Run)"

    def __post_init__(self) -> None:
        if self.camera_index < 0:
            raise ValueError("camera_index must be zero or greater")
        for name in ("frame_width", "frame_height", "target_fps"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero")
        for name in (
            "detection_confidence",
            "presence_confidence",
            "tracking_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")
        if not self.window_title.strip():
            raise ValueError("window_title must not be empty")
        if not 0.0 <= self.cursor_region_left < self.cursor_region_right <= 1.0:
            raise ValueError("cursor horizontal region must be ordered within 0.0..1.0")
        if not 0.0 <= self.cursor_region_top < self.cursor_region_bottom <= 1.0:
            raise ValueError("cursor vertical region must be ordered within 0.0..1.0")
        if self.cursor_smoothing_seconds <= 0.0:
            raise ValueError("cursor_smoothing_seconds must be greater than zero")
        if not 0.0 <= self.cursor_minimum_movement <= 1.0:
            raise ValueError("cursor_minimum_movement must be between 0.0 and 1.0")
