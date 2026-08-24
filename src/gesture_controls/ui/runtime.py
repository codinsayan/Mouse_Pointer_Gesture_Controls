"""Thread-safe commands, status, and managed runtime lifecycle for the UI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Lock, Thread
from typing import Callable

from gesture_controls.config import AppConfig


class RuntimeCommand(str, Enum):
    TOGGLE = "toggle"
    EMERGENCY_PAUSE = "emergency_pause"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    running: bool = False
    control_state: str = "stopped"
    reason: str = "Camera runtime is stopped"
    controller_name: str = "none"
    real_output: bool = False
    hand_detected: bool = False
    tracking_ready: bool = False
    confidence: float | None = None
    fps: float = 0.0


class RuntimeBridge:
    def __init__(self) -> None:
        self._commands: SimpleQueue[RuntimeCommand] = SimpleQueue()
        self._lock = Lock()
        self._snapshot = RuntimeSnapshot()

    def request(self, command: RuntimeCommand) -> None:
        self._commands.put(command)

    def drain_commands(self) -> tuple[RuntimeCommand, ...]:
        commands: list[RuntimeCommand] = []
        while True:
            try:
                commands.append(self._commands.get_nowait())
            except Empty:
                return tuple(commands)

    def publish(self, snapshot: RuntimeSnapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    @property
    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return self._snapshot


RuntimeRunner = Callable[..., None]


class ManagedGestureRuntime:
    """Run the existing foreground loop in one safely stoppable worker."""

    def __init__(self, runner: RuntimeRunner | None = None) -> None:
        self.bridge = RuntimeBridge()
        self._runner = runner
        self._thread: Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self, config: AppConfig, profile_path: Path, real_input_requested: bool
    ) -> bool:
        if self.running:
            return False
        self.bridge = RuntimeBridge()
        self.bridge.publish(
            RuntimeSnapshot(
                running=True,
                control_state="starting",
                reason="Opening camera and tracker",
                controller_name=("pyautogui" if real_input_requested else "dry-run"),
                real_output=real_input_requested,
            )
        )
        self._thread = Thread(
            target=self._run,
            args=(config, profile_path, real_input_requested),
            name="gesture-controls-runtime",
            daemon=False,
        )
        self._thread.start()
        return True

    def _run(
        self, config: AppConfig, profile_path: Path, real_input_requested: bool
    ) -> None:
        try:
            runner = self._runner
            if runner is None:
                from gesture_controls.app import run

                runner = run
            runner(
                config,
                profile_path=profile_path,
                profile_config=config,
                real_input_requested=real_input_requested,
                runtime_bridge=self.bridge,
            )
        except Exception as exc:
            self.bridge.publish(
                replace(
                    self.bridge.snapshot,
                    running=False,
                    control_state="error",
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            self.bridge.publish(
                replace(
                    self.bridge.snapshot,
                    running=False,
                    control_state="stopped",
                    reason="Camera runtime stopped safely",
                    hand_detected=False,
                    tracking_ready=False,
                    fps=0.0,
                )
            )

    def toggle(self) -> None:
        if self.running:
            self.bridge.request(RuntimeCommand.TOGGLE)

    def emergency_pause(self) -> None:
        if self.running:
            self.bridge.request(RuntimeCommand.EMERGENCY_PAUSE)

    def stop(self) -> None:
        if self.running:
            self.bridge.request(RuntimeCommand.STOP)

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)
