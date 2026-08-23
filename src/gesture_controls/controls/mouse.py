"""Operating-system mouse boundary with safe dry-run and PyAutoGUI adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from gesture_controls.errors import InputControllerError

from .cursor import Point2D


def normalized_to_pixel(
    point: Point2D, screen_width: int, screen_height: int
) -> tuple[int, int]:
    """Convert a normalized point to a clamped, zero-based screen pixel."""
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError("screen dimensions must be greater than zero")
    x = min(1.0, max(0.0, point.x))
    y = min(1.0, max(0.0, point.y))
    return round(x * (screen_width - 1)), round(y * (screen_height - 1))


class MouseController(Protocol):
    """Minimal output interface consumed by the safety state machine."""

    @property
    def name(self) -> str: ...

    @property
    def real_output(self) -> bool: ...

    def move_to(self, point: Point2D) -> None: ...
    def click_left(self) -> None: ...
    def click_left_twice(self) -> None: ...
    def click_right(self) -> None: ...
    def scroll_vertical(self, steps: int) -> None: ...
    def scroll_horizontal(self, steps: int) -> None: ...
    def zoom(self, steps: int) -> None: ...
    def begin_drag(self) -> None: ...
    def end_drag(self) -> None: ...
    def release_all(self) -> None: ...


class DryRunMouseController:
    """No-op output adapter used unless real input is explicitly requested."""

    name = "dry-run"
    real_output = False

    def move_to(self, point: Point2D) -> None:
        del point

    def click_left(self) -> None: pass
    def click_left_twice(self) -> None: pass
    def click_right(self) -> None: pass
    def scroll_vertical(self, steps: int) -> None: del steps
    def scroll_horizontal(self, steps: int) -> None: del steps
    def zoom(self, steps: int) -> None: del steps
    def begin_drag(self) -> None: pass
    def end_drag(self) -> None: pass
    def release_all(self) -> None: pass


@dataclass(slots=True)
class RecordingMouseController:
    """Deterministic fake for tests; it never imports or calls PyAutoGUI."""

    actions: list[tuple[str, object | None]] = field(default_factory=list)
    name: str = "fake"
    real_output: bool = False
    dragging: bool = False

    def move_to(self, point: Point2D) -> None:
        self.actions.append(("move", point))

    def click_left(self) -> None:
        self.actions.append(("left_click", None))

    def click_left_twice(self) -> None:
        self.actions.append(("double_click", None))

    def click_right(self) -> None:
        self.actions.append(("right_click", None))

    def scroll_vertical(self, steps: int) -> None:
        self.actions.append(("vertical_scroll", steps))

    def scroll_horizontal(self, steps: int) -> None:
        self.actions.append(("horizontal_scroll", steps))

    def zoom(self, steps: int) -> None:
        self.actions.append(("zoom", steps))

    def begin_drag(self) -> None:
        if not self.dragging:
            self.dragging = True
            self.actions.append(("drag_down", None))

    def end_drag(self) -> None:
        if self.dragging:
            self.dragging = False
            self.actions.append(("drag_up", None))

    def release_all(self) -> None:
        self.end_drag()
        self.actions.append(("release_all", None))


class PyAutoGuiMouseController:
    """Lazy PyAutoGUI adapter. Construct only after explicit real-input opt-in."""

    name = "pyautogui"
    real_output = True

    def __init__(self, backend: Any | None = None) -> None:
        try:
            if backend is None:
                import pyautogui as backend
        except Exception as exc:
            raise InputControllerError(
                "PyAutoGUI could not initialize. Use dry-run mode or verify the "
                "Windows desktop session and dependency installation."
            ) from exc
        self._backend = backend
        try:
            size = backend.size()
            self._width = int(size[0])
            self._height = int(size[1])
            if self._width <= 0 or self._height <= 0:
                raise ValueError("invalid screen size")
            backend.FAILSAFE = True
            backend.PAUSE = 0.0
        except Exception as exc:
            raise InputControllerError(
                "PyAutoGUI could not read the primary screen dimensions."
            ) from exc
        self._dragging = False
        self._control_held = False
        self._pending_button: str | None = None

    def move_to(self, point: Point2D) -> None:
        x, y = normalized_to_pixel(point, self._width, self._height)
        self._backend.moveTo(x, y, duration=0)

    def click_left(self) -> None:
        self._click_with_release_guard(self._backend.click, "left")

    def click_left_twice(self) -> None:
        self._click_with_release_guard(
            self._backend.doubleClick, "left", interval=0.08
        )

    def click_right(self) -> None:
        self._click_with_release_guard(self._backend.click, "right")

    def scroll_vertical(self, steps: int) -> None:
        if steps:
            self._backend.scroll(steps)

    def scroll_horizontal(self, steps: int) -> None:
        if steps:
            self._backend.hscroll(steps)

    def zoom(self, steps: int) -> None:
        if not steps:
            return
        key = "+" if steps > 0 else "-"
        self._backend.keyDown("ctrl")
        self._control_held = True
        try:
            self._backend.press(key, presses=abs(steps), interval=0)
        finally:
            self._release_call(self._backend.keyUp, "ctrl")
            self._control_held = False

    def begin_drag(self) -> None:
        if not self._dragging:
            self._pending_button = "left"
            self._backend.mouseDown(button="left")
            self._dragging = True
            self._pending_button = None

    def end_drag(self) -> None:
        if self._dragging:
            self._release_call(self._backend.mouseUp, button="left")
            self._dragging = False

    def release_all(self) -> None:
        errors: list[Exception] = []
        if self._dragging:
            try:
                self._release_call(self._backend.mouseUp, button="left")
            except Exception as exc:
                errors.append(exc)
            else:
                self._dragging = False
        if self._pending_button is not None:
            button = self._pending_button
            try:
                self._release_call(self._backend.mouseUp, button=button)
            except Exception as exc:
                errors.append(exc)
            else:
                self._pending_button = None
        if self._control_held:
            try:
                self._release_call(self._backend.keyUp, "ctrl")
            except Exception as exc:
                errors.append(exc)
            else:
                self._control_held = False
        if errors:
            raise InputControllerError("Failed to release all held OS inputs.") from errors[0]

    def _click_with_release_guard(
        self, operation: Any, button: str, **kwargs: Any
    ) -> None:
        self._pending_button = button
        operation(button=button, **kwargs)
        self._pending_button = None

    def _release_call(self, operation: Any, *args: Any, **kwargs: Any) -> None:
        """Release only app-owned inputs even when PyAutoGUI's corner failsafe fired."""
        failsafe = self._backend.FAILSAFE
        self._backend.FAILSAFE = False
        try:
            operation(*args, **kwargs)
        finally:
            self._backend.FAILSAFE = failsafe
