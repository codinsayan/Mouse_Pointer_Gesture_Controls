"""Low-latency hysteresis gate for the index-raised pointer pose."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PointerPoseUpdate:
    active: bool
    index_extension_ratio: float


class PointerPoseGate:
    def __init__(self, activation_ratio: float, release_ratio: float) -> None:
        if not 0.0 <= release_ratio < activation_ratio:
            raise ValueError("pointer extension release must be below activation")
        self._activation = activation_ratio
        self._release = release_ratio
        self._active = False

    def update(self, index_extension_ratio: float) -> PointerPoseUpdate:
        if self._active:
            self._active = index_extension_ratio >= self._release
        else:
            self._active = index_extension_ratio >= self._activation
        return PointerPoseUpdate(self._active, index_extension_ratio)

    def reset(self) -> None:
        self._active = False
