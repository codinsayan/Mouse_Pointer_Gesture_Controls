from gesture_controls.gestures import (
    ClickAction,
    ClickGestureCoordinator,
    PinchRecognizer,
    PinchState,
)


def coordinator() -> ClickGestureCoordinator:
    return ClickGestureCoordinator(
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
    )


def test_thumb_index_activation_emits_left_click() -> None:
    item = coordinator()
    first = item.update(0.2, 0.8, 0.8, 0.0)
    assert first.left.state is PinchState.CANDIDATE
    activated = item.update(0.2, 0.8, 0.8, 0.03)
    assert activated.action is ClickAction.LEFT_CLICK


def test_thumb_middle_activation_emits_double_click_once() -> None:
    item = coordinator()
    first = item.update(0.8, 0.2, 0.8, 0.0)
    assert first.double.state is PinchState.CANDIDATE
    activated = item.update(0.8, 0.2, 0.8, 0.03)
    assert activated.action is ClickAction.DOUBLE_CLICK
    held = item.update(0.8, 0.1, 0.8, 0.10)
    assert held.action is ClickAction.NONE


def test_double_click_candidate_suppresses_left_click() -> None:
    item = coordinator()
    both = item.update(0.2, 0.2, 0.8, 0.0)
    assert both.selected.state is PinchState.CANDIDATE
    assert both.double.state is PinchState.CANDIDATE
    assert both.left.state is PinchState.INACTIVE
    activated = item.update(0.2, 0.2, 0.8, 0.03)
    assert activated.action is ClickAction.DOUBLE_CLICK


def test_thumb_little_activation_emits_right_click_once() -> None:
    item = coordinator()
    first = item.update(0.8, 0.8, 0.2, 0.0)
    assert first.right.state is PinchState.CANDIDATE
    activated = item.update(0.8, 0.8, 0.2, 0.03)
    assert activated.action is ClickAction.RIGHT_CLICK
    held = item.update(0.8, 0.8, 0.1, 0.10)
    assert held.action is ClickAction.NONE


def test_right_click_candidate_suppresses_left_click() -> None:
    item = coordinator()
    both = item.update(0.2, 0.8, 0.2, 0.0)
    assert both.selected.state is PinchState.CANDIDATE
    assert both.right.state is PinchState.CANDIDATE
    assert both.left.state is PinchState.INACTIVE
    activated = item.update(0.2, 0.8, 0.2, 0.03)
    assert activated.action is ClickAction.RIGHT_CLICK


def test_right_click_candidate_suppresses_double_click() -> None:
    item = coordinator()
    both = item.update(0.8, 0.2, 0.2, 0.0)
    assert both.right.state is PinchState.CANDIDATE
    assert both.double.state is PinchState.INACTIVE
    activated = item.update(0.8, 0.2, 0.2, 0.03)
    assert activated.action is ClickAction.RIGHT_CLICK


def test_tracking_loss_reset_clears_all_recognizers() -> None:
    item = coordinator()
    item.update(0.2, 0.8, 0.8, 0.0)
    item.reset(0.01)
    update = item.update(0.2, 0.2, 0.2, 0.02)
    assert update.action is ClickAction.NONE
    assert update.selected.state is PinchState.INACTIVE
