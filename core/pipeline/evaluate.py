"""Single route decision pipeline."""

from __future__ import annotations

from datetime import UTC, datetime

from core.accounting.ledger import InMemoryLedger, append_decision_event
from core.config.product_rules import ProductRules
from core.domain.contracts import Capture, CapturePlan, DecisionResult, RouteCandidate, VenueSnapshot
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus
from core.economics.ev import calculate_entry_ev
from core.risk.gates import (
    check_live_capture_allowed,
    check_min_leg_notional,
    check_min_net_profit,
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
    except ValueError:
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

    live_allowed, live_reason = check_live_capture_allowed(active_rules)
    if mode is EvaluationMode.ENTRY and live_allowed:
        capture = Capture(
            capture_id=route.capture_id,
            route_id=route.route_id,
            settlement_time=snapshot.captured_at,
            state=CaptureState.APPROVED,
        )
        capture_plan = CapturePlan(
            plan_id=f"plan-{route.capture_id}",
            capture=capture,
            created_at=datetime.now(UTC),
        )
        decision = DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.LIVE_ELIGIBLE,
            reasons=(),
            net_profit_usd=entry_ev.net_profit_usd,
            entry_ev=entry_ev,
            capture_plan=capture_plan,
        )
    else:
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
