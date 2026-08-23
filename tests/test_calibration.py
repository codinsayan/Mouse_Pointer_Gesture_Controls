import pytest

from gesture_controls.controls import (
    CalibrationState,
    CursorCalibrator,
    Point2D,
)


def calibrator(
    minimum_samples: int = 10,
    low: float = 0.0,
    high: float = 1.0,
    padding: float = 0.0,
    minimum_span: float = 0.2,
) -> CursorCalibrator:
    return CursorCalibrator(minimum_samples, low, high, padding, minimum_span)


def test_calibration_derives_region_and_applies_padding() -> None:
    item = calibrator(padding=0.1)
    item.start()
    for index in range(10):
        fraction = index / 9
        item.add(Point2D(0.2 + 0.5 * fraction, 0.1 + 0.6 * fraction))
    region = item.finish()
    assert region is not None
    assert region.left == pytest.approx(0.15)
    assert region.right == pytest.approx(0.75)
    assert region.top == pytest.approx(0.04)
    assert region.bottom == pytest.approx(0.76)
    assert item.status.state is CalibrationState.APPLIED
    assert item.status.sample_count == 10


def test_percentiles_reduce_outlier_influence() -> None:
    item = calibrator(low=0.1, high=0.9)
    item.start()
    item.add(Point2D(0.0, 0.0))
    for index in range(10):
        fraction = index / 9
        item.add(Point2D(0.3 + 0.4 * fraction, 0.25 + 0.5 * fraction))
    item.add(Point2D(1.0, 1.0))
    region = item.finish()
    assert region is not None
    assert 0.25 < region.left < 0.35
    assert 0.65 < region.right < 0.75


def test_insufficient_samples_and_coverage_are_reported() -> None:
    item = calibrator()
    item.start()
    for _ in range(9):
        item.add(Point2D(0.2, 0.2))
    assert item.finish() is None
    assert item.status.state is CalibrationState.ERROR
    assert "at least" in item.status.message

    item.start()
    for index in range(10):
        item.add(Point2D(0.4 + index * 0.001, 0.5 + index * 0.001))
    assert item.finish() is None
    assert "Coverage" in item.status.message


def test_cancel_and_out_of_bounds_samples_do_not_persist() -> None:
    item = calibrator()
    item.start()
    item.add(Point2D(-1.0, 0.5))
    item.add(Point2D(0.5, 2.0))
    item.add(Point2D(0.5, 0.5))
    assert item.status.sample_count == 1
    item.cancel()
    assert item.status.state is CalibrationState.CANCELLED
    item.start()
    assert item.status.sample_count == 0


@pytest.mark.parametrize(
    "args, message",
    [
        ((9, 0.0, 1.0, 0.0, 0.2), "samples"),
        ((10, 0.9, 0.1, 0.0, 0.2), "quantiles"),
        ((10, 0.0, 1.0, 0.6, 0.2), "padding"),
        ((10, 0.0, 1.0, 0.0, 0.0), "span"),
    ],
)
def test_invalid_calibration_configuration_is_rejected(
    args: tuple[float, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        CursorCalibrator(*args)  # type: ignore[arg-type]
