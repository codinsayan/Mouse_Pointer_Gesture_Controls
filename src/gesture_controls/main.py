"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from gesture_controls.app import run
from gesture_controls.config import (
    AppConfig,
    load_config,
    save_config,
    with_overrides,
)
from gesture_controls.errors import GestureControlsError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local webcam hand-landmark preview")
    parser.add_argument("--camera", type=int, help="override OpenCV camera index")
    parser.add_argument(
        "--model",
        type=Path,
        help="override path to the official MediaPipe Hand Landmarker .task model",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="load a local JSON settings profile; applied calibration is saved here",
    )
    parser.add_argument(
        "--write-default-config",
        type=Path,
        help="write a validated default JSON profile and exit",
    )
    parser.add_argument(
        "--enable-real-input",
        action="store_true",
        help=(
            "allow the PyAutoGUI controller for this run; control still starts "
            "disabled and requires an explicit enable shortcut"
        ),
    )
    return parser


def resolve_config(
    args: argparse.Namespace, base_config: AppConfig | None = None
) -> AppConfig:
    config = (
        base_config
        if base_config is not None
        else (load_config(args.config) if args.config is not None else AppConfig())
    )
    return with_overrides(
        config, camera_index=args.camera, model_path=args.model
    )


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        if args.write_default_config is not None:
            save_config(args.write_default_config, AppConfig())
            logging.info("Default settings written to %s", args.write_default_config)
            return 0
        profile_config = (
            load_config(args.config) if args.config is not None else AppConfig()
        )
        run(
            resolve_config(args, profile_config),
            profile_path=args.config,
            profile_config=profile_config,
            real_input_requested=args.enable_real_input,
        )
    except GestureControlsError as exc:
        logging.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
