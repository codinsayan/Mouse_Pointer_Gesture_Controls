from gesture_controls.tracking import hand_matches_preference


def test_any_preference_accepts_reported_or_missing_handedness() -> None:
    assert hand_matches_preference("Left", "any")
    assert hand_matches_preference(None, "any")


def test_specific_preference_is_case_insensitive_and_rejects_missing_label() -> None:
    assert hand_matches_preference("Left", "left")
    assert hand_matches_preference("RIGHT", "right")
    assert not hand_matches_preference("Right", "left")
    assert not hand_matches_preference(None, "right")
