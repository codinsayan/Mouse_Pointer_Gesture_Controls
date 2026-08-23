"""Top-level deterministic conflict resolution between gesture families."""

from __future__ import annotations

from dataclasses import dataclass

from .clicks import ClickGestureCoordinator, ClickGestureUpdate
from .features import PinchFeatures
from .scroll import ScrollRecognizer, ScrollUpdate


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    scroll: ScrollUpdate
    click: ClickGestureUpdate | None


class GestureCoordinator:
    """Give scrolling exclusive ownership before evaluating click pinches."""

    def __init__(
        self, scroll: ScrollRecognizer, clicks: ClickGestureCoordinator
    ) -> None:
        self._scroll = scroll
        self._clicks = clicks

    def update(
        self, features: PinchFeatures, timestamp_seconds: float
    ) -> InteractionUpdate:
        scroll = self._scroll.update(features, timestamp_seconds)
        if scroll.claims_frame:
            self._clicks.reset(timestamp_seconds)
            return InteractionUpdate(scroll, None)
        click = self._clicks.update(
            features.left_pinch_ratio,
            features.double_click_pinch_ratio,
            features.right_pinch_ratio,
            timestamp_seconds,
        )
        return InteractionUpdate(scroll, click)

    def reset(self, timestamp_seconds: float | None = None) -> None:
        self._scroll.reset()
        self._clicks.reset(timestamp_seconds)
