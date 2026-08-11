"""Deterministic fake paper lifecycle downstream of route decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.accounting.ledger import (
    Ledger,
    LedgerEvent,
    append_decision_event,
    append_paper_capture_closed_event,
    append_paper_capture_opened_event,
    append_paper_rejection_event,
    append_paper_settlement_observed_event,
)
from core.domain.contracts import (
    Capture,
    DecisionResult,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus
from core.domain.state_machine import transition_capture


_OPEN_TARGET_STATES = (
    CaptureState.UNDERWRITING,
    CaptureState.APPROVED,
    CaptureState.ENTERING,
    CaptureState.HEDGED,
    CaptureState.WAITING_SETTLEMENT,
)
_SETTLEMENT_TARGET_STATES = (CaptureState.SETTLED,)
_CLOSE_TARGET_STATES = (CaptureState.EXITING, CaptureState.CLOSED)
_STARTED_ATTRIBUTION = "entry_paper_eligible_decision"
_BLOCKED_ATTRIBUTION = "paper_start_blocked_by_decision"
_MODE_BLOCKER = "decision_mode_not_entry"
_STATUS_BLOCKER = "decision_status_not_paper_eligible"


@dataclass(frozen=True, slots=True)
class PaperResultExplanation:
    """Decision-derived fake paper start attribution and PnL components."""

    route_id: str
    decision_mode: EvaluationMode
    decision_status: RouteStatus
    decision_reasons: tuple[RejectReason, ...]
    paper_started: bool
    paper_start_attribution: str
    paper_start_blockers: tuple[str, ...]
    expected_funding_usd: Decimal | None
    total_fees_usd: Decimal | None
    simulated_roundtrip_cost_usd: Decimal | None
    net_profit_usd: Decimal | None


@dataclass(frozen=True, slots=True)
class PaperRunResult:
    """Outcome of one deterministic fake paper lifecycle attempt."""

    decision: DecisionResult
    started: bool
    explanation: PaperResultExplanation
    capture: Capture | None
    state_path: tuple[CaptureState, ...]
    ledger_events: tuple[LedgerEvent, ...]


def _advance_capture(
    capture: Capture,
    targets: tuple[CaptureState, ...],
) -> tuple[Capture, tuple[CaptureState, ...]]:
    path = [capture.state]
    advanced = capture
    for target in targets:
        advanced = transition_capture(advanced, target)
        path.append(advanced.state)
    return advanced, tuple(path)


def _decimal_entry_ev_component(decision: DecisionResult, field_name: str) -> Decimal | None:
    if decision.entry_ev is None:
        return None
    value = getattr(decision.entry_ev, field_name, None)
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise ValueError(f"decision.entry_ev.{field_name} must be a Decimal")
    return value


def _decision_net_profit(decision: DecisionResult) -> Decimal | None:
    if decision.net_profit_usd is None:
        return _decimal_entry_ev_component(decision, "net_profit_usd")
    if not isinstance(decision.net_profit_usd, Decimal):
        raise ValueError("decision.net_profit_usd must be a Decimal")
    return decision.net_profit_usd


def _build_paper_result_explanation(decision: DecisionResult) -> PaperResultExplanation:
    blockers = []
    if decision.mode is not EvaluationMode.ENTRY:
        blockers.append(_MODE_BLOCKER)
    if decision.status is not RouteStatus.PAPER_ELIGIBLE:
        blockers.append(_STATUS_BLOCKER)
    paper_started = not blockers

    return PaperResultExplanation(
        route_id=decision.route_id,
        decision_mode=decision.mode,
        decision_status=decision.status,
        decision_reasons=tuple(decision.reasons),
        paper_started=paper_started,
        paper_start_attribution=_STARTED_ATTRIBUTION if paper_started else _BLOCKED_ATTRIBUTION,
        paper_start_blockers=tuple(blockers),
        expected_funding_usd=_decimal_entry_ev_component(decision, "expected_funding_usd"),
        total_fees_usd=_decimal_entry_ev_component(decision, "total_fees_usd"),
        simulated_roundtrip_cost_usd=_decimal_entry_ev_component(
            decision,
            "simulated_roundtrip_cost_usd",
        ),
        net_profit_usd=_decision_net_profit(decision),
    )


def _decimal_payload_value(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _paper_result_explanation_payload(
    explanation: PaperResultExplanation,
) -> Mapping[str, Any]:
    return {
        "route_id": explanation.route_id,
        "decision_mode": explanation.decision_mode.value,
        "decision_status": explanation.decision_status.value,
        "decision_reasons": tuple(reason.value for reason in explanation.decision_reasons),
        "paper_started": explanation.paper_started,
        "paper_start_attribution": explanation.paper_start_attribution,
        "paper_start_blockers": explanation.paper_start_blockers,
        "pnl_explanation": {
            "expected_funding_usd": _decimal_payload_value(explanation.expected_funding_usd),
            "total_fees_usd": _decimal_payload_value(explanation.total_fees_usd),
            "simulated_roundtrip_cost_usd": _decimal_payload_value(
                explanation.simulated_roundtrip_cost_usd,
            ),
            "net_profit_usd": _decimal_payload_value(explanation.net_profit_usd),
        },
    }


def run_paper_lifecycle(
    *,
    route: RouteCandidate,
    decision: DecisionResult,
    funding_settlement_at: datetime,
    ledger: Ledger,
) -> PaperRunResult:
    """Run one fake paper capture lifecycle from an existing route decision."""

    validate_timezone_aware_datetime(funding_settlement_at, "funding_settlement_at")
    if decision.route_id != route.route_id:
        raise ValueError("paper lifecycle route_id must match decision.route_id")
    if decision.capture_plan is not None:
        raise ValueError("paper lifecycle must not consume live CapturePlan decisions")

    explanation = _build_paper_result_explanation(decision)
    explanation_payload = _paper_result_explanation_payload(explanation)
    events = [append_decision_event(ledger, decision)]
    if not explanation.paper_started:
        events.append(
            append_paper_rejection_event(
                ledger,
                decision,
                paper_result_explanation=explanation_payload,
            )
        )
        return PaperRunResult(
            decision=decision,
            started=False,
            explanation=explanation,
            capture=None,
            state_path=(),
            ledger_events=tuple(events),
        )

    capture = Capture(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=funding_settlement_at,
    )

    capture, opened_path = _advance_capture(capture, _OPEN_TARGET_STATES)
    events.append(
        append_paper_capture_opened_event(
            ledger,
            capture=capture,
            state_path=opened_path,
            recorded_at=decision.decided_at,
            paper_result_explanation=explanation_payload,
        )
    )

    capture, settlement_path = _advance_capture(capture, _SETTLEMENT_TARGET_STATES)
    events.append(
        append_paper_settlement_observed_event(
            ledger,
            capture=capture,
            state_path=settlement_path,
            recorded_at=funding_settlement_at,
        )
    )

    capture, close_path = _advance_capture(capture, _CLOSE_TARGET_STATES)
    events.append(
        append_paper_capture_closed_event(
            ledger,
            capture=capture,
            state_path=close_path,
            recorded_at=funding_settlement_at,
        )
    )

    full_path = opened_path + settlement_path[1:] + close_path[1:]
    return PaperRunResult(
        decision=decision,
        started=True,
        explanation=explanation,
        capture=capture,
        state_path=full_path,
        ledger_events=tuple(events),
    )
