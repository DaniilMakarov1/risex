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


class ValueSource(StrEnum):
    """Allowed source labels for config-facing and economics input values."""

    DOCUMENTED = "DOCUMENTED"
    OBSERVED = "OBSERVED"
    ESTIMATED_FROM_ORDERBOOK = "ESTIMATED_FROM_ORDERBOOK"
    ESTIMATED_FROM_LAST_VALUE = "ESTIMATED_FROM_LAST_VALUE"
    USER_CONFIGURED = "USER_CONFIGURED"
    UNKNOWN = "UNKNOWN"


class RejectReason(StrEnum):
    """Centralized route rejection and live-gate reason contract."""

    TECHNICALLY_NOT_EXECUTABLE = "TECHNICALLY_NOT_EXECUTABLE"
    REQUIRED_LIVE_DATA_MISSING = "REQUIRED_LIVE_DATA_MISSING"
    MIN_NET_PROFIT_NOT_MET = "MIN_NET_PROFIT_NOT_MET"
    USER_RULE_VIOLATED = "USER_RULE_VIOLATED"
    VENUE_MARKET_OR_MODE_DISABLED = "VENUE_MARKET_OR_MODE_DISABLED"
    LEDGER_NOT_RECONCILED = "LEDGER_NOT_RECONCILED"
    CAPTURE_PLAN_NOT_FRESH = "CAPTURE_PLAN_NOT_FRESH"
    MIN_LEG_NOTIONAL_NOT_MET = "MIN_LEG_NOTIONAL_NOT_MET"
    ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL = "ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL"
    LIVE_TRADING_DISABLED = "LIVE_TRADING_DISABLED"
    LIVE_GATES_NOT_IMPLEMENTED = "LIVE_GATES_NOT_IMPLEMENTED"
