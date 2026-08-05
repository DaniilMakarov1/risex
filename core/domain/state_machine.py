"""Authoritative Capture lifecycle state machine."""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Mapping

from core.domain.contracts import Capture
from core.domain.enums import CaptureState


class InvalidCaptureTransition(ValueError):
    """Raised when a Capture lifecycle transition is not allowed."""


TERMINAL_CAPTURE_STATES = frozenset(
    {
        CaptureState.REJECTED,
        CaptureState.CLOSED,
        CaptureState.FAILED,
        CaptureState.EMERGENCY_FLATTENED,
    }
)

FAILABLE_CAPTURE_STATES = frozenset(state for state in CaptureState if state not in TERMINAL_CAPTURE_STATES)

EMERGENCY_FLATTENABLE_CAPTURE_STATES = frozenset(
    {
        CaptureState.ENTERING,
        CaptureState.PARTIALLY_ENTERED,
        CaptureState.HEDGED,
        CaptureState.WAITING_SETTLEMENT,
        CaptureState.SETTLED,
        CaptureState.EXITING,
    }
)

_NORMAL_CAPTURE_TRANSITIONS: Mapping[CaptureState, frozenset[CaptureState]] = {
    CaptureState.DISCOVERED: frozenset({CaptureState.UNDERWRITING}),
    CaptureState.UNDERWRITING: frozenset({CaptureState.APPROVED, CaptureState.REJECTED}),
    CaptureState.APPROVED: frozenset({CaptureState.ENTERING}),
    CaptureState.ENTERING: frozenset({CaptureState.PARTIALLY_ENTERED, CaptureState.HEDGED}),
    CaptureState.PARTIALLY_ENTERED: frozenset({CaptureState.HEDGED}),
    CaptureState.HEDGED: frozenset({CaptureState.WAITING_SETTLEMENT}),
    CaptureState.WAITING_SETTLEMENT: frozenset({CaptureState.SETTLED}),
    CaptureState.SETTLED: frozenset({CaptureState.EXITING}),
    CaptureState.EXITING: frozenset({CaptureState.CLOSED}),
    CaptureState.REJECTED: frozenset(),
    CaptureState.CLOSED: frozenset(),
    CaptureState.FAILED: frozenset(),
    CaptureState.EMERGENCY_FLATTENED: frozenset(),
}


def _allowed_targets(source: CaptureState) -> frozenset[CaptureState]:
    targets = set(_NORMAL_CAPTURE_TRANSITIONS[source])
    if source in FAILABLE_CAPTURE_STATES:
        targets.add(CaptureState.FAILED)
    if source in EMERGENCY_FLATTENABLE_CAPTURE_STATES:
        targets.add(CaptureState.EMERGENCY_FLATTENED)
    return frozenset(targets)


ALLOWED_CAPTURE_TRANSITIONS: Mapping[CaptureState, frozenset[CaptureState]] = MappingProxyType(
    {source: _allowed_targets(source) for source in CaptureState}
)


def is_terminal_capture_state(state: CaptureState) -> bool:
    """Return whether the state is terminal for a Capture instance."""

    return state in TERMINAL_CAPTURE_STATES


def is_capture_transition_allowed(source: CaptureState, target: CaptureState) -> bool:
    """Return whether a lifecycle transition is allowed."""

    return target in ALLOWED_CAPTURE_TRANSITIONS[source]


def validate_capture_transition(source: CaptureState, target: CaptureState) -> None:
    """Reject invalid Capture lifecycle transitions."""

    if not is_capture_transition_allowed(source, target):
        raise InvalidCaptureTransition(f"Invalid Capture transition: {source.value} -> {target.value}")


def transition_capture(capture: Capture, target: CaptureState) -> Capture:
    """Return a new Capture advanced to the target lifecycle state."""

    validate_capture_transition(capture.state, target)
    return replace(capture, state=target)
