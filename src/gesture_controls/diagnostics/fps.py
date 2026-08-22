"""Stable rolling FPS measurement."""

from __future__ import annotations

from collections import deque


class FpsMeter:
    def __init__(self, window_size: int = 30) -> None:
        if window_size < 2:
            raise ValueError("window_size must be at least 2")
        self._timestamps: deque[float] = deque(maxlen=window_size)

    def update(self, timestamp_seconds: float) -> float:
        if self._timestamps and timestamp_seconds < self._timestamps[-1]:
            raise ValueError("timestamps must be monotonic")
        self._timestamps.append(timestamp_seconds)
        return self.fps

    @property
    def fps(self) -> float:
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        return 0.0 if elapsed <= 0.0 else (len(self._timestamps) - 1) / elapsed

