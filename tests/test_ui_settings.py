from pathlib import Path

import pytest

from gesture_controls.config import AppConfig, load_config
from gesture_controls.ui.settings_model import (
    DashboardSettings,
    load_dashboard_profile,
    pointer_speed_to_smoothing,
    save_dashboard_profile,
    smoothing_to_pointer_speed,
)


@pytest.mark.parametrize(
    ("speed", "smoothing"), [(1, 0.20), (7, 0.08), (10, 0.02)]
)
def test_pointer_speed_mapping_is_stable(speed: int, smoothing: float) -> None:
    assert pointer_speed_to_smoothing(speed) == pytest.approx(smoothing)
    assert smoothing_to_pointer_speed(smoothing) == speed


@pytest.mark.parametrize("speed", [0, 11, True])
def test_pointer_speed_rejects_invalid_values(speed: int) -> None:
    with pytest.raises(ValueError, match="pointer speed"):
        pointer_speed_to_smoothing(speed)


def test_dashboard_round_trip_preserves_calibration_and_other_settings() -> None:
    original = AppConfig(
        cursor_region_left=0.21,
        cursor_region_right=0.79,
        left_pinch_activation_ratio=0.22,
    )
    presentation = DashboardSettings.from_config(original)
    updated = DashboardSettings(9, 5, 1.6, "left").apply(original)

    assert presentation.pointer_speed == 7
    assert updated.cursor_smoothing_seconds == pytest.approx(0.04)
    assert updated.scroll_output_multiplier == 5
    assert updated.cursor_sensitivity == 1.6
    assert updated.dominant_hand == "left"
    assert updated.cursor_region_left == original.cursor_region_left
    assert updated.cursor_region_right == original.cursor_region_right
    assert updated.left_pinch_activation_ratio == 0.22


@pytest.mark.parametrize(
    "settings, message",
    [
        (DashboardSettings(5, 0, 1.0, "any"), "scroll speed"),
        (DashboardSettings(5, 3, 3.1, "any"), "sensitivity"),
        (DashboardSettings(5, 3, 1.0, "upper"), "dominant hand"),
    ],
)
def test_dashboard_settings_are_validated(
    settings: DashboardSettings, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        settings.apply(AppConfig())


def test_missing_profile_loads_defaults_without_writing(local_tmp_path: Path) -> None:
    path = local_tmp_path / "settings.json"
    config, existed = load_dashboard_profile(path)
    assert not existed
    assert config == AppConfig()
    assert not path.exists()


def test_dashboard_save_is_atomic_profile_path(local_tmp_path: Path) -> None:
    path = local_tmp_path / "settings.json"
    updated = save_dashboard_profile(
        path, AppConfig(), DashboardSettings(8, 4, 1.3, "right")
    )
    assert load_config(path) == updated
