from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime

import pytest

from core.domain.contracts import Capture
from core.domain.enums import CaptureState
from core.domain.state_machine import (
    EMERGENCY_FLATTENABLE_CAPTURE_STATES,
    FAILABLE_CAPTURE_STATES,
    InvalidCaptureTransition,
    transition_capture,
)


def _capture(state: CaptureState = CaptureState.DISCOVERED) -> Capture:
    return Capture(
        capture_id="capture-test",
        route_id="route-test",
        settlement_time=datetime(2026, 1, 1, tzinfo=UTC),
        state=state,
    )


def test_capture_contract_uses_lifecycle_state_not_route_status() -> None:
    capture = _capture()

    assert capture.state is CaptureState.DISCOVERED
    assert not hasattr(capture, "status")


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (CaptureState.DISCOVERED, CaptureState.UNDERWRITING),
        (CaptureState.UNDERWRITING, CaptureState.APPROVED),
        (CaptureState.UNDERWRITING, CaptureState.REJECTED),
        (CaptureState.APPROVED, CaptureState.ENTERING),
        (CaptureState.ENTERING, CaptureState.PARTIALLY_ENTERED),
        (CaptureState.ENTERING, CaptureState.HEDGED),
        (CaptureState.PARTIALLY_ENTERED, CaptureState.HEDGED),
        (CaptureState.HEDGED, CaptureState.WAITING_SETTLEMENT),
        (CaptureState.WAITING_SETTLEMENT, CaptureState.SETTLED),
        (CaptureState.SETTLED, CaptureState.EXITING),
        (CaptureState.EXITING, CaptureState.CLOSED),
    ],
)
def test_valid_capture_state_transitions(source: CaptureState, target: CaptureState) -> None:
    capture = _capture(source)

    transitioned = transition_capture(capture, target)

    assert transitioned.state is target
    assert capture.state is source
    assert transitioned.capture_id == capture.capture_id


def test_any_failable_capture_state_can_transition_to_failed() -> None:
    assert FAILABLE_CAPTURE_STATES

    for state in FAILABLE_CAPTURE_STATES:
        assert transition_capture(_capture(state), CaptureState.FAILED).state is CaptureState.FAILED


def test_exposure_capture_states_can_transition_to_emergency_flattened() -> None:
    assert EMERGENCY_FLATTENABLE_CAPTURE_STATES

    for state in EMERGENCY_FLATTENABLE_CAPTURE_STATES:
        assert (
            transition_capture(_capture(state), CaptureState.EMERGENCY_FLATTENED).state
            is CaptureState.EMERGENCY_FLATTENED
        )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (CaptureState.APPROVED, CaptureState.HEDGED),
        (CaptureState.DISCOVERED, CaptureState.ENTERING),
        (CaptureState.CLOSED, CaptureState.ENTERING),
        (CaptureState.SETTLED, CaptureState.WAITING_SETTLEMENT),
        (CaptureState.REJECTED, CaptureState.APPROVED),
    ],
)
def test_invalid_capture_state_transitions(source: CaptureState, target: CaptureState) -> None:
    with pytest.raises(InvalidCaptureTransition):
        transition_capture(_capture(source), target)


def test_capture_state_transition_does_not_touch_execution_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "core.execution" or module_name.startswith("core.execution."):
            del sys.modules[module_name]

    state_machine = importlib.import_module("core.domain.state_machine")
    state_machine = importlib.reload(state_machine)

    state_machine.transition_capture(_capture(), CaptureState.UNDERWRITING)

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
