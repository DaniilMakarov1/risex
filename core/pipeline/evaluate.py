"""Single route decision pipeline."""

from __future__ import annotations

from collections.abc import Sequence

from core.accounting.ledger import InMemoryLedger, append_decision_event
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
    DecisionResult,
    ExecutionCapabilityEvidence,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.economics.errors import EconomicsInputError
from core.economics.ev import calculate_entry_ev
from core.risk.gates import (
    check_live_capture_allowed,
    check_min_leg_notional,
    check_min_net_profit,
    check_route_snapshot_alignment,
    check_snapshot_executability,
)


def _reject(
    *,
    route: RouteCandidate,
    mode: EvaluationMode,
    reason: RejectReason,
    ledger: InMemoryLedger | None,
) -> DecisionResult:
    decision = DecisionResult(
        route_id=route.route_id,
        mode=mode,
        status=RouteStatus.REJECTED,
        reasons=(reason,),
    )
    if ledger is not None:
        append_decision_event(ledger, decision)
    return decision


def evaluate_route(
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    mode: EvaluationMode,
    *,
    rules: ProductRules | None = None,
    ledger: InMemoryLedger | None = None,
    ledger_explicitly_reconciled: bool = False,
    capture_plan_evidence: Sequence[CapturePlanFreshnessEvidence] | None = None,
    execution_capability_evidence: Sequence[ExecutionCapabilityEvidence] | None = None,
) -> DecisionResult:
    """Evaluate one fake route snapshot without exchange APIs or order placement."""

    active_rules = rules or ProductRules()

    ok, reason = check_min_leg_notional(route, active_rules)
    if not ok:
        return _reject(
            route=route,
            mode=mode,
            reason=reason or RejectReason.MIN_LEG_NOTIONAL_NOT_MET,
            ledger=ledger,
        )

    ok, reason = check_route_snapshot_alignment(route, snapshot)
    if not ok:
        return _reject(
            route=route,
            mode=mode,
            reason=reason or RejectReason.TECHNICALLY_NOT_EXECUTABLE,
            ledger=ledger,
        )

    ok, reason = check_snapshot_executability(snapshot, active_rules)
    if not ok:
        return _reject(
            route=route,
            mode=mode,
            reason=reason or RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL,
            ledger=ledger,
        )

    try:
        entry_ev = calculate_entry_ev(snapshot)
    except EconomicsInputError:
        return _reject(
            route=route,
            mode=mode,
            reason=RejectReason.REQUIRED_LIVE_DATA_MISSING,
            ledger=ledger,
        )
    ok, reason = check_min_net_profit(entry_ev.net_profit_usd, active_rules)
    if not ok:
        decision = DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.REJECTED,
            reasons=(reason or RejectReason.MIN_NET_PROFIT_NOT_MET,),
            net_profit_usd=entry_ev.net_profit_usd,
            entry_ev=entry_ev,
        )
        if ledger is not None:
            append_decision_event(ledger, decision)
        return decision

    _, live_reason = check_live_capture_allowed(
        active_rules,
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        ledger_explicitly_reconciled=ledger_explicitly_reconciled,
        capture_plan_evidence=capture_plan_evidence,
        execution_capability_evidence=execution_capability_evidence,
    )
    reasons = (live_reason,) if mode is EvaluationMode.ENTRY and live_reason else ()
    decision = DecisionResult(
        route_id=route.route_id,
        mode=mode,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=reasons,
        net_profit_usd=entry_ev.net_profit_usd,
        entry_ev=entry_ev,
        capture_plan=None,
    )

    if ledger is not None:
        append_decision_event(ledger, decision)
    return decision
