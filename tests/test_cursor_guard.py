import pytest

from gesture_controls.gestures import (
    ClickCursorGuard,
    GestureTransition,
    PinchState,
    PinchUpdate,
)


def update(
    state: PinchState,
    transition: GestureTransition = GestureTransition.NONE,
) -> PinchUpdate:
    return PinchUpdate(0.2, state, transition)


def test_candidate_freezes_and_abandonment_requests_one_resume() -> None:
    guard = ClickCursorGuard(0.05)
    candidate = guard.update(update(PinchState.CANDIDATE), 0.0)
    assert candidate.freeze
    resumed = guard.update(update(PinchState.INACTIVE), 0.02)
    assert not resumed.freeze
    assert resumed.resume_smoothing
    steady = guard.update(update(PinchState.INACTIVE), 0.03)
    assert not steady.resume_smoothing


def test_release_stays_frozen_through_resume_delay() -> None:
    guard = ClickCursorGuard(0.05)
    guard.update(update(PinchState.ACTIVE), 0.0)
    released = guard.update(
        update(PinchState.INACTIVE, GestureTransition.RELEASED), 0.10
    )
    assert released.freeze
    assert guard.update(update(PinchState.INACTIVE), 0.149).freeze
    resumed = guard.update(update(PinchState.INACTIVE), 0.15)
    assert not resumed.freeze
    assert resumed.resume_smoothing


def test_guard_rejects_non_monotonic_time() -> None:
    guard = ClickCursorGuard(0.05)
    guard.update(update(PinchState.INACTIVE), 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        guard.update(update(PinchState.INACTIVE), 0.5)


def test_zero_delay_resumes_on_release_frame() -> None:
    guard = ClickCursorGuard(0.0)
    guard.update(update(PinchState.ACTIVE), 0.0)
    released = guard.update(
        update(PinchState.INACTIVE, GestureTransition.RELEASED), 0.10
    )
    assert not released.freeze
    assert released.resume_smoothing
