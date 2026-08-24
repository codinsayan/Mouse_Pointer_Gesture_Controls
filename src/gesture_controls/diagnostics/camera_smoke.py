"""One-frame local camera/tracker smoke check with no preview or OS input."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable, Sequence

from gesture_controls.camera import CameraCapture
from gesture_controls.config import AppConfig, load_config
from gesture_controls.errors import GestureControlsError
from gesture_controls.tracking import HandLandmarkerTracker


@dataclass(frozen=True, slots=True)
class CameraSmokeResult:
    frame_width: int
    frame_height: int
    hand_detected: bool
    handedness: str | None
    confidence: float | None
    elapsed_milliseconds: float


def run_camera_smoke(
    config: AppConfig,
    *,
    camera_factory: Callable[[AppConfig], Any] = CameraCapture,
    tracker_factory: Callable[[AppConfig], Any] = HandLandmarkerTracker,
    cv2_module: Any | None = None,
    clock_ns: Callable[[], int] = perf_counter_ns,
) -> CameraSmokeResult:
    """Capture and infer exactly one volatile frame, returning metadata only."""
    if cv2_module is None:
        import cv2 as cv2_module

    started_ns = clock_ns()
    with tracker_factory(config) as tracker, camera_factory(config) as camera:
        frame = cv2_module.flip(camera.read(), 1)
        rgb_frame = cv2_module.cvtColor(frame, cv2_module.COLOR_BGR2RGB)
        result = tracker.detect(rgb_frame, clock_ns() // 1_000_000)
    elapsed_ms = (clock_ns() - started_ns) / 1_000_000
    height, width = frame.shape[:2]
    return CameraSmokeResult(
        frame_width=width,
        frame_height=height,
        hand_detected=result.hand_detected,
        handedness=result.handedness,
        confidence=result.confidence,
        elapsed_milliseconds=round(elapsed_ms, 2),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture and infer one local frame without preview or OS input"
    )
    parser.add_argument("--config", type=Path, help="optional local JSON profile")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config) if args.config else AppConfig()
        print(json.dumps(asdict(run_camera_smoke(config)), sort_keys=True))
    except GestureControlsError as exc:
        logging.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
