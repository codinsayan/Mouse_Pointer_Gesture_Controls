"""Resolve left and double-click pinch recognition by explicit priority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .left_pinch import GestureTransition, PinchRecognizer, PinchUpdate


class ClickAction(str, Enum):
    NONE = "none"
    LEFT_CLICK = "left_click"
    DOUBLE_CLICK = "double_click"


@dataclass(frozen=True, slots=True)
class ClickGestureUpdate:
    action: ClickAction
    selected: PinchUpdate
    left: PinchUpdate
    double: PinchUpdate


class ClickGestureCoordinator:
    """Give thumb–middle double click priority over thumb–index left click."""

    def __init__(
        self,
        left: PinchRecognizer,
        double: PinchRecognizer,
    ) -> None:
        self._left = left
        self._double = double

    def update(
        self,
        left_ratio: float,
        double_ratio: float,
        timestamp_seconds: float,
    ) -> ClickGestureUpdate:
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
            return ClickGestureUpdate(action, double, left, double)

        left = self._left.update(left_ratio, timestamp_seconds)
        action = (
            ClickAction.LEFT_CLICK
            if left.transition is GestureTransition.ACTIVATED
            else ClickAction.NONE
        )
        return ClickGestureUpdate(action, left, left, double)

    def reset(self, timestamp_seconds: float | None = None) -> None:
        self._left.reset(timestamp_seconds)
        self._double.reset(timestamp_seconds)
