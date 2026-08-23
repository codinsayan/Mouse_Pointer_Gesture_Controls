"""Foreground local-only application loop."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from gesture_controls.camera import CameraCapture
from gesture_controls.config import AppConfig, save_config
from gesture_controls.controls import (
    CursorCalibrator,
    CursorPipeline,
    CursorRegion,
    DryRunMouseController,
    HotkeyAction,
    InputSafetyController,
    MouseController,
    Point2D,
    PyAutoGuiMouseController,
    RelativeDragMapper,
    WindowsGlobalHotkeys,
)
from gesture_controls.diagnostics import FpsMeter
from gesture_controls.gestures import (
    ClickCursorGuard,
    ClickGestureCoordinator,
    DragRecognizer,
    DragState,
    FistRecognizer,
    GestureAction,
    GestureCoordinator,
    OpenPalmPauseRecognizer,
    PinchRecognizer,
    PointerPoseGate,
    ScrollRecognizer,
    ZoomRecognizer,
    extract_left_pinch_features,
)
from gesture_controls.tracking import HandLandmarkerTracker, hand_matches_preference
from gesture_controls.ui import draw_overlay


def _cursor_components(
    config: AppConfig,
) -> tuple[CursorRegion, CursorPipeline, RelativeDragMapper]:
    region = CursorRegion(
        config.cursor_region_left,
        config.cursor_region_top,
        config.cursor_region_right,
        config.cursor_region_bottom,
    )
    pipeline = CursorPipeline(
        region,
        config.cursor_smoothing_seconds,
        config.cursor_minimum_movement,
        config.cursor_sensitivity,
    )
    return region, pipeline, RelativeDragMapper(region, config.cursor_sensitivity)


def run(
    config: AppConfig,
    profile_path: Path | None = None,
    profile_config: AppConfig | None = None,
    real_input_requested: bool = False,
    mouse_controller: MouseController | None = None,
    hotkey_source: Any | None = None,
) -> None:
    import cv2

    profile_config = config if profile_config is None else profile_config

    fps_meter = FpsMeter()
    cursor_region, cursor_pipeline, drag_motion = _cursor_components(config)
    calibrator = CursorCalibrator(
        config.calibration_min_samples,
        config.calibration_low_quantile,
        config.calibration_high_quantile,
        config.calibration_padding_ratio,
        config.calibration_minimum_span,
    )
    controller = mouse_controller or (
        PyAutoGuiMouseController()
        if real_input_requested
        else DryRunMouseController()
    )
    safety = InputSafetyController(controller)
    hotkeys = hotkey_source or WindowsGlobalHotkeys()
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
        FistRecognizer(
            config.fist_folded_activation_ratio,
            config.fist_folded_release_ratio,
            config.fist_activation_hold_seconds,
            config.fist_release_hold_seconds,
        ),
        DragRecognizer(config.drag_activation_hold_seconds),
        ZoomRecognizer(
            config.zoom_span_activation_ratio,
            config.zoom_span_release_ratio,
            config.zoom_other_fingers_extension_activation_ratio,
            config.zoom_other_fingers_extension_release_ratio,
            config.zoom_activation_hold_seconds,
            config.zoom_release_hold_seconds,
            config.zoom_step_distance_ratio,
            config.zoom_max_steps_per_frame,
        ),
        OpenPalmPauseRecognizer(
            config.pause_extension_activation_ratio,
            config.pause_extension_release_ratio,
            config.pause_activation_hold_seconds,
            config.pause_release_hold_seconds,
        ),
    )
    cursor_guard = ClickCursorGuard(config.post_click_cursor_resume_delay_seconds)
    pointer_pose = PointerPoseGate(
        config.pointer_extension_activation_ratio,
        config.pointer_extension_release_ratio,
    )
    dry_run_left_clicks = 0
    dry_run_double_clicks = 0
    dry_run_right_clicks = 0
    dry_run_drag_starts = 0
    dry_run_drag_ends = 0
    dry_run_zoom_in_steps = 0
    dry_run_zoom_out_steps = 0
    dry_run_scroll_up_steps = 0
    dry_run_scroll_down_steps = 0
    dry_run_scroll_left_steps = 0
    dry_run_scroll_right_steps = 0
    last_click_kind = "none"
    last_scroll_direction = "none"
    scroll_was_claiming = False
    fist_was_claiming = False
    zoom_was_claiming = False
    last_timestamp_ms = -1
    try:
        with (
            hotkeys,
            HandLandmarkerTracker(config) as tracker,
            CameraCapture(config) as camera,
        ):
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
                drag_update = None
                fist_update = None
                zoom_update = None
                pause_update = None
                pointer_pose_update = None
                hand_accepted = len(result.landmarks) >= 21 and hand_matches_preference(
                    result.handedness, config.dominant_hand
                )
                confidence_accepted = (
                    result.confidence is not None
                    and result.confidence >= config.minimum_runtime_hand_confidence
                )
                tracking_ready = hand_accepted and confidence_accepted
                hotkey_actions = hotkeys.poll()
                if HotkeyAction.EMERGENCY_PAUSE in hotkey_actions:
                    safety.emergency_pause("Global emergency pause")
                elif HotkeyAction.TOGGLE in hotkey_actions:
                    safety.toggle(tracking_ready)
                if safety.enabled and not tracking_ready:
                    reason = (
                        "Tracking lost: accepted hand unavailable"
                        if not hand_accepted
                        else "Tracking lost: confidence below safety threshold"
                    )
                    safety.tracking_lost(reason)
                if tracking_ready and not calibrator.collecting and safety.enabled:
                    index_tip = result.landmarks[8]
                    pinch_features = extract_left_pinch_features(result.landmarks)
                    pointer_pose_update = pointer_pose.update(
                        pinch_features.index_extension_ratio
                    )
                    interaction = gestures.update(pinch_features, now_seconds)
                    scroll_update = interaction.scroll
                    click_update = interaction.click
                    drag_update = interaction.drag
                    fist_update = interaction.fist
                    zoom_update = interaction.zoom
                    pause_update = interaction.pause
                    if interaction.action is GestureAction.LEFT_CLICK:
                        dry_run_left_clicks += 1
                        last_click_kind = "left (thumb-index)"
                        safety.click_left()
                    elif interaction.action is GestureAction.DOUBLE_CLICK:
                        dry_run_double_clicks += 1
                        last_click_kind = "double (thumb-middle)"
                        safety.click_left_twice()
                    elif interaction.action is GestureAction.RIGHT_CLICK:
                        dry_run_right_clicks += 1
                        last_click_kind = "right (thumb-little)"
                        safety.click_right()
                    elif interaction.action is GestureAction.DRAG_STARTED:
                        dry_run_drag_starts += 1
                        cursor_origin = cursor_pipeline.output_point
                        if cursor_origin is not None:
                            drag_motion.start(
                                Point2D(
                                    pinch_features.palm_anchor_x,
                                    pinch_features.palm_anchor_y,
                                ),
                                cursor_origin,
                            )
                            safety.begin_drag()
                    elif interaction.action is GestureAction.DRAG_ENDED:
                        dry_run_drag_ends += 1
                        drag_motion.reset()
                        safety.end_drag()
                    elif interaction.action is GestureAction.PAUSE_REQUESTED:
                        safety.pause("Open-palm pause gesture")
                        drag_motion.reset()
                    if zoom_update.steps > 0:
                        dry_run_zoom_in_steps += zoom_update.steps
                    elif zoom_update.steps < 0:
                        dry_run_zoom_out_steps += -zoom_update.steps
                    safety.zoom(zoom_update.steps)
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
                    safety.scroll_vertical(scroll_update.steps)
                    safety.scroll_horizontal(scroll_update.horizontal_steps)
                    if (
                        scroll_update.claims_frame
                        or fist_update.claims_frame
                        or zoom_update.claims_frame
                        or pause_update.claims_frame
                    ):
                        cursor_guard.reset()
                        freeze_cursor = interaction.cursor_should_freeze
                    else:
                        if (
                            scroll_was_claiming
                            or fist_was_claiming
                            or zoom_was_claiming
                        ):
                            cursor_pipeline.resume_from_frozen_output(now_seconds)
                        assert click_update is not None
                        if interaction.action is GestureAction.DRAG_STARTED:
                            cursor_pipeline.resume_from_frozen_output(now_seconds)
                        if drag_update.state is DragState.DRAGGING:
                            cursor_guard.reset()
                            freeze_cursor = False
                        else:
                            guard = cursor_guard.update(
                                click_update.selected, now_seconds
                            )
                            if guard.resume_smoothing:
                                cursor_pipeline.resume_from_frozen_output(now_seconds)
                            freeze_cursor = guard.freeze or not pointer_pose_update.active
                    camera_point = Point2D(index_tip.x, index_tip.y)
                    mapped_drag_target = None
                    if drag_update.state is DragState.DRAGGING:
                        camera_point = Point2D(
                            pinch_features.palm_anchor_x,
                            pinch_features.palm_anchor_y,
                        )
                        mapped_drag_target = drag_motion.update(camera_point)
                    cursor_update = cursor_pipeline.update(
                        camera_point,
                        now_seconds,
                        freeze=freeze_cursor,
                        minimum_movement_override=(
                            config.drag_cursor_minimum_movement
                            if drag_update.state is DragState.DRAGGING
                            else None
                        ),
                        mapped_point_override=mapped_drag_target,
                    )
                    if cursor_update.moved and not cursor_update.frozen:
                        safety.move_to(cursor_update.output_point)
                    scroll_was_claiming = scroll_update.claims_frame
                    fist_was_claiming = fist_update.claims_frame
                    zoom_was_claiming = zoom_update.claims_frame
                elif tracking_ready and calibrator.collecting:
                    index_tip = result.landmarks[8]
                    calibration_point = Point2D(index_tip.x, index_tip.y)
                    calibrator.add(calibration_point)
                    gestures.reset(now_seconds)
                    pointer_pose.reset()
                    cursor_guard.reset()
                    drag_motion.reset()
                    scroll_was_claiming = False
                    fist_was_claiming = False
                    zoom_was_claiming = False
                    cursor_update = cursor_pipeline.update(
                        calibration_point, now_seconds, freeze=True
                    )
                else:
                    cursor_pipeline.reset()
                    if gestures.reset(now_seconds) is GestureAction.DRAG_ENDED:
                        dry_run_drag_ends += 1
                        safety.end_drag()
                    pointer_pose.reset()
                    cursor_guard.reset()
                    drag_motion.reset()
                    scroll_was_claiming = False
                    fist_was_claiming = False
                    zoom_was_claiming = False
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
                        drag_update,
                        dry_run_drag_starts,
                        dry_run_drag_ends,
                        fist_update,
                        zoom_update,
                        dry_run_zoom_in_steps,
                        dry_run_zoom_out_steps,
                        config.dominant_hand,
                        hand_accepted,
                        calibrator.status,
                        profile_path is not None,
                        safety.status,
                        hotkeys.available,
                        pause_update,
                        pointer_pose_update,
                    ),
                )
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("e"), ord("E")):
                    safety.toggle(tracking_ready)
                    if not safety.enabled:
                        if gestures.reset(now_seconds) is GestureAction.DRAG_ENDED:
                            dry_run_drag_ends += 1
                        cursor_pipeline.reset()
                        cursor_guard.reset()
                        drag_motion.reset()
                        pointer_pose.reset()
                    continue
                if key in (ord("p"), ord("P")):
                    safety.emergency_pause("Foreground emergency pause")
                    if gestures.reset(now_seconds) is GestureAction.DRAG_ENDED:
                        dry_run_drag_ends += 1
                    cursor_pipeline.reset()
                    cursor_guard.reset()
                    drag_motion.reset()
                    pointer_pose.reset()
                    continue
                if key in (ord("c"), ord("C")):
                    safety.pause("Calibration mode")
                    gestures.reset(now_seconds)
                    pointer_pose.reset()
                    cursor_guard.reset()
                    drag_motion.reset()
                    cursor_pipeline.reset()
                    calibrator.start()
                    scroll_was_claiming = False
                    fist_was_claiming = False
                    zoom_was_claiming = False
                    continue
                if key in (ord("x"), ord("X")) and calibrator.collecting:
                    calibrator.cancel()
                    cursor_pipeline.reset()
                    continue
                if key in (10, 13) and calibrator.collecting:
                    calibrated_region = calibrator.finish()
                    if calibrated_region is not None:
                        config = replace(
                            config,
                            cursor_region_left=calibrated_region.left,
                            cursor_region_top=calibrated_region.top,
                            cursor_region_right=calibrated_region.right,
                            cursor_region_bottom=calibrated_region.bottom,
                        )
                        cursor_region, cursor_pipeline, drag_motion = (
                            _cursor_components(config)
                        )
                        if profile_path is not None:
                            profile_config = replace(
                                profile_config,
                                cursor_region_left=calibrated_region.left,
                                cursor_region_top=calibrated_region.top,
                                cursor_region_right=calibrated_region.right,
                                cursor_region_bottom=calibrated_region.bottom,
                            )
                            save_config(profile_path, profile_config)
                    continue
                if key in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(config.window_title, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        gestures.reset(perf_counter_ns() / 1_000_000_000)
        safety.shutdown()
        cv2.destroyAllWindows()
