"""Foreground local-only application loop."""

from __future__ import annotations

from time import perf_counter_ns

from gesture_controls.camera import CameraCapture
from gesture_controls.config import AppConfig
from gesture_controls.controls import CursorPipeline, CursorRegion, Point2D
from gesture_controls.diagnostics import FpsMeter
from gesture_controls.gestures import (
    ClickAction,
    ClickCursorGuard,
    ClickGestureCoordinator,
    PinchRecognizer,
    extract_left_pinch_features,
)
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
    click_gestures = ClickGestureCoordinator(
        PinchRecognizer(
            config.left_pinch_activation_ratio,
            config.left_pinch_release_ratio,
            config.left_pinch_activation_hold_seconds,
            config.left_pinch_release_hold_seconds,
            config.left_click_cooldown_seconds,
        ),
        PinchRecognizer(
            config.double_click_pinch_activation_ratio,
            config.double_click_pinch_release_ratio,
            config.double_click_activation_hold_seconds,
            config.double_click_release_hold_seconds,
            config.double_click_cooldown_seconds,
        ),
    )
    cursor_guard = ClickCursorGuard(config.post_click_cursor_resume_delay_seconds)
    dry_run_left_clicks = 0
    dry_run_double_clicks = 0
    last_click_kind = "none"
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
                click_update = None
                if len(result.landmarks) >= 21:
                    index_tip = result.landmarks[8]
                    pinch_features = extract_left_pinch_features(result.landmarks)
                    click_update = click_gestures.update(
                        pinch_features.left_pinch_ratio,
                        pinch_features.double_click_pinch_ratio,
                        now_seconds,
                    )
                    if click_update.action is ClickAction.LEFT_CLICK:
                        dry_run_left_clicks += 1
                        last_click_kind = "left (thumb-index)"
                    elif click_update.action is ClickAction.DOUBLE_CLICK:
                        dry_run_double_clicks += 1
                        last_click_kind = "double (thumb-middle)"
                    guard = cursor_guard.update(click_update.selected, now_seconds)
                    if guard.resume_smoothing:
                        cursor_pipeline.resume_from_frozen_output(now_seconds)
                    cursor_update = cursor_pipeline.update(
                        Point2D(index_tip.x, index_tip.y),
                        now_seconds,
                        freeze=guard.freeze,
                    )
                else:
                    cursor_pipeline.reset()
                    click_gestures.reset(now_seconds)
                    cursor_guard.reset()
                fps = fps_meter.update(now_seconds)
                cv2.imshow(
                    config.window_title,
                    draw_overlay(
                        frame,
                        result,
                        fps,
                        cursor_update,
                        cursor_region,
                        click_update,
                        dry_run_left_clicks,
                        dry_run_double_clicks,
                        last_click_kind,
                    ),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(config.window_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        cv2.destroyAllWindows()
