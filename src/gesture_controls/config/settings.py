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
    left_pinch_activation_ratio: float = 0.30
    left_pinch_release_ratio: float = 0.42
    left_pinch_activation_hold_seconds: float = 0.03
    left_pinch_release_hold_seconds: float = 0.03
    left_click_cooldown_seconds: float = 0.06
    double_click_pinch_activation_ratio: float = 0.30
    double_click_pinch_release_ratio: float = 0.42
    double_click_activation_hold_seconds: float = 0.03
    double_click_release_hold_seconds: float = 0.03
    double_click_cooldown_seconds: float = 0.06
    post_click_cursor_resume_delay_seconds: float = 0.0
    window_title: str = "Gesture Controls - Iteration 3 (Dry Run)"

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
        if not 0.0 < self.left_pinch_activation_ratio < self.left_pinch_release_ratio:
            raise ValueError("left-pinch ratios must satisfy 0 < activation < release")
        if not (
            0.0
            < self.double_click_pinch_activation_ratio
            < self.double_click_pinch_release_ratio
        ):
            raise ValueError(
                "double-click pinch ratios must satisfy 0 < activation < release"
            )
        for name in (
            "left_pinch_activation_hold_seconds",
            "left_pinch_release_hold_seconds",
            "left_click_cooldown_seconds",
            "double_click_activation_hold_seconds",
            "double_click_release_hold_seconds",
            "double_click_cooldown_seconds",
            "post_click_cursor_resume_delay_seconds",
        ):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be zero or greater")
