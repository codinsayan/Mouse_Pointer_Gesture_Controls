"""Dry-run thumb-ring expansion/contraction zoom recognition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import trunc

from .features import PinchFeatures
from .left_pinch import TIME_EPSILON_SECONDS


class ZoomState(str, Enum):
    INACTIVE = "inactive"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RELEASING = "releasing"


class ZoomTransition(str, Enum):
    NONE = "none"
    ACTIVATED = "activated"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class ZoomUpdate:
    state: ZoomState
    transition: ZoomTransition = ZoomTransition.NONE
    steps: int = 0
    span_ratio: float = 0.0

    @property
    def claims_frame(self) -> bool:
        return self.state is not ZoomState.INACTIVE or (
            self.transition is ZoomTransition.RELEASED
        )


class ZoomRecognizer:
    """Quantize thumb-ring span changes after a distinct folded-hand pose."""

    def __init__(
        self,
        span_activation_ratio: float,
        span_release_ratio: float,
        other_extension_activation_ratio: float,
        other_extension_release_ratio: float,
        activation_hold_seconds: float,
        release_hold_seconds: float,
        step_distance_ratio: float,
        max_steps_per_frame: int,
    ) -> None:
        if not 0.0 < span_activation_ratio < span_release_ratio:
            raise ValueError("zoom span ratios must satisfy 0 < activation < release")
        if not (
            0.0
            <= other_extension_release_ratio
            < other_extension_activation_ratio
        ):
            raise ValueError("zoom other-finger extension release must be below activation")
        if activation_hold_seconds < 0.0 or release_hold_seconds < 0.0:
            raise ValueError("zoom hold times must be zero or greater")
        if step_distance_ratio <= 0.0:
            raise ValueError("zoom step distance must be greater than zero")
        if (
            not isinstance(max_steps_per_frame, int)
            or isinstance(max_steps_per_frame, bool)
            or max_steps_per_frame < 1
        ):
            raise ValueError("max zoom steps per frame must be at least one")
        self._span_activation = span_activation_ratio
        self._span_release = span_release_ratio
        self._other_extension_activation = other_extension_activation_ratio
        self._other_extension_release = other_extension_release_ratio
        self._activation_hold = activation_hold_seconds
        self._release_hold = release_hold_seconds
        self._step_distance = step_distance_ratio
        self._max_steps = max_steps_per_frame
        self._state = ZoomState.INACTIVE
        self._state_since = 0.0
        self._span_anchor = 0.0
        self._last_timestamp: float | None = None

    def _entry_pose(self, features: PinchFeatures) -> bool:
        return (
            features.zoom_span_ratio <= self._span_activation
            and features.index_extension_ratio >= self._other_extension_activation
            and features.middle_extension_ratio >= self._other_extension_activation
            and features.little_extension_ratio >= self._other_extension_activation
        )

    def _keep_pose(self, features: PinchFeatures) -> bool:
        return (
            features.zoom_span_ratio <= self._span_release
            and features.index_extension_ratio >= self._other_extension_release
            and features.middle_extension_ratio >= self._other_extension_release
            and features.little_extension_ratio >= self._other_extension_release
        )

    def _steps(self, span_ratio: float) -> int:
        units = (span_ratio - self._span_anchor) / self._step_distance
        raw_steps = trunc(
            units + TIME_EPSILON_SECONDS
            if units >= 0.0
            else units - TIME_EPSILON_SECONDS
        )
        if raw_steps == 0:
            return 0
        steps = max(-self._max_steps, min(self._max_steps, raw_steps))
        if steps != raw_steps:
            self._span_anchor = span_ratio
        else:
            self._span_anchor += steps * self._step_distance
        return steps

    def update(
        self, features: PinchFeatures, timestamp_seconds: float
    ) -> ZoomUpdate:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds
        span = features.zoom_span_ratio

        if self._state is ZoomState.INACTIVE:
            if self._entry_pose(features):
                self._state = ZoomState.CANDIDATE
                self._state_since = timestamp_seconds
            return ZoomUpdate(self._state, span_ratio=span)

        elapsed = timestamp_seconds - self._state_since + TIME_EPSILON_SECONDS
        if self._state is ZoomState.CANDIDATE:
            if not self._entry_pose(features):
                self._state = ZoomState.INACTIVE
            elif elapsed >= self._activation_hold:
                self._state = ZoomState.ACTIVE
                self._span_anchor = span
                return ZoomUpdate(
                    self._state, ZoomTransition.ACTIVATED, span_ratio=span
                )
            return ZoomUpdate(self._state, span_ratio=span)

        if self._state is ZoomState.ACTIVE:
            if self._keep_pose(features):
                return ZoomUpdate(
                    self._state, steps=self._steps(span), span_ratio=span
                )
            self._state = ZoomState.RELEASING
            self._state_since = timestamp_seconds
            return ZoomUpdate(self._state, span_ratio=span)

        if self._keep_pose(features):
            self._state = ZoomState.ACTIVE
            self._span_anchor = span
            return ZoomUpdate(self._state, span_ratio=span)
        if elapsed >= self._release_hold:
            self._state = ZoomState.INACTIVE
            return ZoomUpdate(
                self._state, ZoomTransition.RELEASED, span_ratio=span
            )
        return ZoomUpdate(self._state, span_ratio=span)

    def reset(self) -> None:
        self._state = ZoomState.INACTIVE
        self._state_since = 0.0
        self._span_anchor = 0.0
        self._last_timestamp = None
