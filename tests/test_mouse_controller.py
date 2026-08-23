from types import SimpleNamespace

import pytest

from gesture_controls.controls import Point2D
from gesture_controls.controls.mouse import PyAutoGuiMouseController, normalized_to_pixel


class FakePyAutoGui:
    FAILSAFE = False
    PAUSE = 1.0

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def size(self) -> tuple[int, int]: return 1920, 1080
    def moveTo(self, x: int, y: int, duration: int) -> None: self.calls.append(("move", (x, y, duration)))
    def click(self, *, button: str) -> None: self.calls.append(("click", button))
    def doubleClick(self, *, button: str, interval: float) -> None: self.calls.append(("double", (button, interval)))
    def scroll(self, steps: int) -> None: self.calls.append(("scroll", steps))
    def hscroll(self, steps: int) -> None: self.calls.append(("hscroll", steps))
    def mouseDown(self, *, button: str) -> None: self.calls.append(("down", button))
    def mouseUp(self, *, button: str) -> None: self.calls.append(("up", (button, self.FAILSAFE)))
    def keyDown(self, key: str) -> None: self.calls.append(("key_down", key))
    def press(self, key: str, *, presses: int, interval: int) -> None: self.calls.append(("press", (key, presses, interval)))
    def keyUp(self, key: str) -> None: self.calls.append(("key_up", (key, self.FAILSAFE)))


class FailingClickBackend(FakePyAutoGui):
    def click(self, *, button: str) -> None:
        self.calls.append(("partial_click", button))
        raise OSError("simulated partial click")


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        (Point2D(0.0, 0.0), (0, 0)),
        (Point2D(1.0, 1.0), (1919, 1079)),
        (Point2D(-1.0, 2.0), (0, 1079)),
        (Point2D(0.5, 0.5), (960, 540)),
    ],
)
def test_normalized_to_pixel_clamps(point: Point2D, expected: tuple[int, int]) -> None:
    assert normalized_to_pixel(point, 1920, 1080) == expected


def test_normalized_to_pixel_rejects_invalid_screen() -> None:
    with pytest.raises(ValueError, match="screen dimensions"):
        normalized_to_pixel(Point2D(0.5, 0.5), 0, 1080)


def test_pyautogui_adapter_maps_all_outputs_with_injected_backend() -> None:
    backend = FakePyAutoGui()
    controller = PyAutoGuiMouseController(backend)
    controller.move_to(Point2D(1.0, 0.0))
    controller.click_left()
    controller.click_left_twice()
    controller.click_right()
    controller.scroll_vertical(2)
    controller.scroll_horizontal(-3)
    controller.zoom(2)
    controller.zoom(-1)
    controller.begin_drag()
    controller.begin_drag()
    controller.end_drag()
    controller.end_drag()

    assert backend.FAILSAFE is True
    assert backend.PAUSE == 0.0
    assert backend.calls.count(("down", "left")) == 1
    assert backend.calls.count(("up", ("left", False))) == 1
    assert ("move", (1919, 0, 0)) in backend.calls
    assert ("scroll", 2) in backend.calls
    assert ("hscroll", -3) in backend.calls
    assert ("press", ("+", 2, 0)) in backend.calls
    assert ("press", ("-", 1, 0)) in backend.calls


def test_release_all_is_idempotent_and_releases_only_owned_inputs() -> None:
    backend = FakePyAutoGui()
    controller = PyAutoGuiMouseController(backend)
    controller.begin_drag()
    controller.release_all()
    controller.release_all()
    assert backend.calls.count(("up", ("left", False))) == 1


def test_invalid_backend_screen_is_readable_controller_error() -> None:
    backend = SimpleNamespace(size=lambda: (0, 0))
    with pytest.raises(RuntimeError, match="screen dimensions"):
        PyAutoGuiMouseController(backend)


def test_partial_click_failure_can_be_released_safely() -> None:
    backend = FailingClickBackend()
    controller = PyAutoGuiMouseController(backend)

    with pytest.raises(OSError, match="partial click"):
        controller.click_left()
    controller.release_all()

    assert ("up", ("left", False)) in backend.calls
