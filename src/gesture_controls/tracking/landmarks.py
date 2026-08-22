"""Framework-neutral landmark values and geometry."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Landmark:
    x: float
    y: float
    z: float = 0.0


def normalized_distance(first: Landmark, second: Landmark) -> float:
    """Return Euclidean distance in normalized 3-D landmark coordinates."""
    return sqrt(
        (first.x - second.x) ** 2
        + (first.y - second.y) ** 2
        + (first.z - second.z) ** 2
    )

