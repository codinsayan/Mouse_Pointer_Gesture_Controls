import pytest

from gesture_controls.gestures import (
    PinchFeatures,
    ZoomRecognizer,
    ZoomState,
    ZoomTransition,
)


def features(
    span: float = 0.40,
    index: float = 0.15,
    middle: float = 0.15,
    ring: float = 0.05,
    little: float = 0.15,
) -> PinchFeatures:
    return PinchFeatures(
        left_pinch_ratio=0.8,
        double_click_pinch_ratio=0.8,
        right_pinch_ratio=0.8,
        zoom_span_ratio=span,
        hand_size=1.0,
        index_extension_ratio=index,
        middle_extension_ratio=middle,
        ring_extension_ratio=ring,
        little_extension_ratio=little,
        palm_anchor_y=0.5,
        palm_anchor_x=0.5,
    )


def recognizer(max_steps: int = 3) -> ZoomRecognizer:
    return ZoomRecognizer(
        0.45, 0.85, 0.12, 0.08, 0.06, 0.05, 0.08, max_steps
    )


def activate(item: ZoomRecognizer) -> None:
    assert item.update(features(), 0.0).state is ZoomState.CANDIDATE
    active = item.update(features(), 0.06)
    assert active.state is ZoomState.ACTIVE
    assert active.transition is ZoomTransition.ACTIVATED


def test_pose_requires_index_middle_and_little_extended() -> None:
    item = recognizer()
    assert item.update(features(index=0.11), 0.01).state is ZoomState.INACTIVE
    assert item.update(features(middle=0.11), 0.02).state is ZoomState.INACTIVE
    assert item.update(features(little=0.11), 0.03).state is ZoomState.INACTIVE
    assert item.update(features(), 0.04).state is ZoomState.CANDIDATE


def test_candidate_is_temporally_validated_and_can_be_abandoned() -> None:
    item = recognizer()
    item.update(features(), 0.0)
    assert item.update(features(), 0.03).state is ZoomState.CANDIDATE
    assert item.update(features(span=0.5), 0.04).state is ZoomState.INACTIVE


def test_expansion_zooms_in_and_contraction_zooms_out() -> None:
    item = recognizer()
    activate(item)
    assert item.update(features(span=0.47), 0.07).steps == 0
    assert item.update(features(span=0.49), 0.08).steps == 1
    assert item.update(features(span=0.31), 0.09).steps == -2


def test_large_motion_is_bounded_without_a_step_backlog() -> None:
    item = recognizer(max_steps=2)
    activate(item)
    assert item.update(features(span=0.80), 0.07).steps == 2
    assert item.update(features(span=0.80), 0.08).steps == 0


def test_release_uses_hysteresis_and_temporal_validation() -> None:
    item = recognizer()
    activate(item)
    assert item.update(features(little=0.09), 0.07).state is ZoomState.ACTIVE
    assert item.update(features(span=0.90), 0.08).state is ZoomState.RELEASING
    assert item.update(features(span=0.90), 0.12).state is ZoomState.RELEASING
    released = item.update(features(span=0.90), 0.13)
    assert released.state is ZoomState.INACTIVE
    assert released.transition is ZoomTransition.RELEASED
    assert released.claims_frame


def test_reset_and_non_monotonic_timestamp_handling() -> None:
    item = recognizer()
    item.update(features(), 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(features(), 0.9)
    item.reset()
    assert item.update(features(), 0.0).state is ZoomState.CANDIDATE
