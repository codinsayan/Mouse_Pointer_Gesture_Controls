"""Non-hooking Windows global hotkeys for control toggle and emergency pause."""

from __future__ import annotations

import sys
from enum import Enum
from typing import Any

from gesture_controls.errors import HotkeyRegistrationError


class HotkeyAction(str, Enum):
    TOGGLE = "toggle"
    EMERGENCY_PAUSE = "emergency_pause"


class NullHotkeySource:
    available = False

    def open(self) -> "NullHotkeySource": return self
    def poll(self) -> tuple[HotkeyAction, ...]: return ()
    def close(self) -> None: pass
    def __enter__(self) -> "NullHotkeySource": return self.open()
    def __exit__(self, *_: object) -> None: self.close()


class WindowsGlobalHotkeys:
    """Register Ctrl+Alt+G and Ctrl+Alt+Shift+G on the current thread."""

    available = True
    _TOGGLE_ID = 0xB701
    _EMERGENCY_ID = 0xB702
    _WM_HOTKEY = 0x0312
    _PM_REMOVE = 0x0001
    _MOD_ALT = 0x0001
    _MOD_CONTROL = 0x0002
    _MOD_SHIFT = 0x0004
    _MOD_NOREPEAT = 0x4000
    _VK_G = 0x47

    def __init__(self, user32: Any | None = None) -> None:
        if sys.platform != "win32" and user32 is None:
            raise HotkeyRegistrationError("Global hotkeys require Windows.")
        if user32 is None:
            import ctypes
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            self._message_type = ctypes.wintypes.MSG
            self._byref = ctypes.byref
        else:
            self._message_type = getattr(user32, "message_type", object)
            self._byref = lambda value: value
        self._user32 = user32
        self._registered: list[int] = []

    def open(self) -> "WindowsGlobalHotkeys":
        modifiers = self._MOD_CONTROL | self._MOD_ALT | self._MOD_NOREPEAT
        registrations = (
            (self._TOGGLE_ID, modifiers),
            (self._EMERGENCY_ID, modifiers | self._MOD_SHIFT),
        )
        for hotkey_id, hotkey_modifiers in registrations:
            if not self._user32.RegisterHotKey(
                None, hotkey_id, hotkey_modifiers, self._VK_G
            ):
                self.close()
                raise HotkeyRegistrationError(
                    "Could not register global safety hotkeys; another application "
                    "may already use Ctrl+Alt+G."
                )
            self._registered.append(hotkey_id)
        return self

    def poll(self) -> tuple[HotkeyAction, ...]:
        actions: list[HotkeyAction] = []
        message = self._message_type()
        while self._user32.PeekMessageW(
            self._byref(message), None, self._WM_HOTKEY, self._WM_HOTKEY, self._PM_REMOVE
        ):
            hotkey_id = int(message.wParam)
            if hotkey_id == self._TOGGLE_ID:
                actions.append(HotkeyAction.TOGGLE)
            elif hotkey_id == self._EMERGENCY_ID:
                actions.append(HotkeyAction.EMERGENCY_PAUSE)
        return tuple(actions)

    def close(self) -> None:
        for hotkey_id in reversed(self._registered):
            self._user32.UnregisterHotKey(None, hotkey_id)
        self._registered.clear()

    def __enter__(self) -> "WindowsGlobalHotkeys": return self.open()
    def __exit__(self, *_: object) -> None: self.close()
