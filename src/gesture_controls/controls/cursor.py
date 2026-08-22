"""Framework-neutral cursor mapping and smoothing."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, hypot


@dataclass(frozen=True, slots=True)
class Point2D:
    x: float
    y: float

    def distance_to(self, other: "Point2D") -> float:
        return hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True, slots=True)
class CursorRegion:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.left < self.right <= 1.0:
            raise ValueError("cursor region must satisfy 0 <= left < right <= 1")
        if not 0.0 <= self.top < self.bottom <= 1.0:
            raise ValueError("cursor region must satisfy 0 <= top < bottom <= 1")


def _clamp_unit(value: float) -> float:
    return min(1.0, max(0.0, value))


def map_to_normalized_screen(point: Point2D, region: CursorRegion) -> Point2D:
    """Map a camera-region point to a clamped normalized screen point."""
    return Point2D(
        _clamp_unit((point.x - region.left) / (region.right - region.left)),
        _clamp_unit((point.y - region.top) / (region.bottom - region.top)),
    )


class ExponentialSmoother:
    """Elapsed-time exponential filter whose response is FPS independent."""

    def __init__(self, time_constant_seconds: float) -> None:
        if time_constant_seconds <= 0.0:
            raise ValueError("time_constant_seconds must be greater than zero")
        self._time_constant = time_constant_seconds
        self._value: Point2D | None = None
        self._timestamp: float | None = None

    def update(self, value: Point2D, timestamp_seconds: float) -> Point2D:
        if self._timestamp is not None and timestamp_seconds < self._timestamp:
            raise ValueError("timestamps must be monotonic")
        if self._value is None or self._timestamp is None:
            self._value = value
            self._timestamp = timestamp_seconds
            return value
        elapsed = timestamp_seconds - self._timestamp
        alpha = 1.0 - exp(-elapsed / self._time_constant)
        self._value = Point2D(
            self._value.x + alpha * (value.x - self._value.x),
            self._value.y + alpha * (value.y - self._value.y),
        )
        self._timestamp = timestamp_seconds
        return self._value

    def reset(self) -> None:
        self._value = None
        self._timestamp = None


@dataclass(frozen=True, slots=True)
class CursorUpdate:
    camera_point: Point2D
    mapped_point: Point2D
    smoothed_point: Point2D
    output_point: Point2D
    moved: bool


class CursorPipeline:
    """Map, smooth, and threshold cursor targets without emitting OS input."""

    def __init__(
        self,
        region: CursorRegion,
        smoothing_time_constant_seconds: float,
        minimum_movement: float,
    ) -> None:
        if not 0.0 <= minimum_movement <= 1.0:
            raise ValueError("minimum_movement must be between 0.0 and 1.0")
        self._region = region
        self._smoother = ExponentialSmoother(smoothing_time_constant_seconds)
        self._minimum_movement = minimum_movement
        self._last_output: Point2D | None = None

    def update(self, camera_point: Point2D, timestamp_seconds: float) -> CursorUpdate:
        mapped = map_to_normalized_screen(camera_point, self._region)
        smoothed = self._smoother.update(mapped, timestamp_seconds)
        moved = (
            self._last_output is None
            or smoothed.distance_to(self._last_output) >= self._minimum_movement
        )
        if moved:
            self._last_output = smoothed
        assert self._last_output is not None
        return CursorUpdate(camera_point, mapped, smoothed, self._last_output, moved)

    def reset(self) -> None:
        self._smoother.reset()
        self._last_output = None
