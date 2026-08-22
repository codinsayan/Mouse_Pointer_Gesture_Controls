"""Temporal hysteresis recognizer for a dry-run left pinch."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

TIME_EPSILON_SECONDS = 1e-12


def _elapsed_at_least(now: float, since: float, duration: float) -> bool:
    return now - since + TIME_EPSILON_SECONDS >= duration


class PinchState(str, Enum):
    INACTIVE = "inactive"
    CANDIDATE = "candidate"
    ACTIVE = "active"


class GestureTransition(str, Enum):
    NONE = "none"
    ACTIVATED = "activated"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class PinchUpdate:
    ratio: float
    state: PinchState
    transition: GestureTransition = GestureTransition.NONE

    @property
    def cursor_should_freeze(self) -> bool:
        return self.state in (PinchState.CANDIDATE, PinchState.ACTIVE)


class PinchRecognizer:
    def __init__(
        self,
        activation_threshold: float,
        release_threshold: float,
        activation_hold_seconds: float,
        release_hold_seconds: float,
        cooldown_seconds: float,
    ) -> None:
        if not 0.0 < activation_threshold < release_threshold:
            raise ValueError("thresholds must satisfy 0 < activation < release")
        for name, value in (
            ("activation_hold_seconds", activation_hold_seconds),
            ("release_hold_seconds", release_hold_seconds),
            ("cooldown_seconds", cooldown_seconds),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be zero or greater")
        self._activation_threshold = activation_threshold
        self._release_threshold = release_threshold
        self._activation_hold = activation_hold_seconds
        self._release_hold = release_hold_seconds
        self._cooldown = cooldown_seconds
        self._state = PinchState.INACTIVE
        self._activation_since: float | None = None
        self._release_since: float | None = None
        self._cooldown_until = 0.0
        self._last_timestamp: float | None = None

    @property
    def state(self) -> PinchState:
        return self._state

    def update(self, ratio: float, timestamp_seconds: float) -> PinchUpdate:
        if ratio < 0.0:
            raise ValueError("pinch ratio must be zero or greater")
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds

        if self._state is PinchState.INACTIVE:
            if timestamp_seconds < self._cooldown_until:
                self._activation_since = None
            elif ratio < self._activation_threshold:
                self._state = PinchState.CANDIDATE
                self._activation_since = timestamp_seconds
            else:
                self._activation_since = None
        elif self._state is PinchState.CANDIDATE:
            if ratio < self._activation_threshold:
                assert self._activation_since is not None
                if _elapsed_at_least(
                    timestamp_seconds, self._activation_since, self._activation_hold
                ):
                    self._state = PinchState.ACTIVE
                    self._activation_since = None
                    return PinchUpdate(
                        ratio,
                        self._state,
                        GestureTransition.ACTIVATED,
                    )
            else:
                self._state = PinchState.INACTIVE
                self._activation_since = None
        elif ratio > self._release_threshold:
            if self._release_since is None:
                self._release_since = timestamp_seconds
            if _elapsed_at_least(
                timestamp_seconds, self._release_since, self._release_hold
            ):
                self._state = PinchState.INACTIVE
                self._release_since = None
                self._cooldown_until = timestamp_seconds + self._cooldown
                return PinchUpdate(ratio, self._state, GestureTransition.RELEASED)
        else:
            self._release_since = None

        return PinchUpdate(ratio, self._state)

    def reset(self, timestamp_seconds: float | None = None) -> None:
        if (
            timestamp_seconds is not None
            and self._last_timestamp is not None
            and timestamp_seconds < self._last_timestamp
        ):
            raise ValueError("timestamps must be monotonic")
        self._state = PinchState.INACTIVE
        self._activation_since = None
        self._release_since = None
        if timestamp_seconds is not None:
            self._last_timestamp = timestamp_seconds
            self._cooldown_until = timestamp_seconds + self._cooldown
        else:
            self._last_timestamp = None
            self._cooldown_until = 0.0


LeftPinchRecognizer = PinchRecognizer
