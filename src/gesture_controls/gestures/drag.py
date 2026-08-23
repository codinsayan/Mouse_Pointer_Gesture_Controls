"""Long-hold state machine for the dry-run fist drag gesture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .fist import FistState, FistTransition, FistUpdate
from .left_pinch import TIME_EPSILON_SECONDS


class DragState(str, Enum):
    IDLE = "idle"
    ARMED = "armed"
    DRAGGING = "dragging"


class DragAction(str, Enum):
    NONE = "none"
    STARTED = "started"
    ENDED = "ended"


@dataclass(frozen=True, slots=True)
class DragUpdate:
    state: DragState
    action: DragAction = DragAction.NONE


class DragRecognizer:
    def __init__(self, activation_hold_seconds: float) -> None:
        if activation_hold_seconds < 0.0:
            raise ValueError("drag activation hold must be zero or greater")
        self._activation_hold = activation_hold_seconds
        self._state = DragState.IDLE
        self._armed_since = 0.0
        self._last_timestamp: float | None = None

    @property
    def state(self) -> DragState:
        return self._state

    def update(self, fist: FistUpdate, timestamp_seconds: float) -> DragUpdate:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds

        if self._state is DragState.IDLE:
            if fist.transition is FistTransition.ACTIVATED:
                self._state = DragState.ARMED
                self._armed_since = timestamp_seconds
            return DragUpdate(self._state)

        if self._state is DragState.ARMED:
            if (
                fist.transition is FistTransition.RELEASED
                or fist.state is not FistState.ACTIVE
            ):
                self._state = DragState.IDLE
                return DragUpdate(self._state)
            if (
                timestamp_seconds - self._armed_since + TIME_EPSILON_SECONDS
                >= self._activation_hold
            ):
                self._state = DragState.DRAGGING
                return DragUpdate(self._state, DragAction.STARTED)
            return DragUpdate(self._state)

        if (
            fist.transition is FistTransition.RELEASED
            or fist.state is not FistState.ACTIVE
        ):
            self._state = DragState.IDLE
            return DragUpdate(self._state, DragAction.ENDED)
        return DragUpdate(self._state)

    def reset(self, timestamp_seconds: float | None = None) -> DragUpdate:
        if (
            timestamp_seconds is not None
            and self._last_timestamp is not None
            and timestamp_seconds < self._last_timestamp
        ):
            raise ValueError("timestamps must be monotonic")
        action = (
            DragAction.ENDED
            if self._state is DragState.DRAGGING
            else DragAction.NONE
        )
        self._state = DragState.IDLE
        self._armed_since = 0.0
        self._last_timestamp = timestamp_seconds
        return DragUpdate(self._state, action)
