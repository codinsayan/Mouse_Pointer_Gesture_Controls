import pytest

from gesture_controls.gestures import (
    DragAction,
    DragRecognizer,
    DragState,
    FistState,
    FistTransition,
    FistUpdate,
)


def fist(
    state: FistState,
    transition: FistTransition = FistTransition.NONE,
) -> FistUpdate:
    return FistUpdate(state, transition, 0.05)


def arm(item: DragRecognizer, timestamp: float = 0.0) -> None:
    update = item.update(
        fist(FistState.ACTIVE, FistTransition.ACTIVATED), timestamp
    )
    assert update.state is DragState.ARMED


def test_hold_starts_drag_once_at_threshold() -> None:
    item = DragRecognizer(0.25)
    arm(item)
    assert item.update(fist(FistState.ACTIVE), 0.249).action is DragAction.NONE
    started = item.update(fist(FistState.ACTIVE), 0.25)
    assert started.state is DragState.DRAGGING
    assert started.action is DragAction.STARTED
    assert item.update(fist(FistState.ACTIVE), 0.40).action is DragAction.NONE


def test_short_pinch_does_not_start_or_end_drag() -> None:
    item = DragRecognizer(0.25)
    arm(item)
    released = item.update(
        fist(FistState.INACTIVE, FistTransition.RELEASED), 0.20
    )
    assert released.state is DragState.IDLE
    assert released.action is DragAction.NONE


def test_release_and_reset_end_active_drag_once() -> None:
    item = DragRecognizer(0.25)
    arm(item)
    item.update(fist(FistState.ACTIVE), 0.25)
    ended = item.update(
        fist(FistState.INACTIVE, FistTransition.RELEASED), 0.30
    )
    assert ended.action is DragAction.ENDED
    assert item.reset(0.31).action is DragAction.NONE

    arm(item, 0.40)
    item.update(fist(FistState.ACTIVE), 0.65)
    assert item.reset(0.70).action is DragAction.ENDED
    assert item.reset(0.71).action is DragAction.NONE


def test_rejects_negative_hold_and_non_monotonic_time() -> None:
    with pytest.raises(ValueError, match="zero or greater"):
        DragRecognizer(-0.1)
    item = DragRecognizer(0.25)
    arm(item, 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(fist(FistState.ACTIVE), 0.9)
