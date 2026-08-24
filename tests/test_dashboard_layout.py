from gesture_controls.ui.dashboard import (
    control_toggle_presentation,
    dashboard_layout_mode,
    mousewheel_units,
)


def test_dashboard_stacks_cards_below_breakpoint() -> None:
    assert dashboard_layout_mode(899) == "stacked"
    assert dashboard_layout_mode(520) == "stacked"


def test_dashboard_uses_side_by_side_cards_when_wide() -> None:
    assert dashboard_layout_mode(900) == "wide"
    assert dashboard_layout_mode(1400) == "wide"


def test_windows_mousewheel_delta_is_normalized() -> None:
    assert mousewheel_units(120) == -1
    assert mousewheel_units(-120) == 1
    assert mousewheel_units(240) == -2
    assert mousewheel_units(0) == 0


def test_enable_button_does_not_require_a_current_hand() -> None:
    assert control_toggle_presentation(
        running=True, tracking_ready=False, control_state="disabled"
    ) == ("Enable control", True)
    assert control_toggle_presentation(
        running=True, tracking_ready=True, control_state="disabled"
    ) == ("Enable control", True)


def test_enabled_control_can_always_be_disabled() -> None:
    assert control_toggle_presentation(
        running=True, tracking_ready=False, control_state="enabled"
    ) == ("Disable control", True)
