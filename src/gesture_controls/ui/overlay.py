"""OpenCV landmark and status rendering."""

from __future__ import annotations

from typing import Any

from gesture_controls.controls import CalibrationStatus, CursorRegion, CursorUpdate
from gesture_controls.gestures import (
    ClickGestureUpdate,
    DragState,
    DragUpdate,
    FistUpdate,
    PinchState,
    ScrollUpdate,
    ZoomState,
    ZoomUpdate,
)
from gesture_controls.tracking import TrackingResult

HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


def landmark_to_pixel(x: float, y: float, width: int, height: int) -> tuple[int, int]:
    """Convert normalized coordinates while clamping to image bounds."""
    px = min(width - 1, max(0, round(x * (width - 1))))
    py = min(height - 1, max(0, round(y * (height - 1))))
    return px, py


def draw_overlay(
    frame: Any,
    result: TrackingResult,
    fps: float,
    cursor_update: CursorUpdate | None = None,
    cursor_region: CursorRegion | None = None,
    click_update: ClickGestureUpdate | None = None,
    dry_run_left_clicks: int = 0,
    dry_run_double_clicks: int = 0,
    dry_run_right_clicks: int = 0,
    last_click_kind: str = "none",
    scroll_update: ScrollUpdate | None = None,
    dry_run_scroll_up_steps: int = 0,
    dry_run_scroll_down_steps: int = 0,
    dry_run_scroll_left_steps: int = 0,
    dry_run_scroll_right_steps: int = 0,
    last_scroll_direction: str = "none",
    drag_update: DragUpdate | None = None,
    dry_run_drag_starts: int = 0,
    dry_run_drag_ends: int = 0,
    fist_update: FistUpdate | None = None,
    zoom_update: ZoomUpdate | None = None,
    dry_run_zoom_in_steps: int = 0,
    dry_run_zoom_out_steps: int = 0,
    dominant_hand: str = "any",
    hand_accepted: bool = True,
    calibration_status: CalibrationStatus | None = None,
    calibration_persistence_enabled: bool = False,
) -> Any:
    import cv2

    height, width = frame.shape[:2]
    pixels = [landmark_to_pixel(p.x, p.y, width, height) for p in result.landmarks]
    for start, end in HAND_CONNECTIONS:
        if start < len(pixels) and end < len(pixels):
            cv2.line(frame, pixels[start], pixels[end], (60, 210, 255), 2, cv2.LINE_AA)
    for point in pixels:
        cv2.circle(frame, point, 4, (40, 255, 80), -1, cv2.LINE_AA)

    if cursor_region is not None:
        top_left = landmark_to_pixel(cursor_region.left, cursor_region.top, width, height)
        bottom_right = landmark_to_pixel(cursor_region.right, cursor_region.bottom, width, height)
        cv2.rectangle(frame, top_left, bottom_right, (255, 180, 50), 1, cv2.LINE_AA)
    if cursor_update is not None:
        target = landmark_to_pixel(cursor_update.output_point.x, cursor_update.output_point.y, width, height)
        cv2.drawMarker(frame, target, (255, 80, 255), cv2.MARKER_CROSS, 18, 2, cv2.LINE_AA)
    if len(pixels) > 20:
        left_color = (
            (0, 80, 255)
            if click_update is not None
            and click_update.left.state is PinchState.ACTIVE
            else (180, 180, 180)
        )
        double_color = (
            (255, 80, 0)
            if click_update is not None
            and click_update.double.state is PinchState.ACTIVE
            else (180, 180, 180)
        )
        right_color = (
            (80, 255, 255)
            if click_update is not None
            and click_update.right.state is PinchState.ACTIVE
            else (180, 180, 180)
        )
        zoom_color = (
            (180, 80, 255)
            if zoom_update is not None
            and zoom_update.state is ZoomState.ACTIVE
            else (180, 180, 180)
        )
        cv2.line(frame, pixels[4], pixels[8], left_color, 3, cv2.LINE_AA)
        cv2.line(frame, pixels[4], pixels[12], double_color, 3, cv2.LINE_AA)
        cv2.line(frame, pixels[4], pixels[20], right_color, 3, cv2.LINE_AA)
        cv2.line(frame, pixels[4], pixels[16], zoom_color, 3, cv2.LINE_AA)

    hand = (
        "Detected"
        if result.hand_detected and hand_accepted
        else ("Ignored by preference" if result.hand_detected else "Not detected")
    )
    handedness = result.handedness or "N/A"
    confidence = "N/A" if result.confidence is None else f"{result.confidence:.2f}"
    lines = (
        "Camera: Active",
        f"Hand: {hand}",
        f"Handedness: {handedness}",
        f"Preferred hand: {dominant_hand}",
        f"Confidence: {confidence}",
        f"Processed FPS: {fps:.1f}",
        "Control: DRY RUN (no OS mouse events)",
        "Cursor target: " + (
            "N/A" if cursor_update is None
            else f"{cursor_update.output_point.x:.3f}, {cursor_update.output_point.y:.3f}"
        ),
        "Cursor: " + (
            "N/A" if cursor_update is None
            else ("FROZEN" if cursor_update.frozen else "tracking")
        ),
        "Left pinch: " + (
            "N/A" if click_update is None
            else f"{click_update.left.state.value} ({click_update.left.ratio:.3f})"
        ),
        "Double pinch: " + (
            "N/A" if click_update is None
            else f"{click_update.double.state.value} ({click_update.double.ratio:.3f})"
        ),
        "Right pinch: " + (
            "N/A" if click_update is None
            else f"{click_update.right.state.value} ({click_update.right.ratio:.3f})"
        ),
        "Fist: " + (
            "N/A" if fist_update is None
            else f"{fist_update.state.value} "
            f"(max extension {fist_update.maximum_extension_ratio:.3f})"
        ),
        "Drag: " + (
            "N/A" if drag_update is None else drag_update.state.value
        ),
        f"Dry-run drags: start {dry_run_drag_starts} / end {dry_run_drag_ends}",
        "Zoom: " + (
            "N/A" if zoom_update is None
            else f"{zoom_update.state.value} ({zoom_update.span_ratio:.3f})"
        ),
        "Dry-run zoom steps: "
        f"in {dry_run_zoom_in_steps} / out {dry_run_zoom_out_steps}",
        f"Dry-run left clicks: {dry_run_left_clicks}",
        f"Dry-run double clicks: {dry_run_double_clicks}",
        f"Dry-run right clicks: {dry_run_right_clicks}",
        f"Last click: {last_click_kind}",
        "Scroll: " + (
            "N/A" if scroll_update is None
            else f"{scroll_update.state.value} ({scroll_update.axis.value})"
        ),
        "Vertical scroll steps: "
        f"up {dry_run_scroll_up_steps} / down {dry_run_scroll_down_steps}",
        "Horizontal scroll steps: "
        f"left {dry_run_scroll_left_steps} / right {dry_run_scroll_right_steps}",
        f"Last scroll: {last_scroll_direction}",
        "Calibration: " + (
            "N/A"
            if calibration_status is None
            else f"{calibration_status.state.value} "
            f"({calibration_status.sample_count}) {calibration_status.message}"
        ),
        "Calibration persistence: "
        + ("selected profile" if calibration_persistence_enabled else "session only"),
        "Calibration keys: C start / Enter apply / X cancel",
        "Press Q or Esc to quit",
    )
    for index, text in enumerate(lines):
        y = 17 + index * 15
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.39,
                    (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.39,
                    (255, 255, 255), 1, cv2.LINE_AA)
    return frame
