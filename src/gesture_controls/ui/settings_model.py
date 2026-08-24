"""Deterministic presentation model for the Iteration 9 settings dashboard."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from gesture_controls.config import AppConfig, load_config, save_config

POINTER_SPEED_MIN = 1
POINTER_SPEED_MAX = 10
POINTER_SMOOTHING_SLOW_SECONDS = 0.20
POINTER_SMOOTHING_STEP_SECONDS = 0.02
SCROLL_SPEED_MIN = 1
SCROLL_SPEED_MAX = 20
SENSITIVITY_MIN = 0.1
SENSITIVITY_MAX = 3.0


def pointer_speed_to_smoothing(pointer_speed: int) -> float:
    if (
        not isinstance(pointer_speed, int)
        or isinstance(pointer_speed, bool)
        or not POINTER_SPEED_MIN <= pointer_speed <= POINTER_SPEED_MAX
    ):
        raise ValueError("pointer speed must be an integer within 1..10")
    return round(
        POINTER_SMOOTHING_SLOW_SECONDS
        - (pointer_speed - POINTER_SPEED_MIN) * POINTER_SMOOTHING_STEP_SECONDS,
        3,
    )


def smoothing_to_pointer_speed(smoothing_seconds: float) -> int:
    if smoothing_seconds <= 0.0:
        raise ValueError("smoothing seconds must be greater than zero")
    raw = round(
        (POINTER_SMOOTHING_SLOW_SECONDS - smoothing_seconds)
        / POINTER_SMOOTHING_STEP_SECONDS
        + POINTER_SPEED_MIN
    )
    return min(POINTER_SPEED_MAX, max(POINTER_SPEED_MIN, raw))


@dataclass(frozen=True, slots=True)
class DashboardSettings:
    pointer_speed: int
    scroll_speed: int
    sensitivity: float
    dominant_hand: str

    @classmethod
    def from_config(cls, config: AppConfig) -> "DashboardSettings":
        return cls(
            smoothing_to_pointer_speed(config.cursor_smoothing_seconds),
            config.scroll_output_multiplier,
            config.cursor_sensitivity,
            config.dominant_hand,
        )

    def apply(self, base: AppConfig) -> AppConfig:
        if (
            not isinstance(self.scroll_speed, int)
            or isinstance(self.scroll_speed, bool)
            or not SCROLL_SPEED_MIN <= self.scroll_speed <= SCROLL_SPEED_MAX
        ):
            raise ValueError("scroll speed must be an integer within 1..20")
        if not SENSITIVITY_MIN <= self.sensitivity <= SENSITIVITY_MAX:
            raise ValueError("sensitivity must be within 0.1..3.0")
        if self.dominant_hand not in {"any", "left", "right"}:
            raise ValueError("dominant hand must be any, left, or right")
        return replace(
            base,
            cursor_smoothing_seconds=pointer_speed_to_smoothing(
                self.pointer_speed
            ),
            scroll_output_multiplier=self.scroll_speed,
            cursor_sensitivity=round(float(self.sensitivity), 2),
            dominant_hand=self.dominant_hand,
        )


def load_dashboard_profile(path: Path) -> tuple[AppConfig, bool]:
    """Load an existing profile, or return defaults without writing a new file."""
    if path.is_file():
        return load_config(path), True
    return AppConfig(), False


def save_dashboard_profile(
    path: Path, base: AppConfig, settings: DashboardSettings
) -> AppConfig:
    updated = settings.apply(base)
    save_config(path, updated)
    return updated
