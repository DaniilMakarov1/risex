"""Guarded live runner workflow that never places orders."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    Capture,
    LiveGateEvidenceBundle,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import RejectReason
from core.execution.planning import NonSendingExecutionPlan
from core.risk.gates import check_live_gate_evidence_bundle


@dataclass(frozen=True, slots=True)
class GuardedLiveRunnerResult:
    """Deterministic blocked or no-order-ready live runner outcome."""

    no_order_ready: bool
    blocked_reason: RejectReason | None
    capture_id: str | None
    route_id: str | None
    settlement_time: datetime | None
    evaluated_at: datetime | None

    def __post_init__(self) -> None:
        if type(self.no_order_ready) is not bool:
            raise ValueError("no_order_ready must be a bool")
        if self.no_order_ready and self.blocked_reason is not None:
            raise ValueError("no-order ready results cannot carry a blocked reason")
        if self.no_order_ready and (
            self.capture_id is None
            or self.route_id is None
            or self.settlement_time is None
            or self.evaluated_at is None
        ):
            raise ValueError("no-order ready results require exact identity")
        if not self.no_order_ready and not isinstance(self.blocked_reason, RejectReason):
            raise ValueError("blocked results require a RejectReason")
        for field_name in ("capture_id", "route_id"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be non-empty when provided")
        for field_name in ("settlement_time", "evaluated_at"):
            value = getattr(self, field_name)
            if value is not None:
                validate_timezone_aware_datetime(value, field_name)


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


def _positive_sequence_values(value: object) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return False
    return len(value) > 0 and all(_positive_sequence(item) for item in value)


def _opposite_side(side: str) -> str | None:
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    return None


def _result_identity(
    *,
    capture: object,
    route: object,
    settlement_time: object,
    evaluated_at: object,
) -> tuple[str | None, str | None, datetime | None, datetime | None]:
    capture_id = capture.capture_id if isinstance(capture, Capture) else None
    route_id = route.route_id if isinstance(route, RouteCandidate) else None
    settlement = settlement_time if _timezone_aware(settlement_time) else None
    evaluated = evaluated_at if _timezone_aware(evaluated_at) else None
    return capture_id, route_id, settlement, evaluated


def _blocked(
    reason: RejectReason,
    *,
    capture: object,
    route: object,
    settlement_time: object,
    evaluated_at: object,
) -> GuardedLiveRunnerResult:
    capture_id, route_id, settlement, evaluated = _result_identity(
        capture=capture,
        route=route,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
    )
    return GuardedLiveRunnerResult(
        no_order_ready=False,
        blocked_reason=reason,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement,
        evaluated_at=evaluated,
    )


def _ready(
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    evaluated_at: datetime,
) -> GuardedLiveRunnerResult:
    return GuardedLiveRunnerResult(
        no_order_ready=True,
        blocked_reason=None,
        capture_id=capture.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
    )


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
        and _positive_sequence_values(value.checkpoint_event_sequences)
        and _positive_sequence(value.settlement_event_sequence)
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
    if not _positive_sequence(value.route_decision_event_sequence):
        return False
    if not _positive_sequence(value.funding_verification_event_sequence):
        return False
    if not _positive_sequence_values(value.checked_event_sequences):
        return False
    return (
        value.capture_id == route.capture_id
        and value.route_id == route.route_id
        and value.settlement_time == settlement_time
        and value.reconciled is True
        and value.route_decision_event_sequence in value.checked_event_sequences
        and value.funding_verification_event_sequence in value.checked_event_sequences
    )


def _plan_matches_route(
    plan: NonSendingExecutionPlan,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
) -> RejectReason | None:
    if (
        plan.capture_id != route.capture_id
        or plan.route_id != route.route_id
        or plan.settlement_time != settlement_time
    ):
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    if (
        plan.risex_venue != route.risex_venue
        or plan.risex_symbol != route.risex_symbol
        or plan.risex_entry_side != route.risex_entry_side
        or plan.risex_unwind_side != _opposite_side(route.risex_entry_side)
        or plan.hedge_venue != route.hedge_venue
        or plan.hedge_symbol != route.hedge_symbol
        or plan.hedge_entry_side != route.hedge_entry_side
        or plan.hedge_unwind_side != _opposite_side(route.hedge_entry_side)
        or plan.target_notional_usd != route.target_notional_usd
    ):
        return RejectReason.TECHNICALLY_NOT_EXECUTABLE
    return None


def _plan_matches_prerequisites(
    plan: NonSendingExecutionPlan,
    *,
    live_gate_evidence_bundle: LiveGateEvidenceBundle,
    ledger_reconciliation: object,
    evaluated_at: datetime,
) -> RejectReason | None:
    if not isinstance(live_gate_evidence_bundle, LiveGateEvidenceBundle):
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    if len(live_gate_evidence_bundle.capture_plan_evidence) != 1:
        return RejectReason.CAPTURE_PLAN_NOT_FRESH
    if len(live_gate_evidence_bundle.execution_capability_evidence) != 1:
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    plan_evidence = live_gate_evidence_bundle.capture_plan_evidence[0]
    execution_evidence = live_gate_evidence_bundle.execution_capability_evidence[0]
    if plan.planned_at > evaluated_at or evaluated_at >= plan.valid_until:
        return RejectReason.CAPTURE_PLAN_NOT_FRESH
    expected_valid_until = min(plan_evidence.valid_until, execution_evidence.valid_until)
    if plan.valid_until != expected_valid_until:
        return RejectReason.CAPTURE_PLAN_NOT_FRESH
    if (
        plan.planned_at != plan_evidence.planned_at
        or plan.capture_plan_id != plan_evidence.plan_id
        or plan.capture_plan_version != plan_evidence.plan_version
        or plan.ledger_reconciliation_event_sequence
        != plan_evidence.ledger_reconciliation_event_sequence
    ):
        return RejectReason.CAPTURE_PLAN_NOT_FRESH
    if plan.execution_capability_checked_at != execution_evidence.checked_at:
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    if (
        plan.route_decision_event_sequence
        != getattr(ledger_reconciliation, "route_decision_event_sequence", None)
        or plan.funding_verification_event_sequence
        != getattr(ledger_reconciliation, "funding_verification_event_sequence", None)
    ):
        return RejectReason.LEDGER_NOT_RECONCILED
    return None


def run_guarded_live_without_orders(
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    non_sending_plan: NonSendingExecutionPlan | None,
    funding_verification: object,
    ledger_reconciliation: object,
    live_gate_evidence_bundle: LiveGateEvidenceBundle | None,
    evaluated_at: datetime,
    rules: ProductRules | None = None,
) -> GuardedLiveRunnerResult:
    """Check accepted live prerequisites and stop before executable live behavior."""

    if not isinstance(rules, ProductRules) or rules.live_trading_enabled is not True:
        return _blocked(
            RejectReason.LIVE_TRADING_DISABLED,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    if (
        not isinstance(capture, Capture)
        or not isinstance(route, RouteCandidate)
        or not _timezone_aware(settlement_time)
        or not _timezone_aware(evaluated_at)
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )
    if (
        capture.capture_id != route.capture_id
        or capture.route_id != route.route_id
        or capture.settlement_time != settlement_time
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    if not _funding_verification_is_verified(
        funding_verification,
        route=route,
        settlement_time=settlement_time,
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    if not _ledger_reconciliation_is_current(
        ledger_reconciliation,
        route=route,
        settlement_time=settlement_time,
    ):
        return _blocked(
            RejectReason.LEDGER_NOT_RECONCILED,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    bundle_ok, bundle_reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
        live_gate_evidence_bundle=live_gate_evidence_bundle,
    )
    if not bundle_ok:
        return _blocked(
            bundle_reason or RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    if type(non_sending_plan) is not NonSendingExecutionPlan:
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )
    plan_reason = _plan_matches_route(
        non_sending_plan,
        route=route,
        settlement_time=settlement_time,
    )
    if plan_reason is not None:
        return _blocked(
            plan_reason,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )
    prerequisite_reason = _plan_matches_prerequisites(
        non_sending_plan,
        live_gate_evidence_bundle=live_gate_evidence_bundle,
        ledger_reconciliation=ledger_reconciliation,
        evaluated_at=evaluated_at,
    )
    if prerequisite_reason is not None:
        return _blocked(
            prerequisite_reason,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            evaluated_at=evaluated_at,
        )

    return _ready(
        capture=capture,
        route=route,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
    )
