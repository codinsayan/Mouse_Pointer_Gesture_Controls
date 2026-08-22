"""Coordinate click recognition with cursor freeze and resume timing."""

from __future__ import annotations

from dataclasses import dataclass

from .left_pinch import GestureTransition, PinchUpdate, TIME_EPSILON_SECONDS


@dataclass(frozen=True, slots=True)
class CursorGuardDecision:
    freeze: bool
    resume_smoothing: bool


class ClickCursorGuard:
    def __init__(self, resume_delay_seconds: float) -> None:
        if resume_delay_seconds < 0.0:
            raise ValueError("resume_delay_seconds must be zero or greater")
        self._resume_delay = resume_delay_seconds
        self._resume_at = 0.0
        self._was_frozen = False
        self._last_timestamp: float | None = None

    def update(
        self, pinch: PinchUpdate, timestamp_seconds: float
    ) -> CursorGuardDecision:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds
        if pinch.transition is GestureTransition.RELEASED:
            self._resume_at = timestamp_seconds + self._resume_delay
        freeze = (
            pinch.cursor_should_freeze
            or timestamp_seconds + TIME_EPSILON_SECONDS < self._resume_at
        )
        resume_smoothing = self._was_frozen and not freeze
        self._was_frozen = freeze
        return CursorGuardDecision(freeze, resume_smoothing)

    def reset(self) -> None:
        self._resume_at = 0.0
        self._was_frozen = False
        self._last_timestamp = None
