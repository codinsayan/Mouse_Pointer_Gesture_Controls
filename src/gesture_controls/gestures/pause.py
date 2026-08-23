"""Temporally validated open-palm pause recognition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .features import PinchFeatures
from .left_pinch import TIME_EPSILON_SECONDS


class PauseState(str, Enum):
    INACTIVE = "inactive"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RELEASING = "releasing"


class PauseTransition(str, Enum):
    NONE = "none"
    ACTIVATED = "activated"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class PauseUpdate:
    state: PauseState
    transition: PauseTransition = PauseTransition.NONE
    minimum_extension_ratio: float = 0.0

    @property
    def claims_frame(self) -> bool:
        return self.state is not PauseState.INACTIVE or (
            self.transition is PauseTransition.RELEASED
        )


class OpenPalmPauseRecognizer:
    """Recognize all four non-thumb fingers extended with hysteresis and holds."""

    def __init__(self, activation: float, release: float, hold: float, release_hold: float) -> None:
        if not 0.0 <= release < activation:
            raise ValueError("pause extension release must be below activation")
        if hold < 0.0 or release_hold < 0.0:
            raise ValueError("pause hold times must be zero or greater")
        self._activation = activation
        self._release = release
        self._hold = hold
        self._release_hold = release_hold
        self._state = PauseState.INACTIVE
        self._state_since = 0.0
        self._last_timestamp: float | None = None

    @staticmethod
    def _minimum_extension(features: PinchFeatures) -> float:
        return min(
            features.index_extension_ratio,
            features.middle_extension_ratio,
            features.ring_extension_ratio,
            features.little_extension_ratio,
        )

    def update(self, features: PinchFeatures, timestamp_seconds: float) -> PauseUpdate:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds
        extension = self._minimum_extension(features)
        entry = extension >= self._activation
        retain = extension >= self._release

        if self._state is PauseState.INACTIVE:
            if entry:
                self._state = PauseState.CANDIDATE
                self._state_since = timestamp_seconds
            return PauseUpdate(self._state, minimum_extension_ratio=extension)

        elapsed = timestamp_seconds - self._state_since + TIME_EPSILON_SECONDS
        if self._state is PauseState.CANDIDATE:
            if not entry:
                self._state = PauseState.INACTIVE
            elif elapsed >= self._hold:
                self._state = PauseState.ACTIVE
                return PauseUpdate(self._state, PauseTransition.ACTIVATED, extension)
            return PauseUpdate(self._state, minimum_extension_ratio=extension)

        if self._state is PauseState.ACTIVE:
            if not retain:
                self._state = PauseState.RELEASING
                self._state_since = timestamp_seconds
            return PauseUpdate(self._state, minimum_extension_ratio=extension)

        if retain:
            self._state = PauseState.ACTIVE
        elif elapsed >= self._release_hold:
            self._state = PauseState.INACTIVE
            return PauseUpdate(self._state, PauseTransition.RELEASED, extension)
        return PauseUpdate(self._state, minimum_extension_ratio=extension)

    def reset(self) -> None:
        self._state = PauseState.INACTIVE
        self._state_since = 0.0
        self._last_timestamp = None
