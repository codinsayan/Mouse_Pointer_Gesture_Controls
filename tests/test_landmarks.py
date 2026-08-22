import pytest

from gesture_controls.tracking.landmarks import Landmark, normalized_distance
from gesture_controls.ui.overlay import landmark_to_pixel


def test_normalized_distance_uses_three_dimensions() -> None:
    assert normalized_distance(Landmark(0, 0, 0), Landmark(1, 2, 2)) == pytest.approx(3)


def test_landmark_to_pixel_maps_and_clamps() -> None:
    assert landmark_to_pixel(0.5, 0.5, 640, 480) == (320, 240)
    assert landmark_to_pixel(-1, 2, 640, 480) == (0, 479)

