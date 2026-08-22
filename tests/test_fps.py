import pytest

from gesture_controls.diagnostics import FpsMeter


def test_measures_processed_fps_over_window() -> None:
    meter = FpsMeter(window_size=3)
    assert meter.update(1.0) == 0.0
    assert meter.update(1.05) == pytest.approx(20.0)
    assert meter.update(1.10) == pytest.approx(20.0)
    assert meter.update(1.15) == pytest.approx(20.0)


def test_rejects_time_moving_backwards() -> None:
    meter = FpsMeter()
    meter.update(2.0)
    with pytest.raises(ValueError, match="monotonic"):
        meter.update(1.0)

