import json
from pathlib import Path

import pytest

from gesture_controls.config import (
    AppConfig,
    PROFILE_SCHEMA_VERSION,
    config_to_profile,
    load_config,
    profile_to_config,
    save_config,
    with_overrides,
)
from gesture_controls.errors import ConfigurationError
from gesture_controls.main import build_parser, main, resolve_config


def test_profile_round_trip_preserves_paths_and_settings(local_tmp_path: Path) -> None:
    original = AppConfig(
        camera_index=2,
        model_path=Path("models/custom.task"),
        dominant_hand="left",
        cursor_sensitivity=1.4,
        cursor_smoothing_seconds=0.12,
    )
    path = local_tmp_path / "settings.json"
    save_config(path, original)
    assert load_config(path) == original
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == PROFILE_SCHEMA_VERSION
    assert document["settings"]["model_path"] == str(Path("models/custom.task"))


def test_profile_can_contain_partial_settings() -> None:
    config = profile_to_config(
        {"schema_version": PROFILE_SCHEMA_VERSION, "settings": {"camera_index": 3}}
    )
    assert config.camera_index == 3
    assert config.cursor_sensitivity == AppConfig().cursor_sensitivity


@pytest.mark.parametrize(
    "document, message",
    [
        ([], "root"),
        ({"schema_version": 99, "settings": {}}, "schema version"),
        (
            {"schema_version": PROFILE_SCHEMA_VERSION, "settings": {}, "extra": 1},
            "unknown profile",
        ),
        (
            {"schema_version": PROFILE_SCHEMA_VERSION, "settings": {"mystery": 1}},
            "unknown setting",
        ),
        (
            {"schema_version": PROFILE_SCHEMA_VERSION, "settings": []},
            "settings",
        ),
        (
            {
                "schema_version": PROFILE_SCHEMA_VERSION,
                "settings": {"camera_index": True},
            },
            "integer",
        ),
        (
            {
                "schema_version": PROFILE_SCHEMA_VERSION,
                "settings": {"dominant_hand": "up"},
            },
            "dominant_hand",
        ),
    ],
)
def test_invalid_profiles_are_rejected(document: object, message: str) -> None:
    with pytest.raises(ConfigurationError, match=message):
        profile_to_config(document)


def test_missing_and_malformed_profile_errors_are_user_facing(
    local_tmp_path: Path,
) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(local_tmp_path / "missing.json")
    malformed = local_tmp_path / "bad.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="could not read"):
        load_config(malformed)


def test_explicit_cli_overrides_win_over_profile_values(local_tmp_path: Path) -> None:
    path = local_tmp_path / "settings.json"
    save_config(path, AppConfig(camera_index=2, model_path=Path("profile.task")))
    args = build_parser().parse_args(
        ["--config", str(path), "--camera", "4", "--model", "cli.task"]
    )
    resolved = resolve_config(args)
    assert resolved.camera_index == 4
    assert resolved.model_path == Path("cli.task")

    unchanged = with_overrides(load_config(path))
    assert unchanged.camera_index == 2
    assert unchanged.model_path == Path("profile.task")


def test_write_default_config_command_does_not_start_camera(
    local_tmp_path: Path,
) -> None:
    path = local_tmp_path / "nested" / "defaults.json"
    assert main(["--write-default-config", str(path)]) == 0
    assert load_config(path) == AppConfig()
    assert config_to_profile(AppConfig())["schema_version"] == PROFILE_SCHEMA_VERSION


def test_real_input_cli_flag_is_explicit_and_not_a_profile_setting() -> None:
    assert not build_parser().parse_args([]).enable_real_input
    assert build_parser().parse_args(["--enable-real-input"]).enable_real_input
    assert "enable_real_input" not in config_to_profile(AppConfig())["settings"]


def test_settings_ui_cli_flag_is_explicit() -> None:
    assert not build_parser().parse_args([]).settings_ui
    assert build_parser().parse_args(["--settings-ui"]).settings_ui


def test_settings_ui_rejects_cli_real_input_bypass() -> None:
    assert main(["--settings-ui", "--enable-real-input"]) == 1


def test_legacy_open_palm_settings_are_ignored_and_removed_on_save(
    local_tmp_path: Path,
) -> None:
    document = config_to_profile(AppConfig())
    document["settings"].update(
        {
            "pause_extension_activation_ratio": 0.18,
            "pause_extension_release_ratio": 0.10,
            "pause_activation_hold_seconds": 0.35,
            "pause_release_hold_seconds": 0.05,
        }
    )
    legacy_path = local_tmp_path / "legacy.json"
    legacy_path.write_text(json.dumps(document), encoding="utf-8")

    loaded = load_config(legacy_path)
    save_config(legacy_path, loaded)
    saved_settings = json.loads(legacy_path.read_text(encoding="utf-8"))["settings"]

    assert loaded == AppConfig()
    assert not any(name.startswith("pause_") for name in saved_settings)


def test_legacy_zoom_settings_are_ignored_and_removed_on_save(
    local_tmp_path: Path,
) -> None:
    document = config_to_profile(AppConfig())
    document["settings"].update(
        {
            "zoom_span_activation_ratio": 0.45,
            "zoom_span_release_ratio": 0.85,
            "zoom_other_fingers_extension_activation_ratio": 0.12,
            "zoom_other_fingers_extension_release_ratio": 0.08,
            "zoom_activation_hold_seconds": 0.06,
            "zoom_release_hold_seconds": 0.05,
            "zoom_step_distance_ratio": 0.08,
            "zoom_max_steps_per_frame": 3,
        }
    )
    legacy_path = local_tmp_path / "legacy-zoom.json"
    legacy_path.write_text(json.dumps(document), encoding="utf-8")

    loaded = load_config(legacy_path)
    save_config(legacy_path, loaded)
    saved_settings = json.loads(legacy_path.read_text(encoding="utf-8"))["settings"]

    assert loaded == AppConfig()
    assert not any(name.startswith("zoom_") for name in saved_settings)
