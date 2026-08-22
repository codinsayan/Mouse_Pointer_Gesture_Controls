import pytest

from gesture_controls.config import AppConfig
from gesture_controls.errors import ModelAssetError
from gesture_controls.tracking import HandLandmarkerTracker


def test_missing_model_fails_before_mediapipe_initialization() -> None:
    missing = AppConfig().model_path.with_name("definitely_missing_for_test.task")
    assert not missing.exists()
    tracker = HandLandmarkerTracker(AppConfig(model_path=missing))
    with pytest.raises(ModelAssetError, match="MediaPipe model not found"):
        tracker.open()
