"""Top-level deterministic conflict resolution between gesture families."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .clicks import ClickAction, ClickGestureCoordinator, ClickGestureUpdate
from .drag import DragAction, DragRecognizer, DragState, DragUpdate
from .features import PinchFeatures
from .fist import FistRecognizer, FistState, FistUpdate
from .pause import OpenPalmPauseRecognizer, PauseState, PauseTransition, PauseUpdate
from .scroll import ScrollRecognizer, ScrollState, ScrollUpdate
from .zoom import ZoomRecognizer, ZoomState, ZoomUpdate


class GestureAction(str, Enum):
    NONE = "none"
    LEFT_CLICK = "left_click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG_STARTED = "drag_started"
    DRAG_ENDED = "drag_ended"
    PAUSE_REQUESTED = "pause_requested"


@dataclass(frozen=True, slots=True)
class InteractionUpdate:
    scroll: ScrollUpdate
    click: ClickGestureUpdate | None
    drag: DragUpdate
    fist: FistUpdate
    zoom: ZoomUpdate
    action: GestureAction = GestureAction.NONE
    pause: PauseUpdate = PauseUpdate(PauseState.INACTIVE)

    @property
    def cursor_should_freeze(self) -> bool:
        if self.pause.claims_frame:
            return True
        if self.scroll.claims_frame:
            return True
        if self.drag.state is DragState.DRAGGING:
            return False
        if self.fist.claims_frame:
            return True
        if self.zoom.claims_frame:
            return True
        return self.click is not None and self.click.selected.cursor_should_freeze


class GestureCoordinator:
    """Give scrolling exclusive ownership before evaluating click pinches."""

    def __init__(
        self,
        scroll: ScrollRecognizer,
        clicks: ClickGestureCoordinator,
        fist: FistRecognizer,
        drag: DragRecognizer,
        zoom: ZoomRecognizer,
        pause: OpenPalmPauseRecognizer | None = None,
    ) -> None:
        self._scroll = scroll
        self._clicks = clicks
        self._fist = fist
        self._drag = drag
        self._zoom = zoom
        self._pause = pause

    @staticmethod
    def _drag_action(action: DragAction) -> GestureAction:
        return {
            DragAction.NONE: GestureAction.NONE,
            DragAction.STARTED: GestureAction.DRAG_STARTED,
            DragAction.ENDED: GestureAction.DRAG_ENDED,
        }[action]

    def update(
        self, features: PinchFeatures, timestamp_seconds: float
    ) -> InteractionUpdate:
        pause = (
            self._pause.update(features, timestamp_seconds)
            if self._pause is not None
            else PauseUpdate(PauseState.INACTIVE)
        )
        if pause.claims_frame:
            self._scroll.reset()
            self._clicks.reset(timestamp_seconds)
            self._fist.reset()
            self._zoom.reset()
            drag = self._drag.reset(timestamp_seconds)
            action = (
                GestureAction.PAUSE_REQUESTED
                if pause.transition is PauseTransition.ACTIVATED
                else self._drag_action(drag.action)
            )
            return InteractionUpdate(
                ScrollUpdate(ScrollState.INACTIVE),
                None,
                drag,
                FistUpdate(FistState.INACTIVE),
                ZoomUpdate(ZoomState.INACTIVE),
                action,
                pause,
            )
        scroll = self._scroll.update(features, timestamp_seconds)
        if scroll.claims_frame:
            self._clicks.reset(timestamp_seconds)
            self._fist.reset()
            self._zoom.reset()
            drag = self._drag.reset(timestamp_seconds)
            return InteractionUpdate(
                scroll,
                None,
                drag,
                FistUpdate(FistState.INACTIVE),
                ZoomUpdate(ZoomState.INACTIVE),
                self._drag_action(drag.action),
            )
        fist = self._fist.update(features, timestamp_seconds)
        if fist.claims_frame:
            self._clicks.reset(timestamp_seconds)
            self._zoom.reset()
            drag = self._drag.update(fist, timestamp_seconds)
            return InteractionUpdate(
                scroll,
                None,
                drag,
                fist,
                ZoomUpdate(ZoomState.INACTIVE),
                self._drag_action(drag.action),
            )
        zoom = self._zoom.update(features, timestamp_seconds)
        if zoom.claims_frame:
            self._clicks.reset(timestamp_seconds)
            drag = self._drag.update(fist, timestamp_seconds)
            return InteractionUpdate(
                scroll, None, drag, fist, zoom, self._drag_action(drag.action)
            )
        click = self._clicks.update(
            features.left_pinch_ratio,
            features.double_click_pinch_ratio,
            features.right_pinch_ratio,
            timestamp_seconds,
        )
        drag = self._drag.update(fist, timestamp_seconds)
        action = {
            ClickAction.NONE: GestureAction.NONE,
            ClickAction.LEFT_CLICK: GestureAction.LEFT_CLICK,
            ClickAction.DOUBLE_CLICK: GestureAction.DOUBLE_CLICK,
            ClickAction.RIGHT_CLICK: GestureAction.RIGHT_CLICK,
        }[click.action]
        return InteractionUpdate(scroll, click, drag, fist, zoom, action)

    def reset(self, timestamp_seconds: float | None = None) -> GestureAction:
        if self._pause is not None:
            self._pause.reset()
        self._scroll.reset()
        self._fist.reset()
        self._zoom.reset()
        self._clicks.reset(timestamp_seconds)
        return self._drag_action(self._drag.reset(timestamp_seconds).action)
