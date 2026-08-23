import pytest

from gesture_controls.gestures import PointerPoseGate


def test_pointer_gate_activates_without_a_time_delay() -> None:
    gate = PointerPoseGate(0.18, 0.10)
    update = gate.update(0.18)
    assert update.active
    assert update.index_extension_ratio == 0.18


def test_pointer_gate_uses_release_hysteresis() -> None:
    gate = PointerPoseGate(0.18, 0.10)
    gate.update(0.20)
    assert gate.update(0.11).active
    assert not gate.update(0.09).active
    assert not gate.update(0.17).active
    assert gate.update(0.19).active


def test_pointer_gate_reset_requires_activation_again() -> None:
    gate = PointerPoseGate(0.18, 0.10)
    gate.update(0.20)
    gate.reset()
    assert not gate.update(0.15).active


@pytest.mark.parametrize("activation, release", [(0.1, 0.1), (0.1, -0.1)])
def test_pointer_gate_rejects_invalid_thresholds(
    activation: float, release: float
) -> None:
    with pytest.raises(ValueError, match="pointer extension"):
        PointerPoseGate(activation, release)
