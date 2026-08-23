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
    minimum_runtime_hand_confidence: float = 0.5
    dominant_hand: str = "any"
    cursor_region_left: float = 0.12
    cursor_region_top: float = 0.10
    cursor_region_right: float = 0.88
    cursor_region_bottom: float = 0.90
    cursor_smoothing_seconds: float = 0.08
    cursor_sensitivity: float = 1.0
    cursor_minimum_movement: float = 0.002
    pointer_extension_activation_ratio: float = 0.18
    pointer_extension_release_ratio: float = 0.10
    calibration_min_samples: int = 60
    calibration_low_quantile: float = 0.05
    calibration_high_quantile: float = 0.95
    calibration_padding_ratio: float = 0.05
    calibration_minimum_span: float = 0.25
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
    right_pinch_activation_ratio: float = 0.30
    right_pinch_release_ratio: float = 0.42
    right_click_activation_hold_seconds: float = 0.03
    right_click_release_hold_seconds: float = 0.03
    right_click_cooldown_seconds: float = 0.06
    fist_folded_activation_ratio: float = 0.10
    fist_folded_release_ratio: float = 0.18
    fist_activation_hold_seconds: float = 0.06
    fist_release_hold_seconds: float = 0.05
    drag_activation_hold_seconds: float = 0.25
    drag_cursor_minimum_movement: float = 0.0005
    pause_extension_activation_ratio: float = 0.18
    pause_extension_release_ratio: float = 0.10
    pause_activation_hold_seconds: float = 0.35
    pause_release_hold_seconds: float = 0.05
    zoom_span_activation_ratio: float = 0.45
    zoom_span_release_ratio: float = 0.85
    zoom_other_fingers_extension_activation_ratio: float = 0.12
    zoom_other_fingers_extension_release_ratio: float = 0.08
    zoom_activation_hold_seconds: float = 0.06
    zoom_release_hold_seconds: float = 0.05
    zoom_step_distance_ratio: float = 0.08
    zoom_max_steps_per_frame: int = 3
    scroll_extension_activation_ratio: float = 0.18
    scroll_extension_release_ratio: float = 0.10
    scroll_folded_activation_ratio: float = 0.10
    scroll_folded_release_ratio: float = 0.18
    scroll_activation_hold_seconds: float = 0.06
    scroll_release_hold_seconds: float = 0.05
    scroll_step_distance_ratio: float = 0.08
    scroll_max_steps_per_frame: int = 3
    post_click_cursor_resume_delay_seconds: float = 0.0
    window_title: str = "Gesture Controls - Iteration 8"

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
            "minimum_runtime_hand_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")
        if not self.window_title.strip():
            raise ValueError("window_title must not be empty")
        if self.dominant_hand not in {"any", "left", "right"}:
            raise ValueError("dominant_hand must be 'any', 'left', or 'right'")
        if not 0.0 <= self.cursor_region_left < self.cursor_region_right <= 1.0:
            raise ValueError("cursor horizontal region must be ordered within 0.0..1.0")
        if not 0.0 <= self.cursor_region_top < self.cursor_region_bottom <= 1.0:
            raise ValueError("cursor vertical region must be ordered within 0.0..1.0")
        if self.cursor_smoothing_seconds <= 0.0:
            raise ValueError("cursor_smoothing_seconds must be greater than zero")
        if not 0.1 <= self.cursor_sensitivity <= 3.0:
            raise ValueError("cursor_sensitivity must be between 0.1 and 3.0")
        if not 0.0 <= self.cursor_minimum_movement <= 1.0:
            raise ValueError("cursor_minimum_movement must be between 0.0 and 1.0")
        if not (
            0.0
            <= self.pointer_extension_release_ratio
            < self.pointer_extension_activation_ratio
        ):
            raise ValueError(
                "pointer extension ratios must satisfy 0 <= release < activation"
            )
        if (
            not isinstance(self.calibration_min_samples, int)
            or isinstance(self.calibration_min_samples, bool)
            or self.calibration_min_samples < 10
        ):
            raise ValueError("calibration_min_samples must be at least 10")
        if not (
            0.0
            <= self.calibration_low_quantile
            < self.calibration_high_quantile
            <= 1.0
        ):
            raise ValueError("calibration quantiles must be ordered within 0.0..1.0")
        if not 0.0 <= self.calibration_padding_ratio <= 0.5:
            raise ValueError("calibration_padding_ratio must be between 0.0 and 0.5")
        if not 0.0 < self.calibration_minimum_span <= 1.0:
            raise ValueError("calibration_minimum_span must be within 0.0..1.0")
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
        if not 0.0 < self.right_pinch_activation_ratio < self.right_pinch_release_ratio:
            raise ValueError("right-pinch ratios must satisfy 0 < activation < release")
        if not (
            0.0
            <= self.fist_folded_activation_ratio
            < self.fist_folded_release_ratio
        ):
            raise ValueError(
                "fist folded ratios must satisfy 0 <= activation < release"
            )
        if not 0.0 <= self.drag_cursor_minimum_movement <= 1.0:
            raise ValueError("drag_cursor_minimum_movement must be between 0.0 and 1.0")
        if not (
            0.0
            <= self.pause_extension_release_ratio
            < self.pause_extension_activation_ratio
        ):
            raise ValueError(
                "pause extension ratios must satisfy 0 <= release < activation"
            )
        if not 0.0 < self.zoom_span_activation_ratio < self.zoom_span_release_ratio:
            raise ValueError("zoom span ratios must satisfy 0 < activation < release")
        if not (
            0.0
            <= self.zoom_other_fingers_extension_release_ratio
            < self.zoom_other_fingers_extension_activation_ratio
        ):
            raise ValueError(
                "zoom other-finger extension ratios must satisfy "
                "0 <= release < activation"
            )
        if self.zoom_step_distance_ratio <= 0.0:
            raise ValueError("zoom_step_distance_ratio must be greater than zero")
        if (
            not isinstance(self.zoom_max_steps_per_frame, int)
            or isinstance(self.zoom_max_steps_per_frame, bool)
            or self.zoom_max_steps_per_frame < 1
        ):
            raise ValueError("zoom_max_steps_per_frame must be at least one")
        if not (
            0.0
            <= self.scroll_extension_release_ratio
            < self.scroll_extension_activation_ratio
        ):
            raise ValueError(
                "scroll extension ratios must satisfy 0 <= release < activation"
            )
        if not (
            0.0
            <= self.scroll_folded_activation_ratio
            < self.scroll_folded_release_ratio
        ):
            raise ValueError(
                "scroll folded ratios must satisfy 0 <= activation < release"
            )
        if self.scroll_step_distance_ratio <= 0.0:
            raise ValueError("scroll_step_distance_ratio must be greater than zero")
        if (
            not isinstance(self.scroll_max_steps_per_frame, int)
            or isinstance(self.scroll_max_steps_per_frame, bool)
            or self.scroll_max_steps_per_frame < 1
        ):
            raise ValueError("scroll_max_steps_per_frame must be at least one")
        for name in (
            "left_pinch_activation_hold_seconds",
            "left_pinch_release_hold_seconds",
            "left_click_cooldown_seconds",
            "double_click_activation_hold_seconds",
            "double_click_release_hold_seconds",
            "double_click_cooldown_seconds",
            "right_click_activation_hold_seconds",
            "right_click_release_hold_seconds",
            "right_click_cooldown_seconds",
            "fist_activation_hold_seconds",
            "fist_release_hold_seconds",
            "drag_activation_hold_seconds",
            "pause_activation_hold_seconds",
            "pause_release_hold_seconds",
            "zoom_activation_hold_seconds",
            "zoom_release_hold_seconds",
            "scroll_activation_hold_seconds",
            "scroll_release_hold_seconds",
            "post_click_cursor_resume_delay_seconds",
        ):
            if getattr(self, name) < 0.0:
                raise ValueError(f"{name} must be zero or greater")
