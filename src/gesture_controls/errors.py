"""Expected, user-facing application failures."""


class GestureControlsError(RuntimeError):
    """Base class for failures that should be shown without a traceback."""


class CameraOpenError(GestureControlsError):
    """Raised when the configured camera cannot be opened."""


class CameraReadError(GestureControlsError):
    """Raised when an opened camera stops returning frames."""


class ModelAssetError(GestureControlsError):
    """Raised when the required local model asset is unavailable."""


class TrackerInitializationError(GestureControlsError):
    """Raised when MediaPipe cannot initialize the hand tracker."""


class ConfigurationError(GestureControlsError):
    """Raised when a local settings profile cannot be loaded or saved safely."""


class InputControllerError(GestureControlsError):
    """Raised when the opt-in operating-system input adapter cannot initialize."""


class HotkeyRegistrationError(GestureControlsError):
    """Raised when mandatory Windows safety hotkeys cannot be registered."""


class DashboardInitializationError(GestureControlsError):
    """Raised when the native settings dashboard cannot initialize."""
