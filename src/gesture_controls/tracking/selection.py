"""Deterministic reported-handedness selection."""

from __future__ import annotations


def hand_matches_preference(
    reported_handedness: str | None, dominant_hand: str
) -> bool:
    if dominant_hand == "any":
        return True
    if reported_handedness is None:
        return False
    return reported_handedness.casefold() == dominant_hand.casefold()
