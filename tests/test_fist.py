import pytest

from gesture_controls.gestures import (
    FistRecognizer,
    FistState,
    FistTransition,
    PinchFeatures,
)


def features(
    index: float = 0.05,
    middle: float = 0.05,
    ring: float = 0.05,
    little: float = 0.05,
) -> PinchFeatures:
    return PinchFeatures(
        left_pinch_ratio=0.8,
        double_click_pinch_ratio=0.8,
        right_pinch_ratio=0.8,
        hand_size=1.0,
        index_extension_ratio=index,
        middle_extension_ratio=middle,
        ring_extension_ratio=ring,
        little_extension_ratio=little,
        palm_anchor_y=0.5,
        palm_anchor_x=0.5,
    )


def recognizer() -> FistRecognizer:
    return FistRecognizer(0.10, 0.18, 0.06, 0.05)


def test_all_four_fingers_must_be_folded_for_activation() -> None:
    item = recognizer()
    assert item.update(features(index=0.11), 0.0).state is FistState.INACTIVE
    assert item.update(features(), 0.01).state is FistState.CANDIDATE
    active = item.update(features(), 0.07)
    assert active.state is FistState.ACTIVE
    assert active.transition is FistTransition.ACTIVATED


def test_candidate_can_be_abandoned_without_activation() -> None:
    item = recognizer()
    item.update(features(), 0.0)
    abandoned = item.update(features(ring=0.20), 0.03)
    assert abandoned.state is FistState.INACTIVE
    assert abandoned.transition is FistTransition.NONE


def test_release_hysteresis_prevents_folded_state_jitter() -> None:
    item = recognizer()
    item.update(features(), 0.0)
    item.update(features(), 0.06)
    assert item.update(features(little=0.15), 0.07).state is FistState.ACTIVE
    assert item.update(features(little=0.20), 0.08).state is FistState.RELEASING
    assert item.update(features(little=0.20), 0.12).state is FistState.RELEASING
    released = item.update(features(little=0.20), 0.13)
    assert released.state is FistState.INACTIVE
    assert released.transition is FistTransition.RELEASED


def test_reset_clears_time_history_and_invalid_configuration_is_rejected() -> None:
    item = recognizer()
    item.update(features(), 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(features(), 0.9)
    item.reset()
    assert item.update(features(), 0.0).state is FistState.CANDIDATE
    with pytest.raises(ValueError, match="fist ratios"):
        FistRecognizer(0.2, 0.1, 0.0, 0.0)
    with pytest.raises(ValueError, match="hold times"):
        FistRecognizer(0.1, 0.2, -0.1, 0.0)
