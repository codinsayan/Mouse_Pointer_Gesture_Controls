"""Scale-independent feature extraction from neutral landmarks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from gesture_controls.tracking.landmarks import Landmark, normalized_distance

WRIST = 0
THUMB_TIP = 4
INDEX_FINGER_MCP = 5
INDEX_FINGER_PIP = 6
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_MCP = 9
MIDDLE_FINGER_PIP = 10
MIDDLE_FINGER_TIP = 12
RING_FINGER_MCP = 13
RING_FINGER_PIP = 14
RING_FINGER_TIP = 16
LITTLE_FINGER_MCP = 17
LITTLE_FINGER_PIP = 18
LITTLE_FINGER_TIP = 20
REQUIRED_LANDMARK_COUNT = 21


@dataclass(frozen=True, slots=True)
class PinchFeatures:
    left_pinch_ratio: float
    double_click_pinch_ratio: float
    right_pinch_ratio: float
    hand_size: float
    index_extension_ratio: float
    middle_extension_ratio: float
    ring_extension_ratio: float
    little_extension_ratio: float
    palm_anchor_y: float
    palm_anchor_x: float


def _require_complete_hand(landmarks: Sequence[Landmark]) -> None:
    if len(landmarks) < REQUIRED_LANDMARK_COUNT:
        raise ValueError(f"expected at least {REQUIRED_LANDMARK_COUNT} hand landmarks")


def reference_hand_size(landmarks: Sequence[Landmark]) -> float:
    """Return a palm-scale reference independent of image pixel dimensions."""
    _require_complete_hand(landmarks)
    palm_length = normalized_distance(landmarks[WRIST], landmarks[MIDDLE_FINGER_MCP])
    palm_width = normalized_distance(
        landmarks[INDEX_FINGER_MCP], landmarks[LITTLE_FINGER_MCP]
    )
    hand_size = max(palm_length, palm_width)
    if hand_size <= 1e-9:
        raise ValueError("hand-size reference is degenerate")
    return hand_size


def _finger_extension_ratio(
    landmarks: Sequence[Landmark], tip: int, pip: int, hand_size: float
) -> float:
    """Measure fingertip extension beyond its PIP joint relative to palm scale."""
    return (
        normalized_distance(landmarks[WRIST], landmarks[tip])
        - normalized_distance(landmarks[WRIST], landmarks[pip])
    ) / hand_size


def _palm_anchor(landmarks: Sequence[Landmark]) -> tuple[float, float]:
    indices = (WRIST, INDEX_FINGER_MCP, MIDDLE_FINGER_MCP, RING_FINGER_MCP,
               LITTLE_FINGER_MCP)
    count = len(indices)
    return (
        sum(landmarks[index].x for index in indices) / count,
        sum(landmarks[index].y for index in indices) / count,
    )


def extract_left_pinch_features(landmarks: Sequence[Landmark]) -> PinchFeatures:
    hand_size = reference_hand_size(landmarks)
    palm_anchor_x, palm_anchor_y = _palm_anchor(landmarks)
    pinch_distance = normalized_distance(
        landmarks[THUMB_TIP], landmarks[INDEX_FINGER_TIP]
    )
    double_click_distance = normalized_distance(
        landmarks[THUMB_TIP], landmarks[MIDDLE_FINGER_TIP]
    )
    right_click_distance = normalized_distance(
        landmarks[THUMB_TIP], landmarks[LITTLE_FINGER_TIP]
    )
    return PinchFeatures(
        pinch_distance / hand_size,
        double_click_distance / hand_size,
        right_click_distance / hand_size,
        hand_size,
        _finger_extension_ratio(
            landmarks, INDEX_FINGER_TIP, INDEX_FINGER_PIP, hand_size
        ),
        _finger_extension_ratio(
            landmarks, MIDDLE_FINGER_TIP, MIDDLE_FINGER_PIP, hand_size
        ),
        _finger_extension_ratio(
            landmarks, RING_FINGER_TIP, RING_FINGER_PIP, hand_size
        ),
        _finger_extension_ratio(
            landmarks, LITTLE_FINGER_TIP, LITTLE_FINGER_PIP, hand_size
        ),
        palm_anchor_y,
        palm_anchor_x,
    )
