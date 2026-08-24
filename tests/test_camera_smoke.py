from types import SimpleNamespace

from gesture_controls.config import AppConfig
from gesture_controls.diagnostics.camera_smoke import run_camera_smoke


class FakeFrame:
    shape = (480, 640, 3)


class FakeCv2:
    COLOR_BGR2RGB = 7

    @staticmethod
    def flip(frame, axis):
        assert axis == 1
        return frame

    @staticmethod
    def cvtColor(frame, conversion):
        assert conversion == FakeCv2.COLOR_BGR2RGB
        return frame


class FakeCamera:
    def __init__(self, config):
        self.config = config
        self.read_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        self.read_count += 1
        return FakeFrame()


class FakeTracker:
    def __init__(self, config):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def detect(self, frame, timestamp_ms):
        assert isinstance(frame, FakeFrame)
        assert timestamp_ms == 2
        return SimpleNamespace(
            hand_detected=True,
            handedness="Right",
            confidence=0.91,
        )


def test_camera_smoke_returns_metadata_without_retaining_a_frame() -> None:
    times = iter((1_000_000, 2_000_000, 6_000_000))

    result = run_camera_smoke(
        AppConfig(),
        camera_factory=FakeCamera,
        tracker_factory=FakeTracker,
        cv2_module=FakeCv2,
        clock_ns=lambda: next(times),
    )

    assert (result.frame_width, result.frame_height) == (640, 480)
    assert result.hand_detected
    assert result.handedness == "Right"
    assert result.confidence == 0.91
    assert result.elapsed_milliseconds == 5.0
