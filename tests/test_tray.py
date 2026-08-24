from __future__ import annotations

import sys
from types import SimpleNamespace

from gesture_controls.ui.dashboard import (
    TrayController,
    _run_tray_process,
    create_tray_image,
)
from gesture_controls.ui.runtime import RuntimeSnapshot


class FakeConnection:
    def __init__(self, incoming=None) -> None:
        self.incoming = list(incoming or [])
        self.sent = []
        self.closed = False

    def poll(self) -> bool:
        return bool(self.incoming)

    def recv(self):
        if not self.incoming:
            raise EOFError
        return self.incoming.pop(0)

    def send(self, value) -> None:
        self.sent.append(value)

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self, exit_on_join: bool) -> None:
        self.exit_on_join = exit_on_join
        self.started = False
        self.alive = False
        self.terminated = False

    def start(self) -> None:
        self.started = True
        self.alive = True

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout=None) -> None:
        if self.exit_on_join:
            self.alive = False

    def terminate(self) -> None:
        self.terminated = True
        self.alive = False


class FakeContext:
    def __init__(self, *, exit_on_join: bool = True) -> None:
        self.parent = FakeConnection()
        self.child = FakeConnection()
        self.process = FakeProcess(exit_on_join)

    def Pipe(self):
        return self.parent, self.child

    def Process(self, **_kwargs):
        return self.process


def test_tray_icon_is_generated_in_memory() -> None:
    image = create_tray_image()
    assert image.size == (64, 64)
    assert image.mode == "RGBA"


def test_tray_controller_polls_actions_and_updates_title() -> None:
    calls: list[str] = []
    context = FakeContext()
    tray = TrayController(
        lambda callback: callback(),
        lambda: calls.append("show"),
        lambda: calls.append("pause"),
        lambda: calls.append("quit"),
        process_context=context,
    )
    context.parent.incoming.extend(
        [("ready", None), ("action", "show"), ("action", "pause"), ("action", "quit")]
    )

    tray.start()
    tray.poll_actions()
    tray.update(RuntimeSnapshot(control_state="enabled", real_output=True))
    tray.stop()

    assert calls == ["show", "pause", "quit"]
    assert context.process.started is True
    assert ("title", "Gesture Controls — ENABLED — REAL") in context.parent.sent
    assert ("stop", None) in context.parent.sent
    assert context.parent.closed is True


def test_tray_controller_terminates_a_stuck_backend() -> None:
    context = FakeContext(exit_on_join=False)
    tray = TrayController(
        lambda callback: callback(),
        lambda: None,
        lambda: None,
        lambda: None,
        process_context=context,
    )

    tray.start()
    tray.stop()

    assert context.process.terminated is True
    assert tray.available is False


def test_tray_process_uses_backend_callback_signature(monkeypatch) -> None:
    connection = FakeConnection(incoming=[("stop", None)])

    class MenuItem:
        def __init__(self, text, action, default=False):
            self.text = text
            self.action = action
            self.default = default

    class Menu:
        SEPARATOR = object()

        def __init__(self, *items):
            self.items = items

    class Icon:
        def __init__(self, _name, _image, title, menu):
            self.title = title
            self.menu = menu
            self.visible = False
            self.stopped = False

        def run(self, setup):
            for item in (self.menu.items[0], self.menu.items[1], self.menu.items[3]):
                item.action(self, item)
            setup(self)

        def stop(self):
            self.stopped = True

    monkeypatch.setitem(
        sys.modules,
        "pystray",
        SimpleNamespace(Icon=Icon, Menu=Menu, MenuItem=MenuItem),
    )

    _run_tray_process(connection)

    assert connection.sent[:3] == [
        ("action", "show"),
        ("action", "pause"),
        ("action", "quit"),
    ]
    assert ("ready", None) in connection.sent
    assert connection.closed is True
