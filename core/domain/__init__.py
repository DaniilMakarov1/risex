"""Core domain contracts and lifecycle primitives."""

from core.domain.contracts import (
    Capture,
    CapturePlan,
    DecisionResult,
    ExecutableQuote,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import CaptureState, EvaluationMode, RouteStatus
from core.domain.state_machine import (
    ALLOWED_CAPTURE_TRANSITIONS,
    EMERGENCY_FLATTENABLE_CAPTURE_STATES,
    FAILABLE_CAPTURE_STATES,
    TERMINAL_CAPTURE_STATES,
    InvalidCaptureTransition,
    is_capture_transition_allowed,
    is_terminal_capture_state,
    transition_capture,
    validate_capture_transition,
)

__all__ = [
    "ALLOWED_CAPTURE_TRANSITIONS",
    "Capture",
    "CapturePlan",
    "CaptureState",
    "DecisionResult",
    "EMERGENCY_FLATTENABLE_CAPTURE_STATES",
    "EvaluationMode",
    "ExecutableQuote",
    "FAILABLE_CAPTURE_STATES",
    "InvalidCaptureTransition",
    "RouteCandidate",
    "RouteStatus",
    "TERMINAL_CAPTURE_STATES",
    "VenueSnapshot",
    "is_capture_transition_allowed",
    "is_terminal_capture_state",
    "transition_capture",
    "validate_capture_transition",
]
