from math import exp

import pytest

from gesture_controls.controls import (
    CursorPipeline,
    CursorRegion,
    ExponentialSmoother,
    Point2D,
    map_to_normalized_screen,
)


def test_maps_active_region_corners_and_center() -> None:
    region = CursorRegion(0.2, 0.1, 0.8, 0.9)
    assert map_to_normalized_screen(Point2D(0.2, 0.1), region) == Point2D(0.0, 0.0)
    assert map_to_normalized_screen(Point2D(0.8, 0.9), region) == Point2D(1.0, 1.0)
    center = map_to_normalized_screen(Point2D(0.5, 0.5), region)
    assert center.x == pytest.approx(0.5)
    assert center.y == pytest.approx(0.5)


def test_mapping_clamps_points_outside_active_region() -> None:
    region = CursorRegion(0.2, 0.2, 0.8, 0.8)
    assert map_to_normalized_screen(Point2D(-10, 10), region) == Point2D(0.0, 1.0)


def test_rejects_invalid_region() -> None:
    with pytest.raises(ValueError, match="left < right"):
        CursorRegion(0.5, 0.1, 0.5, 0.9)


def test_smoother_uses_elapsed_time() -> None:
    smoother = ExponentialSmoother(time_constant_seconds=0.1)
    assert smoother.update(Point2D(0, 0), 1.0) == Point2D(0, 0)
    result = smoother.update(Point2D(1, 1), 1.1)
    expected = 1.0 - exp(-1.0)
    assert result.x == pytest.approx(expected)
    assert result.y == pytest.approx(expected)


def test_smoother_rejects_non_monotonic_time() -> None:
    smoother = ExponentialSmoother(0.1)
    smoother.update(Point2D(0, 0), 2.0)
    with pytest.raises(ValueError, match="monotonic"):
        smoother.update(Point2D(1, 1), 1.0)


def test_smoother_response_is_independent_of_update_frequency() -> None:
    one_step = ExponentialSmoother(0.1)
    two_steps = ExponentialSmoother(0.1)
    one_step.update(Point2D(0, 0), 0.0)
    two_steps.update(Point2D(0, 0), 0.0)
    expected = one_step.update(Point2D(1, 1), 0.1)
    two_steps.update(Point2D(1, 1), 0.05)
    actual = two_steps.update(Point2D(1, 1), 0.1)
    assert actual.x == pytest.approx(expected.x)
    assert actual.y == pytest.approx(expected.y)


def test_pipeline_suppresses_tiny_output_changes() -> None:
    pipeline = CursorPipeline(CursorRegion(0, 0, 1, 1), 0.01, 0.05)
    first = pipeline.update(Point2D(0.5, 0.5), 0.0)
    tiny = pipeline.update(Point2D(0.51, 0.5), 1.0)
    assert first.moved
    assert not tiny.moved
    assert tiny.output_point == first.output_point


def test_pipeline_reset_reacquires_without_stale_interpolation() -> None:
    pipeline = CursorPipeline(CursorRegion(0, 0, 1, 1), 10.0, 0.0)
    pipeline.update(Point2D(0, 0), 0.0)
    pipeline.reset()
    reacquired = pipeline.update(Point2D(1, 1), 0.1)
    assert reacquired.smoothed_point == Point2D(1, 1)
    assert reacquired.output_point == Point2D(1, 1)


def test_pipeline_freeze_keeps_pre_pinch_output() -> None:
    pipeline = CursorPipeline(CursorRegion(0, 0, 1, 1), 0.01, 0.0)
    before = pipeline.update(Point2D(0.25, 0.25), 0.0)
    frozen = pipeline.update(Point2D(0.75, 0.75), 0.1, freeze=True)
    assert frozen.frozen
    assert not frozen.moved
    assert frozen.output_point == before.output_point


def test_resume_reseeds_smoothing_from_frozen_output() -> None:
    pipeline = CursorPipeline(CursorRegion(0, 0, 1, 1), 0.1, 0.0)
    before = pipeline.update(Point2D(0.25, 0.25), 0.0)
    pipeline.update(Point2D(0.75, 0.75), 0.1, freeze=True)
    pipeline.resume_from_frozen_output(0.2)
    resumed = pipeline.update(Point2D(0.75, 0.75), 0.2)
    assert resumed.output_point == before.output_point
    later = pipeline.update(Point2D(0.75, 0.75), 0.3)
    assert before.output_point.x < later.output_point.x < 0.75
