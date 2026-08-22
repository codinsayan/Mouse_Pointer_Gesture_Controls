from gesture_controls.tracking import Landmark, TrackingResult


def test_empty_result_has_no_hand() -> None:
    assert not TrackingResult().hand_detected


def test_landmarks_mark_hand_as_detected() -> None:
    result = TrackingResult((Landmark(0.1, 0.2),), "Left", 0.9)
    assert result.hand_detected
    assert result.handedness == "Left"

