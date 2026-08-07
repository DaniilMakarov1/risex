"""Deterministic fake paper lifecycle downstream of route decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
from core.domain.enums import CaptureState, EvaluationMode, RouteStatus
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


@dataclass(frozen=True, slots=True)
class PaperRunResult:
    """Outcome of one deterministic fake paper lifecycle attempt."""

    decision: DecisionResult
    started: bool
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

    events = [append_decision_event(ledger, decision)]
    if decision.status is not RouteStatus.PAPER_ELIGIBLE or decision.mode is not EvaluationMode.ENTRY:
        events.append(append_paper_rejection_event(ledger, decision))
        return PaperRunResult(
            decision=decision,
            started=False,
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
        capture=capture,
        state_path=full_path,
        ledger_events=tuple(events),
    )
