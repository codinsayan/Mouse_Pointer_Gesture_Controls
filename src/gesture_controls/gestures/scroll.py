"""Deterministic two-finger scroll recognition and displacement quantization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import trunc

from .features import PinchFeatures
from .left_pinch import TIME_EPSILON_SECONDS


class ScrollState(str, Enum):
    INACTIVE = "inactive"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RELEASING = "releasing"


class ScrollTransition(str, Enum):
    NONE = "none"
    ACTIVATED = "activated"
    RELEASED = "released"


class ScrollAxis(str, Enum):
    NONE = "none"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


@dataclass(frozen=True, slots=True)
class ScrollUpdate:
    state: ScrollState
    transition: ScrollTransition = ScrollTransition.NONE
    steps: int = 0
    horizontal_steps: int = 0
    axis: ScrollAxis = ScrollAxis.NONE

    @property
    def claims_frame(self) -> bool:
        return self.state is not ScrollState.INACTIVE or (
            self.transition is ScrollTransition.RELEASED
        )


class ScrollRecognizer:
    """Recognize two-axis scroll strokes with return-motion clutching."""

    def __init__(
        self,
        extension_activation_ratio: float,
        extension_release_ratio: float,
        folded_activation_ratio: float,
        folded_release_ratio: float,
        activation_hold_seconds: float,
        release_hold_seconds: float,
        step_distance_ratio: float,
        max_steps_per_frame: int,
        direction_lock_enabled: bool = True,
        output_multiplier: int = 1,
    ) -> None:
        if not 0.0 <= extension_release_ratio < extension_activation_ratio:
            raise ValueError("extension release ratio must be below activation")
        if not 0.0 <= folded_activation_ratio < folded_release_ratio:
            raise ValueError("folded activation ratio must be below release")
        if activation_hold_seconds < 0.0 or release_hold_seconds < 0.0:
            raise ValueError("scroll hold times must be zero or greater")
        if step_distance_ratio <= 0.0:
            raise ValueError("scroll step distance must be greater than zero")
        if (
            not isinstance(max_steps_per_frame, int)
            or isinstance(max_steps_per_frame, bool)
            or max_steps_per_frame < 1
        ):
            raise ValueError("max scroll steps per frame must be at least one")
        if not isinstance(direction_lock_enabled, bool):
            raise ValueError("scroll direction lock setting must be a boolean")
        if (
            not isinstance(output_multiplier, int)
            or isinstance(output_multiplier, bool)
            or not 1 <= output_multiplier <= 20
        ):
            raise ValueError("scroll output multiplier must be within 1..20")
        self._extension_activation = extension_activation_ratio
        self._extension_release = extension_release_ratio
        self._folded_activation = folded_activation_ratio
        self._folded_release = folded_release_ratio
        self._activation_hold = activation_hold_seconds
        self._release_hold = release_hold_seconds
        self._step_distance = step_distance_ratio
        self._max_steps = max_steps_per_frame
        self._direction_lock_enabled = direction_lock_enabled
        self._output_multiplier = output_multiplier
        self._state = ScrollState.INACTIVE
        self._state_since = 0.0
        self._anchor_x = 0.0
        self._anchor_y = 0.0
        self._axis = ScrollAxis.NONE
        self._locked_direction = 0
        self._last_timestamp: float | None = None

    @property
    def state(self) -> ScrollState:
        return self._state

    def _entry_axis(self, features: PinchFeatures) -> ScrollAxis:
        vertical = (
            features.index_extension_ratio >= self._extension_activation
            and features.middle_extension_ratio >= self._extension_activation
            and features.ring_extension_ratio <= self._folded_activation
            and features.little_extension_ratio <= self._folded_activation
        )
        if vertical:
            return ScrollAxis.VERTICAL
        horizontal = (
            features.index_extension_ratio <= self._folded_activation
            and features.middle_extension_ratio >= self._extension_activation
            and features.ring_extension_ratio >= self._extension_activation
            and features.little_extension_ratio <= self._folded_activation
        )
        return ScrollAxis.HORIZONTAL if horizontal else ScrollAxis.NONE

    def _keep_pose(self, features: PinchFeatures) -> bool:
        if self._axis is ScrollAxis.VERTICAL:
            return (
                features.index_extension_ratio >= self._extension_release
                and features.middle_extension_ratio >= self._extension_release
                and features.ring_extension_ratio <= self._folded_release
                and features.little_extension_ratio <= self._folded_release
            )
        if self._axis is ScrollAxis.HORIZONTAL:
            return (
                features.index_extension_ratio <= self._folded_release
                and features.middle_extension_ratio >= self._extension_release
                and features.ring_extension_ratio >= self._extension_release
                and features.little_extension_ratio <= self._folded_release
            )
        return False

    def _elapsed(self, timestamp_seconds: float) -> float:
        return timestamp_seconds - self._state_since + TIME_EPSILON_SECONDS

    def _bounded_steps(self, raw_steps: int) -> int:
        return max(-self._max_steps, min(self._max_steps, raw_steps))

    def _scroll_steps(self, features: PinchFeatures) -> tuple[int, int]:
        horizontal_displacement = (
            features.palm_anchor_x - self._anchor_x
        ) / features.hand_size
        vertical_displacement = (
            self._anchor_y - features.palm_anchor_y
        ) / features.hand_size
        displacement = (
            horizontal_displacement
            if self._axis is ScrollAxis.HORIZONTAL
            else vertical_displacement
        )
        raw_steps = trunc(displacement / self._step_distance)
        if raw_steps == 0:
            return 0, 0
        direction = 1 if raw_steps > 0 else -1
        if self._direction_lock_enabled:
            if self._locked_direction == 0:
                self._locked_direction = direction
            elif direction != self._locked_direction:
                self._anchor_x = features.palm_anchor_x
                self._anchor_y = features.palm_anchor_y
                return 0, 0
        steps = self._bounded_steps(raw_steps)
        if steps != raw_steps:
            if self._axis is ScrollAxis.HORIZONTAL:
                self._anchor_x = features.palm_anchor_x
            else:
                self._anchor_y = features.palm_anchor_y
        elif self._axis is ScrollAxis.HORIZONTAL:
            self._anchor_x += steps * self._step_distance * features.hand_size
        else:
            self._anchor_y -= steps * self._step_distance * features.hand_size
        if self._axis is ScrollAxis.HORIZONTAL:
            return 0, steps * self._output_multiplier
        return steps * self._output_multiplier, 0

    def update(
        self, features: PinchFeatures, timestamp_seconds: float
    ) -> ScrollUpdate:
        if self._last_timestamp is not None and timestamp_seconds < self._last_timestamp:
            raise ValueError("timestamps must be monotonic")
        self._last_timestamp = timestamp_seconds

        if self._state is ScrollState.INACTIVE:
            entry_axis = self._entry_axis(features)
            if entry_axis is not ScrollAxis.NONE:
                self._state = ScrollState.CANDIDATE
                self._state_since = timestamp_seconds
                self._axis = entry_axis
                self._locked_direction = 0
            return ScrollUpdate(self._state, axis=self._axis)

        if self._state is ScrollState.CANDIDATE:
            entry_axis = self._entry_axis(features)
            if entry_axis is ScrollAxis.NONE:
                self._state = ScrollState.INACTIVE
                self._axis = ScrollAxis.NONE
                self._locked_direction = 0
            elif entry_axis is not self._axis:
                self._axis = entry_axis
                self._state_since = timestamp_seconds
                self._locked_direction = 0
            elif self._elapsed(timestamp_seconds) >= self._activation_hold:
                self._state = ScrollState.ACTIVE
                self._anchor_x = features.palm_anchor_x
                self._anchor_y = features.palm_anchor_y
                self._locked_direction = 0
                return ScrollUpdate(
                    self._state, ScrollTransition.ACTIVATED, axis=self._axis
                )
            return ScrollUpdate(self._state, axis=self._axis)

        if self._state is ScrollState.ACTIVE:
            if self._keep_pose(features):
                vertical, horizontal = self._scroll_steps(features)
                return ScrollUpdate(
                    self._state,
                    steps=vertical,
                    horizontal_steps=horizontal,
                    axis=self._axis,
                )
            self._state = ScrollState.RELEASING
            self._state_since = timestamp_seconds
            return ScrollUpdate(self._state, axis=self._axis)

        if self._keep_pose(features):
            self._state = ScrollState.ACTIVE
            self._anchor_x = features.palm_anchor_x
            self._anchor_y = features.palm_anchor_y
            return ScrollUpdate(self._state, axis=self._axis)
        if self._elapsed(timestamp_seconds) >= self._release_hold:
            self._state = ScrollState.INACTIVE
            self._axis = ScrollAxis.NONE
            self._locked_direction = 0
            return ScrollUpdate(self._state, ScrollTransition.RELEASED)
        return ScrollUpdate(self._state, axis=self._axis)

    def reset(self) -> None:
        self._state = ScrollState.INACTIVE
        self._state_since = 0.0
        self._anchor_x = 0.0
        self._anchor_y = 0.0
        self._axis = ScrollAxis.NONE
        self._locked_direction = 0
        self._last_timestamp = None
