"""Deterministic enablement and fail-safe output gating."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .cursor import Point2D
from .mouse import MouseController


class ControlState(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"


@dataclass(frozen=True, slots=True)
class ControlStatus:
    state: ControlState
    reason: str
    controller_name: str
    real_output: bool


class InputSafetyController:
    """Own output enablement and release held inputs on every unsafe transition."""

    def __init__(self, controller: MouseController) -> None:
        self._controller = controller
        self._state = ControlState.DISABLED
        self._tracking_available = False
        self._reason = "Startup safety: explicitly enable control"

    @property
    def enabled(self) -> bool:
        return self._state is ControlState.ENABLED

    @property
    def tracking_available(self) -> bool:
        return self._tracking_available

    @property
    def status(self) -> ControlStatus:
        return ControlStatus(
            self._state,
            self._reason,
            self._controller.name,
            self._controller.real_output,
        )

    def toggle(self) -> bool:
        if self.enabled:
            self.pause("Control explicitly disabled")
            return False
        self._state = ControlState.ENABLED
        self._reason = (
            "Control enabled: hand tracking active"
            if self._tracking_available
            else "Control enabled: waiting for accepted hand"
        )
        return True

    def set_tracking_available(
        self, available: bool, reason: str = "Control enabled: waiting for accepted hand"
    ) -> None:
        """Gate output without changing the user's enabled/disabled choice."""
        was_available = self._tracking_available
        self._tracking_available = available
        if not self.enabled:
            return
        if available:
            self._reason = "Control enabled: hand tracking active"
        elif was_available:
            self._reason = self._release_safely(reason)
        else:
            self._reason = reason

    def pause(self, reason: str = "Paused by user") -> None:
        reason = self._release_safely(reason)
        self._state = ControlState.DISABLED
        self._reason = reason

    def emergency_pause(self, reason: str = "Emergency pause requested") -> None:
        reason = self._release_safely(reason)
        self._state = ControlState.DISABLED
        self._reason = reason

    def shutdown(self) -> None:
        reason = self._release_safely("Application shutdown")
        self._state = ControlState.DISABLED
        self._reason = reason

    def move_to(self, point: Point2D) -> bool:
        return self._emit(lambda: self._controller.move_to(point), "Cursor output failed")

    def click_left(self) -> bool:
        return self._emit(self._controller.click_left, "Left click output failed")

    def click_left_twice(self) -> bool:
        return self._emit(
            self._controller.click_left_twice, "Double click output failed"
        )

    def click_right(self) -> bool:
        return self._emit(self._controller.click_right, "Right click output failed")

    def scroll_vertical(self, steps: int) -> bool:
        if not steps:
            return False
        return self._emit(
            lambda: self._controller.scroll_vertical(steps),
            "Vertical scroll output failed",
        )

    def scroll_horizontal(self, steps: int) -> bool:
        if not steps:
            return False
        return self._emit(
            lambda: self._controller.scroll_horizontal(steps),
            "Horizontal scroll output failed",
        )

    def begin_drag(self) -> bool:
        return self._emit(self._controller.begin_drag, "Drag start output failed")

    def end_drag(self) -> bool:
        return self._emit(self._controller.end_drag, "Drag release output failed")

    def _emit(self, operation: Callable[[], None], failure_reason: str) -> bool:
        if not self.enabled or not self._tracking_available:
            return False
        try:
            operation()
            return True
        except Exception as exc:
            detail = f"{failure_reason}: {type(exc).__name__}"
            self.emergency_pause(detail)
            return False

    def _release_safely(self, fallback_reason: str) -> str:
        try:
            self._controller.release_all()
        except Exception as exc:
            return f"{fallback_reason}; release failed: {type(exc).__name__}"
        return fallback_reason
