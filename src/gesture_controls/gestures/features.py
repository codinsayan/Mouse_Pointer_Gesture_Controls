"""Scale-independent feature extraction from neutral landmarks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from gesture_controls.tracking.landmarks import Landmark, normalized_distance

WRIST = 0
THUMB_TIP = 4
INDEX_FINGER_MCP = 5
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_MCP = 9
MIDDLE_FINGER_TIP = 12
LITTLE_FINGER_MCP = 17
LITTLE_FINGER_TIP = 20
REQUIRED_LANDMARK_COUNT = 21


@dataclass(frozen=True, slots=True)
class PinchFeatures:
    left_pinch_ratio: float
    double_click_pinch_ratio: float
    right_pinch_ratio: float
    hand_size: float


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


def extract_left_pinch_features(landmarks: Sequence[Landmark]) -> PinchFeatures:
    hand_size = reference_hand_size(landmarks)
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
    )
