import pytest

from gesture_controls.gestures import (
    ClickGestureCoordinator,
    DragRecognizer,
    FistRecognizer,
    GestureAction,
    GestureCoordinator,
    OpenPalmPauseRecognizer,
    PauseState,
    PauseTransition,
    PinchFeatures,
    PinchRecognizer,
    ScrollRecognizer,
    ZoomRecognizer,
)


def features(extension: float) -> PinchFeatures:
    return PinchFeatures(
        0.8,
        0.8,
        0.8,
        0.8,
        1.0,
        extension,
        extension,
        extension,
        extension,
        0.5,
        0.5,
    )


def recognizer() -> OpenPalmPauseRecognizer:
    return OpenPalmPauseRecognizer(0.18, 0.10, 0.35, 0.05)


def test_open_palm_activates_once_after_deliberate_hold() -> None:
    item = recognizer()
    first = item.update(features(0.20), 0.0)
    early = item.update(features(0.20), 0.34)
    active = item.update(features(0.20), 0.35)
    held = item.update(features(0.20), 0.80)

    assert first.state is PauseState.CANDIDATE
    assert early.transition is PauseTransition.NONE
    assert active.transition is PauseTransition.ACTIVATED
    assert held.transition is PauseTransition.NONE


def test_open_palm_uses_release_hysteresis_and_temporal_release() -> None:
    item = recognizer()
    item.update(features(0.20), 0.0)
    item.update(features(0.20), 0.35)
    assert item.update(features(0.12), 0.40).state is PauseState.ACTIVE
    assert item.update(features(0.05), 0.41).state is PauseState.RELEASING
    released = item.update(features(0.05), 0.46)
    assert released.state is PauseState.INACTIVE
    assert released.transition is PauseTransition.RELEASED


def test_candidate_cancels_and_reset_clears_timestamp_history() -> None:
    item = recognizer()
    item.update(features(0.20), 1.0)
    assert item.update(features(0.05), 1.1).state is PauseState.INACTIVE
    item.reset()
    assert item.update(features(0.20), 0.0).state is PauseState.CANDIDATE


def test_timestamps_must_be_monotonic() -> None:
    item = recognizer()
    item.update(features(0.20), 1.0)
    with pytest.raises(ValueError, match="monotonic"):
        item.update(features(0.20), 0.9)


@pytest.mark.parametrize(
    "arguments",
    [
        (0.10, 0.10, 0.35, 0.05),
        (0.18, 0.10, -0.1, 0.05),
        (0.18, 0.10, 0.35, -0.1),
    ],
)
def test_invalid_settings_are_rejected(arguments: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        OpenPalmPauseRecognizer(*arguments)


def test_open_palm_has_priority_over_zoom_and_click_families() -> None:
    pinch = lambda: PinchRecognizer(0.30, 0.42, 0.03, 0.03, 0.06)
    coordinator = GestureCoordinator(
        ScrollRecognizer(0.18, 0.10, 0.10, 0.18, 0.06, 0.05, 0.08, 3),
        ClickGestureCoordinator(pinch(), pinch(), pinch()),
        FistRecognizer(0.10, 0.18, 0.06, 0.05),
        DragRecognizer(0.25),
        ZoomRecognizer(0.45, 0.85, 0.12, 0.08, 0.06, 0.05, 0.08, 3),
        recognizer(),
    )
    open_palm_that_also_matches_zoom = PinchFeatures(
        0.2, 0.2, 0.2, 0.2, 1.0, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5
    )

    candidate = coordinator.update(open_palm_that_also_matches_zoom, 0.0)
    activated = coordinator.update(open_palm_that_also_matches_zoom, 0.35)

    assert candidate.pause.state is PauseState.CANDIDATE
    assert candidate.click is None
    assert activated.action is GestureAction.PAUSE_REQUESTED
    assert not activated.zoom.claims_frame
