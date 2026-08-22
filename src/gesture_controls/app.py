"""Foreground Iteration 1 application loop."""

from __future__ import annotations

from time import perf_counter_ns

from gesture_controls.camera import CameraCapture
from gesture_controls.config import AppConfig
from gesture_controls.controls import CursorPipeline, CursorRegion, Point2D
from gesture_controls.diagnostics import FpsMeter
from gesture_controls.tracking import HandLandmarkerTracker
from gesture_controls.ui import draw_overlay


def run(config: AppConfig) -> None:
    import cv2

    fps_meter = FpsMeter()
    cursor_region = CursorRegion(
        config.cursor_region_left,
        config.cursor_region_top,
        config.cursor_region_right,
        config.cursor_region_bottom,
    )
    cursor_pipeline = CursorPipeline(
        cursor_region,
        config.cursor_smoothing_seconds,
        config.cursor_minimum_movement,
    )
    last_timestamp_ms = -1
    try:
        with HandLandmarkerTracker(config) as tracker, CameraCapture(config) as camera:
            while True:
                frame = cv2.flip(camera.read(), 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp_ms = perf_counter_ns() // 1_000_000
                timestamp_ms = max(timestamp_ms, last_timestamp_ms + 1)
                last_timestamp_ms = timestamp_ms
                result = tracker.detect(rgb_frame, timestamp_ms)
                now_seconds = perf_counter_ns() / 1_000_000_000
                cursor_update = None
                if len(result.landmarks) > 8:
                    index_tip = result.landmarks[8]
                    cursor_update = cursor_pipeline.update(
                        Point2D(index_tip.x, index_tip.y), now_seconds
                    )
                else:
                    cursor_pipeline.reset()
                fps = fps_meter.update(now_seconds)
                cv2.imshow(
                    config.window_title,
                    draw_overlay(frame, result, fps, cursor_update, cursor_region),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(config.window_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        cv2.destroyAllWindows()
