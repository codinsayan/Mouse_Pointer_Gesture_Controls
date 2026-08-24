"""Cross-component gesture, conflict, and safety scenarios without OS input."""

from gesture_controls.controls import InputSafetyController, RecordingMouseController
from gesture_controls.gestures import (
    ClickGestureCoordinator,
    DragRecognizer,
    FistRecognizer,
    GestureAction,
    GestureCoordinator,
    PinchFeatures,
    PinchRecognizer,
    ScrollRecognizer,
)


def features(
    *,
    left: float = 0.8,
    double: float = 0.8,
    right: float = 0.8,
    index: float = 0.25,
    middle: float = 0.05,
    ring: float = 0.05,
    little: float = 0.05,
    x: float = 0.5,
    y: float = 0.5,
) -> PinchFeatures:
    return PinchFeatures(
        left,
        double,
        right,
        1.0,
        index,
        middle,
        ring,
        little,
        y,
        x,
    )


def coordinator() -> GestureCoordinator:
    pinch = lambda: PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06)
    return GestureCoordinator(
        ScrollRecognizer(
            0.18,
            0.10,
            0.10,
            0.18,
            0.06,
            0.05,
            0.08,
            3,
            True,
            3,
        ),
        ClickGestureCoordinator(pinch(), pinch(), pinch()),
        FistRecognizer(0.10, 0.18, 0.06, 0.05),
        DragRecognizer(0.25),
    )


def dispatch(update, safety: InputSafetyController) -> None:
    if update.action is GestureAction.LEFT_CLICK:
        safety.click_left()
    elif update.action is GestureAction.DOUBLE_CLICK:
        safety.click_left_twice()
    elif update.action is GestureAction.RIGHT_CLICK:
        safety.click_right()
    elif update.action is GestureAction.DRAG_STARTED:
        safety.begin_drag()
    elif update.action is GestureAction.DRAG_ENDED:
        safety.end_drag()
    safety.scroll_vertical(update.scroll.steps)
    safety.scroll_horizontal(update.scroll.horizontal_steps)


def enabled_safety() -> tuple[InputSafetyController, RecordingMouseController]:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    assert safety.toggle()
    return safety, fake


def test_right_click_conflict_dispatches_only_right_click() -> None:
    gestures = coordinator()
    safety, fake = enabled_safety()
    competing = features(left=0.2, double=0.2, right=0.2)

    dispatch(gestures.update(competing, 0.0), safety)
    update = gestures.update(competing, 0.03)
    dispatch(update, safety)

    assert update.action is GestureAction.RIGHT_CLICK
    assert fake.actions == [("right_click", None)]


def test_scroll_owns_frame_and_cannot_leak_a_click() -> None:
    gestures = coordinator()
    safety, fake = enabled_safety()
    pose = features(left=0.2, index=0.25, middle=0.25, ring=0.05, little=0.05)

    dispatch(gestures.update(pose, 0.0), safety)
    dispatch(gestures.update(pose, 0.06), safety)
    moved = features(
        left=0.2,
        index=0.25,
        middle=0.25,
        ring=0.05,
        little=0.05,
        y=0.30,
    )
    update = gestures.update(moved, 0.07)
    dispatch(update, safety)

    assert update.scroll.steps == 6
    assert fake.actions == [("vertical_scroll", 6)]


def test_tracking_loss_releases_a_scenario_started_drag() -> None:
    gestures = coordinator()
    safety, fake = enabled_safety()
    fist = features(index=0.05, middle=0.05, ring=0.05, little=0.05)

    dispatch(gestures.update(fist, 0.0), safety)
    dispatch(gestures.update(fist, 0.06), safety)
    started = gestures.update(fist, 0.31)
    dispatch(started, safety)
    safety.set_tracking_available(False, "scenario hand loss")

    assert started.action is GestureAction.DRAG_STARTED
    assert fake.actions == [
        ("drag_down", None),
        ("drag_up", None),
        ("release_all", None),
    ]
    assert not fake.dragging


def test_former_thumb_ring_pose_has_no_assigned_action() -> None:
    gestures = coordinator()
    safety, fake = enabled_safety()
    former_zoom_pose = features(index=0.25, middle=0.25, ring=0.05, little=0.25)
    update = gestures.update(former_zoom_pose, 0.0)
    dispatch(update, safety)

    assert update.action is GestureAction.NONE
    assert not update.cursor_should_freeze
    assert fake.actions == []


def test_open_hand_no_longer_pauses_or_claims_the_frame() -> None:
    gestures = coordinator()
    safety, fake = enabled_safety()
    open_hand = features(index=0.25, middle=0.25, ring=0.25, little=0.25)

    first = gestures.update(open_hand, 0.0)
    held = gestures.update(open_hand, 1.0)
    dispatch(first, safety)
    dispatch(held, safety)

    assert first.action is GestureAction.NONE
    assert held.action is GestureAction.NONE
    assert not held.cursor_should_freeze
    assert safety.enabled
    assert fake.actions == []
