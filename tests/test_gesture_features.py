import pytest

from gesture_controls.gestures import extract_left_pinch_features, reference_hand_size
from gesture_controls.tracking import Landmark


def make_hand(
    scale: float = 1.0,
    pinch_ratio: float = 0.2,
    double_ratio: float = 0.6,
    right_ratio: float = 0.7,
    zoom_ratio: float = 0.6,
) -> tuple[Landmark, ...]:
    points = [Landmark(2.0, 3.0, 0.0) for _ in range(21)]
    points[0] = Landmark(2.0, 3.0, 0.0)
    points[9] = Landmark(2.0, 3.0 + scale, 0.0)
    points[5] = Landmark(2.0 - scale / 2, 3.5, 0.0)
    points[17] = Landmark(2.0 + scale / 2, 3.5, 0.0)
    points[4] = Landmark(2.0, 3.0, 0.0)
    points[8] = Landmark(2.0 + scale * pinch_ratio, 3.0, 0.0)
    points[12] = Landmark(2.0 + scale * double_ratio, 3.0, 0.0)
    points[20] = Landmark(2.0 + scale * right_ratio, 3.0, 0.0)
    points[16] = Landmark(2.0 + scale * zoom_ratio, 3.0, 0.0)
    return tuple(points)


def make_scroll_hand(
    scale: float = 1.0, x_offset: float = 0.0, y_offset: float = 0.0
) -> tuple[Landmark, ...]:
    points = [Landmark(0.0, y_offset, 0.0) for _ in range(21)]
    points[0] = Landmark(0.0, y_offset, 0.0)
    points[5] = Landmark(-0.5 * scale, y_offset + 0.5 * scale, 0.0)
    points[9] = Landmark(0.0, y_offset + scale, 0.0)
    points[13] = Landmark(0.25 * scale, y_offset + 0.6 * scale, 0.0)
    points[17] = Landmark(0.5 * scale, y_offset + 0.5 * scale, 0.0)
    points[6] = Landmark(-0.2 * scale, y_offset - 0.2 * scale, 0.0)
    points[8] = Landmark(-0.2 * scale, y_offset - 0.8 * scale, 0.0)
    points[10] = Landmark(0.05 * scale, y_offset - 0.2 * scale, 0.0)
    points[12] = Landmark(0.05 * scale, y_offset - 0.8 * scale, 0.0)
    points[14] = Landmark(0.25 * scale, y_offset + 0.5 * scale, 0.0)
    points[16] = Landmark(0.25 * scale, y_offset + 0.35 * scale, 0.0)
    points[18] = Landmark(0.5 * scale, y_offset + 0.45 * scale, 0.0)
    points[20] = Landmark(0.45 * scale, y_offset + 0.35 * scale, 0.0)
    return tuple(
        Landmark(point.x + x_offset, point.y, point.z) for point in points
    )


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


def test_right_click_ratio_is_scale_independent() -> None:
    small = extract_left_pinch_features(make_hand(scale=0.5, right_ratio=0.22))
    large = extract_left_pinch_features(make_hand(scale=3.0, right_ratio=0.22))
    assert small.right_pinch_ratio == pytest.approx(0.22)
    assert large.right_pinch_ratio == pytest.approx(0.22)


def test_right_click_ratio_uses_thumb_to_little_tip_not_ring_tip() -> None:
    points = list(make_hand(scale=1.0, right_ratio=0.2))
    points[16] = Landmark(2.01, 3.0, 0.0)
    features = extract_left_pinch_features(tuple(points))
    assert features.right_pinch_ratio == pytest.approx(0.2)


def test_zoom_span_uses_thumb_to_ring_tip_and_is_scale_independent() -> None:
    small = extract_left_pinch_features(make_hand(scale=0.5, zoom_ratio=0.24))
    large = extract_left_pinch_features(make_hand(scale=3.0, zoom_ratio=0.24))
    assert small.zoom_span_ratio == pytest.approx(0.24)
    assert large.zoom_span_ratio == pytest.approx(0.24)


def test_scroll_extension_geometry_is_scale_independent() -> None:
    small = extract_left_pinch_features(make_scroll_hand(scale=0.5))
    large = extract_left_pinch_features(make_scroll_hand(scale=3.0))
    assert small.index_extension_ratio == pytest.approx(large.index_extension_ratio)
    assert small.middle_extension_ratio == pytest.approx(large.middle_extension_ratio)
    assert small.ring_extension_ratio == pytest.approx(large.ring_extension_ratio)
    assert small.little_extension_ratio == pytest.approx(large.little_extension_ratio)
    assert small.index_extension_ratio > 0.18
    assert small.middle_extension_ratio > 0.18
    assert small.ring_extension_ratio < 0.10
    assert small.little_extension_ratio < 0.10


def test_palm_anchor_tracks_translation_without_using_fingertips() -> None:
    first = extract_left_pinch_features(make_scroll_hand(y_offset=0.1))
    moved = extract_left_pinch_features(
        make_scroll_hand(x_offset=0.3, y_offset=0.35)
    )
    assert moved.palm_anchor_y - first.palm_anchor_y == pytest.approx(0.25)
    assert moved.palm_anchor_x - first.palm_anchor_x == pytest.approx(0.3)


def test_feature_extraction_requires_complete_landmarks() -> None:
    with pytest.raises(ValueError, match="at least 21"):
        extract_left_pinch_features((Landmark(0, 0),) * 10)


def test_feature_extraction_rejects_degenerate_hand_size() -> None:
    with pytest.raises(ValueError, match="degenerate"):
        reference_hand_size((Landmark(0, 0),) * 21)
