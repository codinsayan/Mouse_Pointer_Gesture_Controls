"""Scale-independent, hysteretic fist-pose recognition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .features import PinchFeatures
from .left_pinch import TIME_EPSILON_SECONDS


class FistState(str, Enum):
    INACTIVE = "inactive"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RELEASING = "releasing"


class FistTransition(str, Enum):
    NONE = "none"
    ACTIVATED = "activated"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class FistUpdate:
    state: FistState
    transition: FistTransition = FistTransition.NONE
    maximum_extension_ratio: float = 0.0

    @property
    def claims_frame(self) -> bool:
        return self.state is not FistState.INACTIVE or (
            self.transition is FistTransition.RELEASED
        )


class FistRecognizer:
    """Require all four non-thumb fingers to remain folded over time."""

    def __init__(
        self,
        activation_ratio: float,
        release_ratio: float,
        activation_hold_seconds: float,
        release_hold_seconds: float,
    ) -> None:
        if not 0.0 <= activation_ratio < release_ratio:
            raise ValueError("fist ratios must satisfy 0 <= activation < release")
        if activation_hold_seconds < 0.0 or release_hold_seconds < 0.0:
            raise ValueError("fist hold times must be zero or greater")
        self._activation_ratio = activation_ratio
        self._release_ratio = release_ratio
        self._activation_hold = activation_hold_seconds
        self._release_hold = release_hold_seconds
        self._state = FistState.INACTIVE
        self._state_since = 0.0
        self._last_timestamp: float | None = None

    @staticmethod
    def _maximum_extension(features: PinchFeatures) -> float:
        return max(
            features.index_extension_ratio,
            features.middle_extension_ratio,
            features.ring_extension_ratio,
            features.little_extension_ratio,
        )

    def update(self, features: PinchFeatures, timestamp_seconds: float) -> FistUpdate:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds
        maximum = self._maximum_extension(features)
        folded = maximum <= self._activation_ratio
        retained = maximum <= self._release_ratio

        if self._state is FistState.INACTIVE:
            if folded:
                self._state = FistState.CANDIDATE
                self._state_since = timestamp_seconds
            return FistUpdate(self._state, maximum_extension_ratio=maximum)

        elapsed = timestamp_seconds - self._state_since + TIME_EPSILON_SECONDS
        if self._state is FistState.CANDIDATE:
            if not folded:
                self._state = FistState.INACTIVE
            elif elapsed >= self._activation_hold:
                self._state = FistState.ACTIVE
                return FistUpdate(self._state, FistTransition.ACTIVATED, maximum)
            return FistUpdate(self._state, maximum_extension_ratio=maximum)

        if self._state is FistState.ACTIVE:
            if retained:
                return FistUpdate(self._state, maximum_extension_ratio=maximum)
            self._state = FistState.RELEASING
            self._state_since = timestamp_seconds
            return FistUpdate(self._state, maximum_extension_ratio=maximum)

        if retained:
            self._state = FistState.ACTIVE
            return FistUpdate(self._state, maximum_extension_ratio=maximum)
        if elapsed >= self._release_hold:
            self._state = FistState.INACTIVE
            return FistUpdate(self._state, FistTransition.RELEASED, maximum)
        return FistUpdate(self._state, maximum_extension_ratio=maximum)

    def reset(self) -> None:
        self._state = FistState.INACTIVE
        self._state_since = 0.0
        self._last_timestamp = None
