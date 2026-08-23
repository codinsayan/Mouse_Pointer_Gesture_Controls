from gesture_controls.controls import ControlState, InputSafetyController, Point2D, RecordingMouseController


def test_starts_disabled_and_blocks_every_output() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    assert safety.status.state is ControlState.DISABLED
    assert not safety.move_to(Point2D(0.2, 0.3))
    assert not safety.click_left()
    assert not safety.begin_drag()
    assert fake.actions == []


def test_explicit_enable_requires_tracking_and_dispatches_when_ready() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    assert not safety.toggle(False)
    assert safety.status.state is ControlState.TRACKING_LOST
    assert safety.toggle(True)
    assert safety.click_left()
    assert safety.scroll_vertical(2)
    assert ("left_click", None) in fake.actions
    assert ("vertical_scroll", 2) in fake.actions


def test_tracking_loss_releases_drag_and_requires_explicit_reenable() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.toggle(True)
    safety.begin_drag()
    safety.tracking_lost("hand disappeared")
    assert safety.status.state is ControlState.TRACKING_LOST
    assert not fake.dragging
    assert ("drag_up", None) in fake.actions
    assert not safety.move_to(Point2D(0.5, 0.5))
    assert safety.toggle(True)


def test_user_pause_and_emergency_pause_release_held_drag() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.toggle(True)
    safety.begin_drag()
    safety.pause()
    assert safety.status.state is ControlState.DISABLED
    assert not fake.dragging
    safety.toggle(True)
    safety.begin_drag()
    safety.emergency_pause()
    assert safety.status.state is ControlState.EMERGENCY_PAUSED
    assert not fake.dragging


def test_shutdown_is_idempotent_and_blocks_later_output() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.toggle(True)
    safety.begin_drag()
    safety.shutdown()
    safety.shutdown()
    assert safety.status.state is ControlState.DISABLED
    assert not fake.dragging
    assert not safety.click_right()


class FailingMouseController(RecordingMouseController):
    def click_left(self) -> None:
        raise OSError("simulated output failure")


def test_output_failure_emergency_pauses_and_releases() -> None:
    fake = FailingMouseController()
    safety = InputSafetyController(fake)
    safety.toggle(True)
    safety.begin_drag()
    assert not safety.click_left()
    assert safety.status.state is ControlState.EMERGENCY_PAUSED
    assert "OSError" in safety.status.reason
    assert not fake.dragging


def test_zero_step_operations_do_not_dispatch() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.toggle(True)
    assert not safety.scroll_vertical(0)
    assert not safety.scroll_horizontal(0)
    assert not safety.zoom(0)
    assert fake.actions == []
