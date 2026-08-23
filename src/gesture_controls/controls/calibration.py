"""Transient landmark-only cursor-region calibration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import floor

from .cursor import CursorRegion, Point2D


class CalibrationState(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    APPLIED = "applied"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class CalibrationStatus:
    state: CalibrationState
    sample_count: int
    message: str


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = floor(position)
    upper = min(len(ordered) - 1, lower + 1)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


class CursorCalibrator:
    """Collect normalized points and derive robust cursor-region bounds."""

    def __init__(
        self,
        minimum_samples: int,
        low_quantile: float,
        high_quantile: float,
        padding_ratio: float,
        minimum_span: float,
    ) -> None:
        if minimum_samples < 10:
            raise ValueError("minimum calibration samples must be at least 10")
        if not 0.0 <= low_quantile < high_quantile <= 1.0:
            raise ValueError("calibration quantiles must be ordered")
        if not 0.0 <= padding_ratio <= 0.5:
            raise ValueError("calibration padding must be between 0.0 and 0.5")
        if not 0.0 < minimum_span <= 1.0:
            raise ValueError("minimum calibration span must be within 0.0..1.0")
        self._minimum_samples = minimum_samples
        self._low_quantile = low_quantile
        self._high_quantile = high_quantile
        self._padding_ratio = padding_ratio
        self._minimum_span = minimum_span
        self._samples: list[Point2D] = []
        self._status = CalibrationStatus(
            CalibrationState.IDLE, 0, "Press C to start cursor calibration"
        )

    @property
    def collecting(self) -> bool:
        return self._status.state is CalibrationState.COLLECTING

    @property
    def status(self) -> CalibrationStatus:
        return self._status

    def start(self) -> None:
        self._samples.clear()
        self._status = CalibrationStatus(
            CalibrationState.COLLECTING,
            0,
            "Move index tip around desired area; Enter applies, X cancels",
        )

    def add(self, point: Point2D) -> None:
        if not self.collecting:
            return
        if not 0.0 <= point.x <= 1.0 or not 0.0 <= point.y <= 1.0:
            return
        self._samples.append(point)
        self._status = CalibrationStatus(
            CalibrationState.COLLECTING,
            len(self._samples),
            "Move index tip around desired area; Enter applies, X cancels",
        )

    def finish(self) -> CursorRegion | None:
        if not self.collecting:
            return None
        count = len(self._samples)
        if count < self._minimum_samples:
            self._status = CalibrationStatus(
                CalibrationState.ERROR,
                count,
                f"Need at least {self._minimum_samples} valid samples; press C to retry",
            )
            return None
        xs = [point.x for point in self._samples]
        ys = [point.y for point in self._samples]
        left = _quantile(xs, self._low_quantile)
        right = _quantile(xs, self._high_quantile)
        top = _quantile(ys, self._low_quantile)
        bottom = _quantile(ys, self._high_quantile)
        horizontal_span = right - left
        vertical_span = bottom - top
        if horizontal_span < self._minimum_span or vertical_span < self._minimum_span:
            self._status = CalibrationStatus(
                CalibrationState.ERROR,
                count,
                "Coverage too small; press C and move across a wider area",
            )
            return None
        left = max(0.0, left - horizontal_span * self._padding_ratio)
        right = min(1.0, right + horizontal_span * self._padding_ratio)
        top = max(0.0, top - vertical_span * self._padding_ratio)
        bottom = min(1.0, bottom + vertical_span * self._padding_ratio)
        region = CursorRegion(left, top, right, bottom)
        self._samples.clear()
        self._status = CalibrationStatus(
            CalibrationState.APPLIED, count, "Calibration applied"
        )
        return region

    def cancel(self) -> None:
        count = len(self._samples)
        self._samples.clear()
        self._status = CalibrationStatus(
            CalibrationState.CANCELLED, count, "Calibration cancelled; press C to retry"
        )
