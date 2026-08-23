from types import SimpleNamespace

from gesture_controls.controls import HotkeyAction, WindowsGlobalHotkeys
from gesture_controls.errors import HotkeyRegistrationError


class FakeUser32:
    message_type = SimpleNamespace

    def __init__(self, *, fail_id: int | None = None) -> None:
        self.fail_id = fail_id
        self.registered: list[int] = []
        self.unregistered: list[int] = []
        self.messages: list[int] = []

    def RegisterHotKey(self, window: object, hotkey_id: int, modifiers: int, key: int) -> bool:
        del window, modifiers, key
        if hotkey_id == self.fail_id:
            return False
        self.registered.append(hotkey_id)
        return True

    def UnregisterHotKey(self, window: object, hotkey_id: int) -> bool:
        del window
        self.unregistered.append(hotkey_id)
        return True

    def PeekMessageW(self, message: object, *args: object) -> bool:
        del args
        if not self.messages:
            return False
        message.wParam = self.messages.pop(0)
        return True


def test_register_poll_and_unregister_hotkeys() -> None:
    user32 = FakeUser32()
    hotkeys = WindowsGlobalHotkeys(user32)
    with hotkeys:
        user32.messages.extend((hotkeys._TOGGLE_ID, hotkeys._EMERGENCY_ID))
        assert hotkeys.poll() == (HotkeyAction.TOGGLE, HotkeyAction.EMERGENCY_PAUSE)
    assert user32.unregistered == list(reversed(user32.registered))


def test_partial_registration_failure_cleans_up() -> None:
    user32 = FakeUser32(fail_id=WindowsGlobalHotkeys._EMERGENCY_ID)
    hotkeys = WindowsGlobalHotkeys(user32)
    try:
        hotkeys.open()
    except HotkeyRegistrationError as exc:
        assert "Could not register" in str(exc)
    else:
        raise AssertionError("expected registration error")
    assert user32.unregistered == [WindowsGlobalHotkeys._TOGGLE_ID]
