"""Non-sending execution planning evidence."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    ExecutionCapabilityEvidence,
    OrderSide,
    RouteCandidate,
    validate_order_side,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.risk.gates import (
    check_capture_plan_freshness_gate,
    check_execution_capability_gate,
)

if TYPE_CHECKING:
    from core.accounting.reconciliation import LedgerReconciliationResult
    from core.monitoring.funding_settlement import FundingSettlementVerificationResult


@dataclass(frozen=True, slots=True)
class NonSendingExecutionPlan:
    """Evidence-only intended entry and unwind actions for one Capture."""

    capture_id: str
    route_id: str
    settlement_time: datetime
    planned_at: datetime
    valid_until: datetime
    risex_venue: str
    risex_symbol: str
    risex_entry_side: OrderSide
    risex_unwind_side: OrderSide
    hedge_venue: str
    hedge_symbol: str
    hedge_entry_side: OrderSide
    hedge_unwind_side: OrderSide
    target_notional_usd: Decimal
    capture_plan_id: str
    capture_plan_version: str
    route_decision_event_sequence: int
    funding_verification_event_sequence: int
    ledger_reconciliation_event_sequence: int
    execution_capability_checked_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "capture_id",
            "route_id",
            "risex_venue",
            "risex_symbol",
            "hedge_venue",
            "hedge_symbol",
            "capture_plan_id",
            "capture_plan_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        validate_timezone_aware_datetime(self.settlement_time, "settlement_time")
        validate_timezone_aware_datetime(self.planned_at, "planned_at")
        validate_timezone_aware_datetime(self.valid_until, "valid_until")
        validate_timezone_aware_datetime(
            self.execution_capability_checked_at,
            "execution_capability_checked_at",
        )
        if self.valid_until <= self.planned_at:
            raise ValueError("valid_until must be after planned_at")
        for side in (
            self.risex_entry_side,
            self.risex_unwind_side,
            self.hedge_entry_side,
            self.hedge_unwind_side,
        ):
            validate_order_side(side)
        if self.risex_entry_side == self.risex_unwind_side:
            raise ValueError("risex unwind side must oppose entry side")
        if self.hedge_entry_side == self.hedge_unwind_side:
            raise ValueError("hedge unwind side must oppose entry side")
        if not isinstance(self.target_notional_usd, Decimal):
            raise ValueError("target_notional_usd must be a Decimal")
        if (
            not self.target_notional_usd.is_finite()
            or self.target_notional_usd <= Decimal("0")
        ):
            raise ValueError("target_notional_usd must be a positive finite Decimal")
        for field_name in (
            "route_decision_event_sequence",
            "funding_verification_event_sequence",
            "ledger_reconciliation_event_sequence",
        ):
            if not _positive_sequence(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be a positive integer")


def _opposite_side(side: OrderSide) -> OrderSide:
    return "sell" if side == "buy" else "buy"


def _timezone_aware(value: object) -> bool:
    if not isinstance(value, datetime):
        return False
    try:
        validate_timezone_aware_datetime(value, "datetime")
    except ValueError:
        return False
    return True


def _positive_sequence(value: object) -> bool:
    return type(value) is int and value > 0


def _funding_verification_is_verified(
    value: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
) -> bool:
    from core.monitoring.funding_settlement import FundingSettlementVerificationResult

    if not isinstance(value, FundingSettlementVerificationResult):
        return False
    return (
        value.capture_id == route.capture_id
        and value.route_id == route.route_id
        and value.settlement_time == settlement_time
        and value.verified is True
    )


def _ledger_reconciliation_is_current(
    value: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
) -> bool:
    from core.accounting.reconciliation import LedgerReconciliationResult

    if not isinstance(value, LedgerReconciliationResult):
        return False
    route_decision_sequence = value.route_decision_event_sequence
    funding_verification_sequence = value.funding_verification_event_sequence
    checked_sequences = value.checked_event_sequences
    if not isinstance(checked_sequences, Sequence):
        return False
    try:
        checked_sequence_values = tuple(checked_sequences)
    except TypeError:
        return False

    return (
        value.capture_id == route.capture_id
        and value.route_id == route.route_id
        and value.settlement_time == settlement_time
        and value.reconciled is True
        and _positive_sequence(route_decision_sequence)
        and _positive_sequence(funding_verification_sequence)
        and route_decision_sequence in checked_sequence_values
        and funding_verification_sequence in checked_sequence_values
    )


def plan_execution_without_orders(
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    decision: DecisionResult | None,
    funding_verification: FundingSettlementVerificationResult | None,
    ledger_reconciliation: LedgerReconciliationResult | None,
    capture_plan_evidence: Sequence[CapturePlanFreshnessEvidence] | None,
    execution_capability_evidence: Sequence[ExecutionCapabilityEvidence] | None,
    planned_at: datetime,
) -> tuple[NonSendingExecutionPlan | None, RejectReason | None]:
    """Build one non-executable plan from already-derived prerequisite evidence."""

    if (
        not isinstance(capture, Capture)
        or not isinstance(route, RouteCandidate)
        or not _timezone_aware(settlement_time)
        or not _timezone_aware(planned_at)
    ):
        return None, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if (
        capture.capture_id != route.capture_id
        or capture.route_id != route.route_id
        or capture.settlement_time != settlement_time
    ):
        return None, RejectReason.REQUIRED_LIVE_DATA_MISSING

    if (
        not isinstance(decision, DecisionResult)
        or decision.route_id != route.route_id
        or decision.mode is not EvaluationMode.ENTRY
        or decision.status is not RouteStatus.PAPER_ELIGIBLE
        or decision.capture_plan is not None
    ):
        return None, RejectReason.REQUIRED_LIVE_DATA_MISSING

    if not _funding_verification_is_verified(
        funding_verification,
        route=route,
        settlement_time=settlement_time,
    ):
        return None, RejectReason.REQUIRED_LIVE_DATA_MISSING

    if not _ledger_reconciliation_is_current(
        ledger_reconciliation,
        route=route,
        settlement_time=settlement_time,
    ):
        return None, RejectReason.LEDGER_NOT_RECONCILED

    if capture_plan_evidence is not None and not isinstance(capture_plan_evidence, Sequence):
        return None, RejectReason.CAPTURE_PLAN_NOT_FRESH
    plan_ok, plan_reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=settlement_time,
        evaluated_at=planned_at,
        plan_evidence=capture_plan_evidence,
    )
    if not plan_ok:
        return None, plan_reason or RejectReason.CAPTURE_PLAN_NOT_FRESH

    if execution_capability_evidence is not None and not isinstance(
        execution_capability_evidence,
        Sequence,
    ):
        return None, RejectReason.REQUIRED_LIVE_DATA_MISSING
    execution_ok, execution_reason = check_execution_capability_gate(
        route=route,
        settlement_time=settlement_time,
        evaluated_at=planned_at,
        execution_evidence=execution_capability_evidence,
    )
    if not execution_ok:
        return None, execution_reason or RejectReason.REQUIRED_LIVE_DATA_MISSING

    plan_evidence = capture_plan_evidence[0]
    execution_evidence = execution_capability_evidence[0]
    ledger_reconciliation_sequence = plan_evidence.ledger_reconciliation_event_sequence
    if not _positive_sequence(ledger_reconciliation_sequence):
        return None, RejectReason.CAPTURE_PLAN_NOT_FRESH

    return (
        NonSendingExecutionPlan(
            capture_id=route.capture_id,
            route_id=route.route_id,
            settlement_time=settlement_time,
            planned_at=planned_at,
            valid_until=min(plan_evidence.valid_until, execution_evidence.valid_until),
            risex_venue=route.risex_venue,
            risex_symbol=route.risex_symbol,
            risex_entry_side=route.risex_entry_side,
            risex_unwind_side=_opposite_side(route.risex_entry_side),
            hedge_venue=route.hedge_venue,
            hedge_symbol=route.hedge_symbol,
            hedge_entry_side=route.hedge_entry_side,
            hedge_unwind_side=_opposite_side(route.hedge_entry_side),
            target_notional_usd=route.target_notional_usd,
            capture_plan_id=plan_evidence.plan_id,
            capture_plan_version=plan_evidence.plan_version,
            route_decision_event_sequence=ledger_reconciliation.route_decision_event_sequence,
            funding_verification_event_sequence=(
                ledger_reconciliation.funding_verification_event_sequence
            ),
            ledger_reconciliation_event_sequence=ledger_reconciliation_sequence,
            execution_capability_checked_at=execution_evidence.checked_at,
        ),
        None,
    )
