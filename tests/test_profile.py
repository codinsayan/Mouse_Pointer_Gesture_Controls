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
