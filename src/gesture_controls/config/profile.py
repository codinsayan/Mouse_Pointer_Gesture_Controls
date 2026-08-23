"""Strict versioned local JSON settings profiles."""

from __future__ import annotations

from dataclasses import fields, replace
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from gesture_controls.errors import ConfigurationError

from .settings import AppConfig

PROFILE_SCHEMA_VERSION = 1
PROFILE_ROOT_KEYS = frozenset({"schema_version", "settings"})


def _field_defaults() -> dict[str, Any]:
    defaults = AppConfig()
    return {field.name: getattr(defaults, field.name) for field in fields(defaults)}


def _coerce_setting(name: str, value: Any, default: Any) -> Any:
    if isinstance(default, Path):
        if not isinstance(value, str):
            raise ConfigurationError(f"setting '{name}' must be a string path")
        return Path(value)
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise ConfigurationError(f"setting '{name}' must be a boolean")
        return value
    if isinstance(default, int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigurationError(f"setting '{name}' must be an integer")
        return value
    if isinstance(default, float):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigurationError(f"setting '{name}' must be a number")
        return float(value)
    if isinstance(default, str):
        if not isinstance(value, str):
            raise ConfigurationError(f"setting '{name}' must be a string")
        return value
    raise ConfigurationError(f"setting '{name}' has an unsupported type")


def config_to_profile(config: AppConfig) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    for field in fields(config):
        value = getattr(config, field.name)
        settings[field.name] = str(value) if isinstance(value, Path) else value
    return {"schema_version": PROFILE_SCHEMA_VERSION, "settings": settings}


def profile_to_config(document: Any) -> AppConfig:
    if not isinstance(document, dict):
        raise ConfigurationError("settings profile root must be a JSON object")
    unknown_root = set(document) - PROFILE_ROOT_KEYS
    if unknown_root:
        names = ", ".join(sorted(unknown_root))
        raise ConfigurationError(f"unknown profile field(s): {names}")
    if document.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ConfigurationError(
            f"unsupported settings schema version; expected {PROFILE_SCHEMA_VERSION}"
        )
    raw_settings = document.get("settings")
    if not isinstance(raw_settings, dict):
        raise ConfigurationError("profile 'settings' must be a JSON object")
    defaults = _field_defaults()
    unknown_settings = set(raw_settings) - set(defaults)
    if unknown_settings:
        names = ", ".join(sorted(unknown_settings))
        raise ConfigurationError(f"unknown setting(s): {names}")
    values = {
        name: _coerce_setting(name, value, defaults[name])
        for name, value in raw_settings.items()
    }
    try:
        return AppConfig(**values)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"invalid settings profile: {exc}") from exc


def load_config(path: Path) -> AppConfig:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"settings profile not found: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"could not read settings profile: {exc}") from exc
    return profile_to_config(document)


def save_config(path: Path, config: AppConfig) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(config_to_profile(config), indent=2, sort_keys=True) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    except OSError as exc:
        try:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise ConfigurationError(f"could not save settings profile: {exc}") from exc


def with_overrides(
    config: AppConfig,
    *,
    camera_index: int | None = None,
    model_path: Path | None = None,
) -> AppConfig:
    changes: dict[str, Any] = {}
    if camera_index is not None:
        changes["camera_index"] = camera_index
    if model_path is not None:
        changes["model_path"] = model_path
    try:
        return replace(config, **changes)
    except ValueError as exc:
        raise ConfigurationError(f"invalid command-line override: {exc}") from exc
