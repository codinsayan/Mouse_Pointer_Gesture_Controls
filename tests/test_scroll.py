import pytest

from gesture_controls.gestures import (
    ClickAction,
    ClickGestureCoordinator,
    DragRecognizer,
    DragState,
    FistRecognizer,
    GestureAction,
    GestureCoordinator,
    PinchFeatures,
    PinchRecognizer,
    ScrollRecognizer,
    ScrollAxis,
    ScrollState,
    ScrollTransition,
)


def features(
    *,
    index: float = 0.25,
    middle: float = 0.25,
    ring: float = 0.05,
    little: float = 0.05,
    anchor_x: float = 0.5,
    anchor_y: float = 0.5,
    hand_size: float = 1.0,
    left: float = 0.8,
    double: float = 0.8,
    right: float = 0.8,
) -> PinchFeatures:
    return PinchFeatures(
        left,
        double,
        right,
        hand_size,
        index,
        middle,
        ring,
        little,
        anchor_y,
        anchor_x,
    )


def recognizer(max_steps: int = 3) -> ScrollRecognizer:
    return ScrollRecognizer(0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, max_steps)


def horizontal_features(
    *,
    anchor_x: float = 0.5,
    anchor_y: float = 0.5,
    hand_size: float = 1.0,
    left: float = 0.8,
    double: float = 0.8,
    right: float = 0.8,
) -> PinchFeatures:
    return features(
        index=0.05,
        middle=0.25,
        ring=0.25,
        little=0.05,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
        hand_size=hand_size,
        left=left,
        double=double,
        right=right,
    )


def click_coordinator() -> ClickGestureCoordinator:
    return ClickGestureCoordinator(
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
        PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06),
    )


def interaction_coordinator() -> GestureCoordinator:
    return GestureCoordinator(
        recognizer(),
        click_coordinator(),
        FistRecognizer(0.10, 0.18, 0.06, 0.05),
        DragRecognizer(0.25),
    )


def activate(
    item: ScrollRecognizer,
    pose: PinchFeatures | None = None,
    expected_axis: ScrollAxis = ScrollAxis.VERTICAL,
) -> None:
    pose = features() if pose is None else pose
    first = item.update(pose, 0.0)
    assert first.state is ScrollState.CANDIDATE
    assert first.axis is expected_axis
    update = item.update(pose, 0.06)
    assert update.state is ScrollState.ACTIVE
    assert update.transition is ScrollTransition.ACTIVATED
    assert update.axis is expected_axis


def test_pose_requires_index_and_middle_raised_with_ring_and_little_folded() -> None:
    item = recognizer()
    assert item.update(features(index=0.17), 0.0).state is ScrollState.INACTIVE
    assert item.update(features(ring=0.11), 0.01).state is ScrollState.INACTIVE
    assert item.update(features(), 0.02).state is ScrollState.CANDIDATE


def test_horizontal_pose_requires_middle_and_ring_with_index_and_little_folded() -> None:
    item = recognizer()
    assert item.update(horizontal_features(), 0.0).axis is ScrollAxis.HORIZONTAL
    item.reset()
    assert item.update(features(index=0.11, ring=0.25), 0.0).state is ScrollState.INACTIVE
    assert item.update(features(index=0.05, ring=0.17), 0.01).state is ScrollState.INACTIVE


def test_activation_is_temporally_validated_and_candidate_can_be_abandoned() -> None:
    item = recognizer()
    assert item.update(features(), 0.0).state is ScrollState.CANDIDATE
    assert item.update(features(), 0.03).state is ScrollState.CANDIDATE
    assert item.update(features(index=0.0), 0.04).state is ScrollState.INACTIVE


def test_switching_candidate_pose_restarts_temporal_validation() -> None:
    item = recognizer()
    assert item.update(features(), 0.0).axis is ScrollAxis.VERTICAL
    switched = item.update(horizontal_features(), 0.04)
    assert switched.state is ScrollState.CANDIDATE
    assert switched.axis is ScrollAxis.HORIZONTAL
    assert item.update(horizontal_features(), 0.06).state is ScrollState.CANDIDATE
    assert item.update(horizontal_features(), 0.10).state is ScrollState.ACTIVE


def test_vertical_motion_emits_signed_scale_independent_steps() -> None:
    item = recognizer()
    activate(item)
    assert item.update(features(anchor_y=0.43), 0.07).steps == 0
    assert item.update(features(anchor_y=0.41), 0.08).steps == 1
    assert item.update(features(anchor_y=0.59), 0.09).steps == 0
    assert item.update(features(anchor_y=0.50), 0.10).steps == 1

    scaled = recognizer()
    activate(scaled)
    assert scaled.update(features(anchor_y=0.32, hand_size=2.0), 0.07).steps == 1


def test_horizontal_motion_emits_left_and_right_scale_independent_steps() -> None:
    item = recognizer()
    activate(item, horizontal_features(), ScrollAxis.HORIZONTAL)
    right = item.update(horizontal_features(anchor_x=0.59), 0.07)
    assert right.horizontal_steps == 1
    assert right.steps == 0
    left = item.update(horizontal_features(anchor_x=0.39), 0.08)
    assert left.horizontal_steps == 0
    repeated_right = item.update(horizontal_features(anchor_x=0.48), 0.09)
    assert repeated_right.horizontal_steps == 1

    scaled = recognizer()
    activate(scaled, horizontal_features(hand_size=2.0), ScrollAxis.HORIZONTAL)
    assert (
        scaled.update(horizontal_features(anchor_x=0.68, hand_size=2.0), 0.07).horizontal_steps
        == 1
    )


def test_pose_binds_axis_and_ignores_motion_on_the_other_axis() -> None:
    vertical = recognizer()
    activate(vertical)
    assert vertical.update(features(anchor_x=0.8), 0.07).horizontal_steps == 0
    assert vertical.update(features(anchor_x=0.8, anchor_y=0.40), 0.08).steps == 1

    horizontal = recognizer()
    activate(horizontal, horizontal_features(), ScrollAxis.HORIZONTAL)
    assert horizontal.update(horizontal_features(anchor_y=0.2), 0.07).steps == 0
    update = horizontal.update(horizontal_features(anchor_x=0.59, anchor_y=0.2), 0.08)
    assert update.horizontal_steps == 1


def test_large_motion_is_bounded_and_does_not_build_a_step_backlog() -> None:
    item = recognizer(max_steps=2)
    activate(item)
    moved = features(anchor_y=-1.0)
    assert item.update(moved, 0.07).steps == 2
    assert item.update(moved, 0.08).steps == 0


def test_releasing_pose_allows_a_new_scroll_direction() -> None:
    item = recognizer()
    activate(item)
    assert item.update(features(anchor_y=0.41), 0.07).steps == 1
    assert item.update(features(index=0.0), 0.08).state is ScrollState.RELEASING
    assert item.update(features(index=0.0), 0.13).state is ScrollState.INACTIVE
    assert item.update(features(anchor_y=0.41), 0.14).state is ScrollState.CANDIDATE
    assert item.update(features(anchor_y=0.41), 0.20).state is ScrollState.ACTIVE
    assert item.update(features(anchor_y=0.50), 0.21).steps == -1


def test_output_multiplier_scales_steps_after_quantization() -> None:
    item = ScrollRecognizer(
        0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, 3, True, 3
    )
    activate(item)
    assert item.update(features(anchor_y=0.41), 0.07).steps == 3


def test_direction_lock_can_be_disabled_for_legacy_reversible_behavior() -> None:
    item = ScrollRecognizer(
        0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, 3, False, 1
    )
    activate(item)
    assert item.update(features(anchor_y=0.41), 0.07).steps == 1
    assert item.update(features(anchor_y=0.59), 0.08).steps == -2


def test_scroll_recognizer_validates_direction_lock_type() -> None:
    with pytest.raises(ValueError, match="direction lock"):
        ScrollRecognizer(
            0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, 3, 1  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("multiplier", [0, 21, True])
def test_scroll_recognizer_validates_output_multiplier(multiplier: int) -> None:
    with pytest.raises(ValueError, match="output multiplier"):
        ScrollRecognizer(
            0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, 3, True, multiplier
        )


def test_pose_hysteresis_and_release_hold_prevent_jitter() -> None:
    item = recognizer()
    activate(item)
    hysteresis_pose = features(index=0.11, middle=0.11, ring=0.17, little=0.17)
    assert item.update(hysteresis_pose, 0.07).state is ScrollState.ACTIVE
    releasing = item.update(features(index=0.09), 0.08)
    assert releasing.state is ScrollState.RELEASING
    assert item.update(features(index=0.09), 0.12).state is ScrollState.RELEASING
    released = item.update(features(index=0.09), 0.13)
    assert released.state is ScrollState.INACTIVE
    assert released.transition is ScrollTransition.RELEASED
    assert released.axis is ScrollAxis.NONE
    assert released.claims_frame


def test_horizontal_pose_uses_extension_and_folded_hysteresis() -> None:
    item = recognizer()
    activate(item, horizontal_features(), ScrollAxis.HORIZONTAL)
    hysteresis_pose = features(index=0.17, middle=0.11, ring=0.11, little=0.17)
    assert item.update(hysteresis_pose, 0.07).state is ScrollState.ACTIVE
    assert item.update(features(index=0.19, middle=0.25, ring=0.25), 0.08).state is ScrollState.RELEASING


def test_reset_and_non_monotonic_timestamp_handling() -> None:
    item = recognizer()
    item.update(features(), 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(features(), 0.9)
    item.reset()
    assert item.update(features(), 0.0).state is ScrollState.CANDIDATE


@pytest.mark.parametrize(
    "conflicting",
    [
        features(left=0.2, double=0.2, right=0.2),
        horizontal_features(left=0.2, double=0.2, right=0.2),
    ],
)
def test_scroll_claim_suppresses_click_even_when_pinch_ratio_is_active(
    conflicting: PinchFeatures,
) -> None:
    item = interaction_coordinator()
    first = item.update(conflicting, 0.0)
    assert first.scroll.state is ScrollState.CANDIDATE
    assert first.click is None
    active = item.update(conflicting, 0.06)
    assert active.scroll.state is ScrollState.ACTIVE
    assert active.click is None


def test_clicks_are_evaluated_when_scroll_pose_is_inactive() -> None:
    item = interaction_coordinator()
    click_pose = features(index=0.0, middle=0.0, ring=0.2, left=0.2)
    assert item.update(click_pose, 0.0).click is not None
    update = item.update(click_pose, 0.03)
    assert update.click is not None
    assert update.click.action is ClickAction.LEFT_CLICK
    assert update.action is GestureAction.LEFT_CLICK


def test_fist_hold_starts_precise_drag_and_opening_ends_it() -> None:
    item = interaction_coordinator()
    fist_pose = features(index=0.05, middle=0.05, ring=0.05, little=0.05)
    candidate = item.update(fist_pose, 0.0)
    assert candidate.cursor_should_freeze
    armed = item.update(fist_pose, 0.06)
    assert armed.drag.state is DragState.ARMED
    assert armed.cursor_should_freeze
    started = item.update(fist_pose, 0.31)
    assert started.action is GestureAction.DRAG_STARTED
    assert started.drag.state is DragState.DRAGGING
    assert not started.cursor_should_freeze
    ended = item.update(
        features(index=0.25, middle=0.05, ring=0.05, little=0.05), 0.32
    )
    assert ended.action is GestureAction.DRAG_ENDED
    assert ended.drag.state is DragState.IDLE


def test_scroll_conflict_ends_an_active_fist_drag() -> None:
    item = interaction_coordinator()
    fist_pose = features(index=0.05, middle=0.05, ring=0.05, little=0.05)
    item.update(fist_pose, 0.0)
    item.update(fist_pose, 0.06)
    item.update(fist_pose, 0.31)
    ended = item.update(features(), 0.32)
    assert ended.scroll.claims_frame
    assert ended.action is GestureAction.DRAG_ENDED


def test_tracking_reset_ends_drag_exactly_once() -> None:
    item = interaction_coordinator()
    fist_pose = features(index=0.05, middle=0.05, ring=0.05, little=0.05)
    item.update(fist_pose, 0.0)
    item.update(fist_pose, 0.06)
    item.update(fist_pose, 0.31)
    assert item.reset(0.32) is GestureAction.DRAG_ENDED
    assert item.reset(0.33) is GestureAction.NONE


def test_fist_candidate_suppresses_all_click_pinches() -> None:
    item = interaction_coordinator()
    fist_with_conflicting_pinches = features(
        index=0.05,
        middle=0.05,
        ring=0.05,
        little=0.05,
        left=0.2,
        double=0.2,
        right=0.2,
    )
    update = item.update(fist_with_conflicting_pinches, 0.0)
    assert update.fist.claims_frame
    assert update.click is None
