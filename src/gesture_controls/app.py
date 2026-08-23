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
    GestureCoordinator,
    PinchRecognizer,
    ScrollRecognizer,
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
    scroll_gesture = ScrollRecognizer(
        config.scroll_extension_activation_ratio,
        config.scroll_extension_release_ratio,
        config.scroll_folded_activation_ratio,
        config.scroll_folded_release_ratio,
        config.scroll_activation_hold_seconds,
        config.scroll_release_hold_seconds,
        config.scroll_step_distance_ratio,
        config.scroll_max_steps_per_frame,
    )
    gestures = GestureCoordinator(
        scroll_gesture,
        ClickGestureCoordinator(
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
            PinchRecognizer(
                config.right_pinch_activation_ratio,
                config.right_pinch_release_ratio,
                config.right_click_activation_hold_seconds,
                config.right_click_release_hold_seconds,
                config.right_click_cooldown_seconds,
            ),
        ),
    )
    cursor_guard = ClickCursorGuard(config.post_click_cursor_resume_delay_seconds)
    dry_run_left_clicks = 0
    dry_run_double_clicks = 0
    dry_run_right_clicks = 0
    dry_run_scroll_up_steps = 0
    dry_run_scroll_down_steps = 0
    dry_run_scroll_left_steps = 0
    dry_run_scroll_right_steps = 0
    last_click_kind = "none"
    last_scroll_direction = "none"
    scroll_was_claiming = False
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
                scroll_update = None
                if len(result.landmarks) >= 21:
                    index_tip = result.landmarks[8]
                    pinch_features = extract_left_pinch_features(result.landmarks)
                    interaction = gestures.update(pinch_features, now_seconds)
                    scroll_update = interaction.scroll
                    click_update = interaction.click
                    if scroll_update.steps > 0:
                        dry_run_scroll_up_steps += scroll_update.steps
                        last_scroll_direction = "up"
                    elif scroll_update.steps < 0:
                        dry_run_scroll_down_steps += -scroll_update.steps
                        last_scroll_direction = "down"
                    if scroll_update.horizontal_steps > 0:
                        dry_run_scroll_right_steps += scroll_update.horizontal_steps
                        last_scroll_direction = "right"
                    elif scroll_update.horizontal_steps < 0:
                        dry_run_scroll_left_steps += -scroll_update.horizontal_steps
                        last_scroll_direction = "left"
                    if scroll_update.claims_frame:
                        cursor_guard.reset()
                        freeze_cursor = True
                    else:
                        if scroll_was_claiming:
                            cursor_pipeline.resume_from_frozen_output(now_seconds)
                        assert click_update is not None
                        if click_update.action is ClickAction.LEFT_CLICK:
                            dry_run_left_clicks += 1
                            last_click_kind = "left (thumb-index)"
                        elif click_update.action is ClickAction.DOUBLE_CLICK:
                            dry_run_double_clicks += 1
                            last_click_kind = "double (thumb-middle)"
                        elif click_update.action is ClickAction.RIGHT_CLICK:
                            dry_run_right_clicks += 1
                            last_click_kind = "right (thumb-little)"
                        guard = cursor_guard.update(click_update.selected, now_seconds)
                        if guard.resume_smoothing:
                            cursor_pipeline.resume_from_frozen_output(now_seconds)
                        freeze_cursor = guard.freeze
                    cursor_update = cursor_pipeline.update(
                        Point2D(index_tip.x, index_tip.y),
                        now_seconds,
                        freeze=freeze_cursor,
                    )
                    scroll_was_claiming = scroll_update.claims_frame
                else:
                    cursor_pipeline.reset()
                    gestures.reset(now_seconds)
                    cursor_guard.reset()
                    scroll_was_claiming = False
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
                        dry_run_right_clicks,
                        last_click_kind,
                        scroll_update,
                        dry_run_scroll_up_steps,
                        dry_run_scroll_down_steps,
                        dry_run_scroll_left_steps,
                        dry_run_scroll_right_steps,
                        last_scroll_direction,
                    ),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(config.window_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        cv2.destroyAllWindows()
