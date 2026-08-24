from gesture_controls.controls import ControlState, InputSafetyController, Point2D, RecordingMouseController


def test_starts_disabled_and_blocks_every_output() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    assert safety.status.state is ControlState.DISABLED
    assert not safety.move_to(Point2D(0.2, 0.3))
    assert not safety.click_left()
    assert not safety.begin_drag()
    assert fake.actions == []


def test_explicit_enable_waits_for_tracking_then_dispatches_automatically() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    assert safety.toggle()
    assert safety.status.state is ControlState.ENABLED
    assert not safety.click_left()
    safety.set_tracking_available(True)
    assert safety.click_left()
    assert safety.scroll_vertical(2)
    assert ("left_click", None) in fake.actions
    assert ("vertical_scroll", 2) in fake.actions


def test_tracking_loss_releases_drag_and_recovers_without_reenable() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    safety.toggle()
    safety.begin_drag()
    safety.set_tracking_available(False, "waiting for hand")
    assert safety.status.state is ControlState.ENABLED
    assert safety.status.reason == "waiting for hand"
    assert not fake.dragging
    assert ("drag_up", None) in fake.actions
    assert not safety.move_to(Point2D(0.5, 0.5))
    safety.set_tracking_available(True)
    assert safety.status.state is ControlState.ENABLED
    assert safety.move_to(Point2D(0.5, 0.5))


def test_manual_disable_remains_disabled_when_hand_reappears() -> None:
    safety = InputSafetyController(RecordingMouseController())
    safety.set_tracking_available(True)
    safety.toggle()
    assert not safety.toggle()
    safety.set_tracking_available(False)
    safety.set_tracking_available(True)
    assert safety.status.state is ControlState.DISABLED
    assert not safety.enabled


def test_user_pause_and_emergency_pause_release_held_drag() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    safety.toggle()
    safety.begin_drag()
    safety.pause()
    assert safety.status.state is ControlState.DISABLED
    assert not fake.dragging
    safety.toggle()
    safety.begin_drag()
    safety.emergency_pause()
    assert safety.status.state is ControlState.DISABLED
    assert not fake.dragging


def test_shutdown_is_idempotent_and_blocks_later_output() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    safety.toggle()
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
    safety.set_tracking_available(True)
    safety.toggle()
    safety.begin_drag()
    assert not safety.click_left()
    assert safety.status.state is ControlState.DISABLED
    assert "OSError" in safety.status.reason
    assert not fake.dragging


def test_zero_step_operations_do_not_dispatch() -> None:
    fake = RecordingMouseController()
    safety = InputSafetyController(fake)
    safety.set_tracking_available(True)
    safety.toggle()
    assert not safety.scroll_vertical(0)
    assert not safety.scroll_horizontal(0)
    assert fake.actions == []
