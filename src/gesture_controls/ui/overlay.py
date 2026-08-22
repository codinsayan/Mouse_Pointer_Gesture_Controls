"""OpenCV landmark and status rendering."""

from __future__ import annotations

from typing import Any

from gesture_controls.controls import CursorRegion, CursorUpdate
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

    hand = "Detected" if result.hand_detected else "Not detected"
    handedness = result.handedness or "N/A"
    confidence = "N/A" if result.confidence is None else f"{result.confidence:.2f}"
    lines = (
        "Camera: Active",
        f"Hand: {hand}",
        f"Handedness: {handedness}",
        f"Confidence: {confidence}",
        f"Processed FPS: {fps:.1f}",
        "Control: DRY RUN (no OS mouse events)",
        "Cursor target: " + (
            "N/A" if cursor_update is None
            else f"{cursor_update.output_point.x:.3f}, {cursor_update.output_point.y:.3f}"
        ),
        "Press Q or Esc to quit",
    )
    for index, text in enumerate(lines):
        y = 28 + index * 25
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                    (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                    (255, 255, 255), 1, cv2.LINE_AA)
    return frame
