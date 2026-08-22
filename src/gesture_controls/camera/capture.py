"""OpenCV webcam ownership with explicit failures."""

from __future__ import annotations

from typing import Any

from gesture_controls.config import AppConfig
from gesture_controls.errors import CameraOpenError, CameraReadError


class CameraCapture:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._capture: Any | None = None

    def open(self) -> "CameraCapture":
        try:
            import cv2
        except ImportError as exc:
            raise CameraOpenError(
                "OpenCV is not installed. Install requirements before running."
            ) from exc

        backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY
        capture = cv2.VideoCapture(self._config.camera_index, backend)
        if not capture.isOpened():
            capture.release()
            raise CameraOpenError(
                f"Could not open camera {self._config.camera_index}. Close other "
                "camera applications and check Windows camera permissions."
            )
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.frame_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.frame_height)
        capture.set(cv2.CAP_PROP_FPS, self._config.target_fps)
        self._capture = capture
        return self

    def read(self) -> Any:
        if self._capture is None:
            raise CameraReadError("Camera has not been opened.")
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise CameraReadError(
                "Camera stopped returning frames. Check the connection and permissions."
            )
        return frame

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "CameraCapture":
        return self.open()

    def __exit__(self, *_: object) -> None:
        self.close()

