import pytest

from gesture_controls.gestures import (
    GestureTransition,
    LeftPinchRecognizer,
    PinchState,
)


def recognizer() -> LeftPinchRecognizer:
    return LeftPinchRecognizer(0.30, 0.42, 0.08, 0.05, 0.06)


def activate(item: LeftPinchRecognizer) -> None:
    candidate = item.update(0.2, 0.0)
    assert candidate.state is PinchState.CANDIDATE
    assert candidate.cursor_should_freeze
    update = item.update(0.2, 0.08)
    assert update.transition is GestureTransition.ACTIVATED


def test_activation_requires_continuous_hold() -> None:
    item = recognizer()
    item.update(0.2, 0.0)
    item.update(0.31, 0.05)
    assert item.update(0.2, 0.08).transition is GestureTransition.NONE
    assert item.update(0.2, 0.16).transition is GestureTransition.ACTIVATED


def test_holding_pinch_emits_only_one_activation() -> None:
    item = recognizer()
    activate(item)
    for timestamp in (0.10, 0.20, 1.0):
        update = item.update(0.1, timestamp)
        assert update.state is PinchState.ACTIVE
        assert update.transition is GestureTransition.NONE


def test_hysteresis_band_does_not_release_active_pinch() -> None:
    item = recognizer()
    activate(item)
    assert item.update(0.36, 0.20).state is PinchState.ACTIVE
    assert item.update(0.36, 1.0).state is PinchState.ACTIVE


def test_release_requires_hold_and_starts_cooldown() -> None:
    item = recognizer()
    activate(item)
    assert item.update(0.5, 0.20).transition is GestureTransition.NONE
    released = item.update(0.5, 0.25)
    assert released.transition is GestureTransition.RELEASED
    assert released.state is PinchState.INACTIVE
    assert item.update(0.2, 0.30).transition is GestureTransition.NONE
    assert item.update(0.2, 0.31).state is PinchState.CANDIDATE
    second = item.update(0.2, 0.39)
    assert second.transition is GestureTransition.ACTIVATED


def test_abandoned_candidate_unfreezes_without_click() -> None:
    item = recognizer()
    assert item.update(0.2, 0.0).state is PinchState.CANDIDATE
    update = item.update(0.4, 0.03)
    assert update.state is PinchState.INACTIVE
    assert update.transition is GestureTransition.NONE
    assert not update.cursor_should_freeze


def test_tracking_loss_reset_clears_active_state_without_activation() -> None:
    item = recognizer()
    activate(item)
    item.reset(0.10)
    assert item.state is PinchState.INACTIVE
    assert item.update(0.2, 0.20).transition is GestureTransition.NONE


def test_rejects_invalid_thresholds_and_non_monotonic_time() -> None:
    with pytest.raises(ValueError, match="activation < release"):
        LeftPinchRecognizer(0.5, 0.4, 0, 0, 0)
    item = recognizer()
    item.update(0.5, 2.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(0.5, 1.0)
