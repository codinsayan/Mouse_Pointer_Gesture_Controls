from threading import Event
from pathlib import Path

from gesture_controls.config import AppConfig
from gesture_controls.ui.runtime import (
    ManagedGestureRuntime,
    RuntimeBridge,
    RuntimeCommand,
    RuntimeSnapshot,
)


def test_bridge_preserves_command_order_and_latest_snapshot() -> None:
    bridge = RuntimeBridge()
    bridge.request(RuntimeCommand.TOGGLE)
    bridge.request(RuntimeCommand.EMERGENCY_PAUSE)
    bridge.publish(RuntimeSnapshot(running=True, control_state="enabled"))

    assert bridge.drain_commands() == (
        RuntimeCommand.TOGGLE,
        RuntimeCommand.EMERGENCY_PAUSE,
    )
    assert bridge.drain_commands() == ()
    assert bridge.snapshot.control_state == "enabled"


def test_managed_runtime_starts_once_and_passes_safe_arguments(
    local_tmp_path: Path,
) -> None:
    started = Event()
    may_finish = Event()
    received: dict[str, object] = {}

    def runner(config: AppConfig, **kwargs: object) -> None:
        received["config"] = config
        received.update(kwargs)
        started.set()
        may_finish.wait(2.0)

    runtime = ManagedGestureRuntime(runner)
    profile = local_tmp_path / "settings.json"
    config = AppConfig()
    assert runtime.start(config, profile, False)
    assert started.wait(1.0)
    assert not runtime.start(config, profile, True)
    assert received["profile_path"] == profile
    assert received["profile_config"] == config
    assert received["real_input_requested"] is False
    assert received["runtime_bridge"] is runtime.bridge
    may_finish.set()
    runtime.join(1.0)
    assert not runtime.running
    assert runtime.bridge.snapshot.control_state == "stopped"


def test_managed_runtime_commands_are_noops_when_stopped() -> None:
    runtime = ManagedGestureRuntime(lambda *args, **kwargs: None)
    runtime.toggle()
    runtime.emergency_pause()
    runtime.stop()
    assert runtime.bridge.drain_commands() == ()


def test_managed_runtime_reports_runner_error(local_tmp_path: Path) -> None:
    def failing_runner(*args: object, **kwargs: object) -> None:
        raise RuntimeError("camera unavailable")

    runtime = ManagedGestureRuntime(failing_runner)
    assert runtime.start(AppConfig(), local_tmp_path / "settings.json", False)
    runtime.join(1.0)
    assert runtime.bridge.snapshot.control_state == "error"
    assert "camera unavailable" in runtime.bridge.snapshot.reason
