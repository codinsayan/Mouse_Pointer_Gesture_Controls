"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from gesture_controls.app import run
from gesture_controls.config import AppConfig
from gesture_controls.errors import GestureControlsError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local webcam hand-landmark preview")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index")
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("assets/models/hand_landmarker.task"),
        help="path to the official MediaPipe Hand Landmarker .task model",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        run(AppConfig(camera_index=args.camera, model_path=args.model))
    except GestureControlsError as exc:
        logging.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

