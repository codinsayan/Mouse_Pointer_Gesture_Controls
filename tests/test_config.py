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


def test_rejects_invalid_left_pinch_hysteresis() -> None:
    with pytest.raises(ValueError, match="left-pinch ratios"):
        AppConfig(left_pinch_activation_ratio=0.5, left_pinch_release_ratio=0.4)


@pytest.mark.parametrize(
    "field",
    [
        "left_click_cooldown_seconds",
        "double_click_activation_hold_seconds",
        "double_click_release_hold_seconds",
        "double_click_cooldown_seconds",
        "right_click_activation_hold_seconds",
        "right_click_release_hold_seconds",
        "right_click_cooldown_seconds",
        "scroll_activation_hold_seconds",
        "scroll_release_hold_seconds",
        "post_click_cursor_resume_delay_seconds",
    ],
)
def test_rejects_negative_left_click_timing(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        AppConfig(**{field: -0.1})


def test_rejects_invalid_double_click_pinch_hysteresis() -> None:
    with pytest.raises(ValueError, match="double-click pinch ratios"):
        AppConfig(
            double_click_pinch_activation_ratio=0.5,
            double_click_pinch_release_ratio=0.4,
        )


def test_rejects_invalid_right_pinch_hysteresis() -> None:
    with pytest.raises(ValueError, match="right-pinch ratios"):
        AppConfig(right_pinch_activation_ratio=0.5, right_pinch_release_ratio=0.4)


def test_rejects_invalid_scroll_extension_hysteresis() -> None:
    with pytest.raises(ValueError, match="scroll extension ratios"):
        AppConfig(
            scroll_extension_activation_ratio=0.10,
            scroll_extension_release_ratio=0.18,
        )


def test_rejects_invalid_scroll_folded_hysteresis() -> None:
    with pytest.raises(ValueError, match="scroll folded ratios"):
        AppConfig(
            scroll_folded_activation_ratio=0.18,
            scroll_folded_release_ratio=0.10,
        )


def test_rejects_invalid_scroll_step_distance() -> None:
    with pytest.raises(ValueError, match="scroll_step_distance_ratio"):
        AppConfig(scroll_step_distance_ratio=0.0)


@pytest.mark.parametrize("value", [0, 1.5, True])
def test_rejects_invalid_scroll_step_bound(value: object) -> None:
    with pytest.raises(ValueError, match="scroll_max_steps_per_frame"):
        AppConfig(scroll_max_steps_per_frame=value)  # type: ignore[arg-type]
