"""Shared domain enums for route evaluation and capture lifecycle."""

from __future__ import annotations

from enum import StrEnum


class RouteStatus(StrEnum):
    """Allowed route statuses.

    Keep this enum intentionally small. Do not add CANARY_ELIGIBLE.
    """

    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"
    LIVE_ELIGIBLE = "LIVE_ELIGIBLE"
    REJECTED = "REJECTED"


class CaptureState(StrEnum):
    """Lifecycle states for one Capture.

    Keep these states separate from RouteStatus eligibility decisions.
    """

    DISCOVERED = "DISCOVERED"
    UNDERWRITING = "UNDERWRITING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    ENTERING = "ENTERING"
    PARTIALLY_ENTERED = "PARTIALLY_ENTERED"
    HEDGED = "HEDGED"
    WAITING_SETTLEMENT = "WAITING_SETTLEMENT"
    SETTLED = "SETTLED"
    EXITING = "EXITING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    EMERGENCY_FLATTENED = "EMERGENCY_FLATTENED"


class EvaluationMode(StrEnum):
    """Evaluation mode used by the shared route decision pipeline."""

    DISCOVERY = "DISCOVERY"
    ENTRY = "ENTRY"
