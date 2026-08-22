from pathlib import Path

import pytest

from gesture_controls.config import AppConfig


def test_default_configuration_is_safe_and_expected() -> None:
    config = AppConfig()
    assert config.camera_index == 0
    assert (config.frame_width, config.frame_height, config.target_fps) == (640, 480, 30)
    assert config.model_path == Path("assets/models/hand_landmarker.task")


@pytest.mark.parametrize("field", ["detection_confidence", "presence_confidence", "tracking_confidence"])
def test_rejects_invalid_confidence(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        AppConfig(**{field: 1.01})


def test_rejects_negative_camera_index() -> None:
    with pytest.raises(ValueError, match="camera_index"):
        AppConfig(camera_index=-1)


def test_rejects_invalid_cursor_region() -> None:
    with pytest.raises(ValueError, match="horizontal region"):
        AppConfig(cursor_region_left=0.9, cursor_region_right=0.1)


def test_rejects_invalid_cursor_smoothing() -> None:
    with pytest.raises(ValueError, match="smoothing"):
        AppConfig(cursor_smoothing_seconds=0.0)


def test_rejects_invalid_minimum_movement() -> None:
    with pytest.raises(ValueError, match="minimum_movement"):
        AppConfig(cursor_minimum_movement=-0.1)
