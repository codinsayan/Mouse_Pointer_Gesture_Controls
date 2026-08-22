"""Resolve mutually exclusive click pinches by explicit priority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .left_pinch import GestureTransition, PinchRecognizer, PinchUpdate


class ClickAction(str, Enum):
    NONE = "none"
    LEFT_CLICK = "left_click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"


@dataclass(frozen=True, slots=True)
class ClickGestureUpdate:
    action: ClickAction
    selected: PinchUpdate
    left: PinchUpdate
    double: PinchUpdate
    right: PinchUpdate


class ClickGestureCoordinator:
    """Resolve click priority as thumb–little, thumb–middle, then thumb–index."""

    def __init__(
        self,
        left: PinchRecognizer,
        double: PinchRecognizer,
        right: PinchRecognizer,
    ) -> None:
        self._left = left
        self._double = double
        self._right = right

    def update(
        self,
        left_ratio: float,
        double_ratio: float,
        right_ratio: float,
        timestamp_seconds: float,
    ) -> ClickGestureUpdate:
        right = self._right.update(right_ratio, timestamp_seconds)
        right_claims_frame = (
            right.cursor_should_freeze
            or right.transition is GestureTransition.RELEASED
        )
        if right_claims_frame:
            self._double.reset(timestamp_seconds)
            self._left.reset(timestamp_seconds)
            left = PinchUpdate(left_ratio, self._left.state)
            double = PinchUpdate(double_ratio, self._double.state)
            action = (
                ClickAction.RIGHT_CLICK
                if right.transition is GestureTransition.ACTIVATED
                else ClickAction.NONE
            )
            return ClickGestureUpdate(action, right, left, double, right)

        double = self._double.update(double_ratio, timestamp_seconds)
        double_claims_frame = (
            double.cursor_should_freeze
            or double.transition is GestureTransition.RELEASED
        )
        if double_claims_frame:
            self._left.reset(timestamp_seconds)
            left = PinchUpdate(left_ratio, self._left.state)
            action = (
                ClickAction.DOUBLE_CLICK
                if double.transition is GestureTransition.ACTIVATED
                else ClickAction.NONE
            )
            return ClickGestureUpdate(action, double, left, double, right)

        left = self._left.update(left_ratio, timestamp_seconds)
        action = (
            ClickAction.LEFT_CLICK
            if left.transition is GestureTransition.ACTIVATED
            else ClickAction.NONE
        )
        return ClickGestureUpdate(action, left, left, double, right)

    def reset(self, timestamp_seconds: float | None = None) -> None:
        self._left.reset(timestamp_seconds)
        self._double.reset(timestamp_seconds)
        self._right.reset(timestamp_seconds)
