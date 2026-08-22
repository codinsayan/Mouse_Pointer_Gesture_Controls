import pytest

from gesture_controls.gestures import extract_left_pinch_features, reference_hand_size
from gesture_controls.tracking import Landmark


def make_hand(
    scale: float = 1.0,
    pinch_ratio: float = 0.2,
    double_ratio: float = 0.6,
) -> tuple[Landmark, ...]:
    points = [Landmark(2.0, 3.0, 0.0) for _ in range(21)]
    points[0] = Landmark(2.0, 3.0, 0.0)
    points[9] = Landmark(2.0, 3.0 + scale, 0.0)
    points[5] = Landmark(2.0 - scale / 2, 3.5, 0.0)
    points[17] = Landmark(2.0 + scale / 2, 3.5, 0.0)
    points[4] = Landmark(2.0, 3.0, 0.0)
    points[8] = Landmark(2.0 + scale * pinch_ratio, 3.0, 0.0)
    points[12] = Landmark(2.0 + scale * double_ratio, 3.0, 0.0)
    return tuple(points)


def test_reference_hand_size_uses_palm_geometry() -> None:
    assert reference_hand_size(make_hand(scale=2.0)) == pytest.approx(2.0)


def test_left_pinch_ratio_is_scale_independent() -> None:
    small = extract_left_pinch_features(make_hand(scale=0.5, pinch_ratio=0.25))
    large = extract_left_pinch_features(make_hand(scale=3.0, pinch_ratio=0.25))
    assert small.left_pinch_ratio == pytest.approx(0.25)
    assert large.left_pinch_ratio == pytest.approx(0.25)


def test_double_click_ratio_uses_thumb_to_middle_tip() -> None:
    features = extract_left_pinch_features(
        make_hand(scale=2.0, pinch_ratio=0.7, double_ratio=0.2)
    )
    assert features.double_click_pinch_ratio == pytest.approx(0.2)


def test_feature_extraction_requires_complete_landmarks() -> None:
    with pytest.raises(ValueError, match="at least 21"):
        extract_left_pinch_features((Landmark(0, 0),) * 10)


def test_feature_extraction_rejects_degenerate_hand_size() -> None:
    with pytest.raises(ValueError, match="degenerate"):
        reference_hand_size((Landmark(0, 0),) * 21)
