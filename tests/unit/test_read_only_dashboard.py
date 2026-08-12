from __future__ import annotations

from dataclasses import fields, replace
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

from apps.dashboard import render_capture_monitor_view
from apps.live_runner.guarded import GuardedLiveRunnerResult
from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.reconciliation import LedgerReconciliationResult
from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.ev import EntryEV
from core.execution.orders import (
    ApprovalGatedOrderPlacementResult,
    OrderPlacementApproval,
)
from core.execution.planning import NonSendingExecutionPlan
from core.monitoring.funding_settlement import FundingSettlementVerificationResult


def _fixture() -> dict[str, object]:
    route, snapshot = build_fake_route_and_snapshot()
    settlement_time = snapshot.risex_funding_settlement_at
    viewed_at = snapshot.captured_at + timedelta(seconds=45)
    capture = Capture(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
    )
    decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=(),
        net_profit_usd=Decimal("2.50"),
        entry_ev=EntryEV(
            expected_funding_usd=Decimal("7.50"),
            total_fees_usd=Decimal("3.00"),
            simulated_roundtrip_cost_usd=Decimal("2.00"),
            net_profit_usd=Decimal("2.50"),
        ),
        decided_at=snapshot.captured_at,
    )
    funding_verification = FundingSettlementVerificationResult(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        verified=True,
        reasons=(),
        checkpoint_event_sequences=(2, 3, 4, 5),
        settlement_event_sequence=6,
    )
    ledger_reconciliation = LedgerReconciliationResult(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        reconciled=True,
        reasons=(),
        route_decision_event_sequence=1,
        paper_event_sequences=(7, 8, 9),
        funding_verification_event_sequence=6,
        checked_event_sequences=(1, 2, 3, 4, 5, 6, 7, 8, 9),
    )
    plan_evidence = CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        planned_at=snapshot.captured_at,
        valid_until=snapshot.captured_at + timedelta(minutes=5),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=10,
    )
    execution_evidence = ExecutionCapabilityEvidence(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        checked_at=snapshot.captured_at,
        valid_until=snapshot.captured_at + timedelta(minutes=3),
        source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
        risex_entry_quote=snapshot.risex_entry_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
        hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
    )
    live_gate_evidence_bundle = LiveGateEvidenceBundle(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        funding_settlement_verified=True,
        ledger_explicitly_reconciled=True,
        capture_plan_evidence=(plan_evidence,),
        execution_capability_evidence=(execution_evidence,),
    )
    non_sending_plan = NonSendingExecutionPlan(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        planned_at=snapshot.captured_at,
        valid_until=execution_evidence.valid_until,
        risex_venue=route.risex_venue,
        risex_symbol=route.risex_symbol,
        risex_entry_side=route.risex_entry_side,
        risex_unwind_side="sell",
        hedge_venue=route.hedge_venue,
        hedge_symbol=route.hedge_symbol,
        hedge_entry_side=route.hedge_entry_side,
        hedge_unwind_side="buy",
        target_notional_usd=route.target_notional_usd,
        capture_plan_id=plan_evidence.plan_id,
        capture_plan_version=plan_evidence.plan_version,
        route_decision_event_sequence=1,
        funding_verification_event_sequence=6,
        ledger_reconciliation_event_sequence=10,
        execution_capability_checked_at=execution_evidence.checked_at,
    )
    guarded_readiness = GuardedLiveRunnerResult(
        no_order_ready=True,
        blocked_reason=None,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        evaluated_at=snapshot.captured_at + timedelta(seconds=30),
    )
    approval = OrderPlacementApproval(
        approval_id="approval-001",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        guarded_evaluated_at=guarded_readiness.evaluated_at,
        non_sending_plan_planned_at=non_sending_plan.planned_at,
        non_sending_plan_valid_until=non_sending_plan.valid_until,
        capture_plan_id=non_sending_plan.capture_plan_id,
        capture_plan_version=non_sending_plan.capture_plan_version,
        route_decision_event_sequence=non_sending_plan.route_decision_event_sequence,
        funding_verification_event_sequence=(
            non_sending_plan.funding_verification_event_sequence
        ),
        ledger_reconciliation_event_sequence=(
            non_sending_plan.ledger_reconciliation_event_sequence
        ),
        execution_capability_checked_at=(
            non_sending_plan.execution_capability_checked_at
        ),
        approval_granted=True,
        approved_at=guarded_readiness.evaluated_at + timedelta(seconds=5),
        valid_until=viewed_at + timedelta(minutes=1),
    )
    approval_boundary_result = ApprovalGatedOrderPlacementResult(
        boundary_invoked=True,
        blocked_reason=None,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        requested_at=viewed_at,
        approval_id=approval.approval_id,
    )
    return {
        "route": route,
        "snapshot": snapshot,
        "settlement_time": settlement_time,
        "viewed_at": viewed_at,
        "capture": capture,
        "decision": decision,
        "funding_verification": funding_verification,
        "ledger_reconciliation": ledger_reconciliation,
        "plan_evidence": plan_evidence,
        "execution_evidence": execution_evidence,
        "live_gate_evidence_bundle": live_gate_evidence_bundle,
        "non_sending_plan": non_sending_plan,
        "guarded_readiness": guarded_readiness,
        "approval": approval,
        "approval_boundary_result": approval_boundary_result,
    }


def _render(fixture: dict[str, object], **overrides: object) -> dict[str, object]:
    values = {
        "capture": fixture["capture"],
        "route": fixture["route"],
        "settlement_time": fixture["settlement_time"],
        "viewed_at": fixture["viewed_at"],
        "decision": fixture["decision"],
        "funding_verification": fixture["funding_verification"],
        "ledger_reconciliation": fixture["ledger_reconciliation"],
        "live_gate_evidence_bundle": fixture["live_gate_evidence_bundle"],
        "non_sending_plan": fixture["non_sending_plan"],
        "guarded_readiness": fixture["guarded_readiness"],
        "approval": fixture["approval"],
        "approval_boundary_result": fixture["approval_boundary_result"],
    }
    values.update(overrides)
    return render_capture_monitor_view(**values)


def _forged(value: object, *, field_name: str, replacement: object) -> object:
    forged = object.__new__(type(value))
    for field in fields(type(value)):
        object.__setattr__(forged, field.name, getattr(value, field.name))
    object.__setattr__(forged, field_name, replacement)
    return forged


def _spoof_like(real: object) -> object:
    real_type = type(real)
    spoof_type = type(
        real_type.__name__,
        (),
        {"__slots__": tuple(field.name for field in fields(real_type))},
    )
    spoof_type.__module__ = real_type.__module__
    spoof = object.__new__(spoof_type)
    for field in fields(real_type):
        object.__setattr__(spoof, field.name, getattr(real, field.name))
    return spoof


def test_exact_identity_and_existing_evidence_render_available_summary() -> None:
    fixture = _fixture()

    view = _render(fixture)

    assert view["display_state"] == "available"
    assert view["unavailable_sections"] == ()
    sections = view["sections"]
    assert sections["identity"] == {
        "display_state": "available",
        "capture_id": fixture["route"].capture_id,
        "route_id": fixture["route"].route_id,
        "settlement_time": fixture["settlement_time"].isoformat(),
        "viewed_at": fixture["viewed_at"].isoformat(),
        "capture_state": "DISCOVERED",
        "risex": {
            "venue": fixture["route"].risex_venue,
            "symbol": fixture["route"].risex_symbol,
            "entry_side": fixture["route"].risex_entry_side,
        },
        "hedge": {
            "venue": fixture["route"].hedge_venue,
            "symbol": fixture["route"].hedge_symbol,
            "entry_side": fixture["route"].hedge_entry_side,
        },
        "target_notional_usd": str(fixture["route"].target_notional_usd),
    }
    assert sections["decision"]["economics"]["net_profit_usd"] == {
        "display_state": "available",
        "value": "2.50",
    }
    assert sections["guarded_readiness"]["no_order_ready"] is True
    assert sections["approval_boundary_result"]["boundary_invoked"] is True


def test_missing_malformed_and_cross_identity_inputs_fail_closed_in_display() -> None:
    fixture = _fixture()

    missing = _render(fixture, decision=None)
    assert missing["display_state"] == "blocked"
    assert missing["sections"]["decision"]["display_state"] == "missing"
    assert missing["sections"]["decision"]["display_reason"] == (
        "decision_missing_or_malformed"
    )

    malformed = _render(fixture, non_sending_plan=SimpleNamespace())
    assert malformed["sections"]["non_sending_plan"]["display_state"] == "missing"

    cross_route = _render(
        fixture,
        funding_verification=replace(
            fixture["funding_verification"],
            route_id="other-route",
        ),
    )
    assert cross_route["sections"]["funding_verification"]["display_state"] == "blocked"
    assert cross_route["sections"]["funding_verification"]["display_reason"] == (
        "cross_identity_funding_verification"
    )

    cross_settlement = _render(
        fixture,
        live_gate_evidence_bundle=replace(
            fixture["live_gate_evidence_bundle"],
            settlement_time=fixture["settlement_time"] + timedelta(hours=8),
        ),
    )
    assert cross_settlement["sections"]["live_gate_evidence_bundle"][
        "display_state"
    ] == "blocked"
    assert cross_settlement["sections"]["live_gate_evidence_bundle"][
        "display_reason"
    ] == "cross_identity_live_gate_bundle"


def test_spoofed_module_qualname_contracts_render_missing_not_available() -> None:
    fixture = _fixture()

    for key, section_name in (
        ("non_sending_plan", "non_sending_plan"),
        ("guarded_readiness", "guarded_readiness"),
        ("approval", "approval"),
        ("approval_boundary_result", "approval_boundary_result"),
    ):
        view = _render(fixture, **{key: _spoof_like(fixture[key])})

        section = view["sections"][section_name]
        assert section["display_state"] == "missing"
        assert section["display_reason"].endswith("_missing_or_malformed")
        assert view["display_state"] == "blocked"


def test_unverified_unreconciled_and_stale_inputs_render_blocked() -> None:
    fixture = _fixture()

    unverified = _render(
        fixture,
        funding_verification=replace(fixture["funding_verification"], verified=False),
    )
    assert unverified["sections"]["funding_verification"]["display_reason"] == (
        "funding_not_verified"
    )

    unreconciled = _render(
        fixture,
        ledger_reconciliation=replace(fixture["ledger_reconciliation"], reconciled=False),
    )
    assert unreconciled["sections"]["ledger_reconciliation"]["display_reason"] == (
        "ledger_not_reconciled"
    )

    stale_plan = _render(
        fixture,
        viewed_at=fixture["non_sending_plan"].valid_until,
    )
    assert stale_plan["sections"]["non_sending_plan"]["display_reason"] == (
        "non_sending_plan_stale"
    )


def test_blocked_guarded_readiness_and_boundary_result_are_displayed_without_retry() -> None:
    fixture = _fixture()
    guarded_blocked = GuardedLiveRunnerResult(
        no_order_ready=False,
        blocked_reason=RejectReason.LIVE_TRADING_DISABLED,
        capture_id=fixture["route"].capture_id,
        route_id=fixture["route"].route_id,
        settlement_time=fixture["settlement_time"],
        evaluated_at=fixture["guarded_readiness"].evaluated_at,
    )
    boundary_blocked = ApprovalGatedOrderPlacementResult(
        boundary_invoked=False,
        blocked_reason=RejectReason.USER_RULE_VIOLATED,
        capture_id=fixture["route"].capture_id,
        route_id=fixture["route"].route_id,
        settlement_time=fixture["settlement_time"],
        requested_at=fixture["viewed_at"],
        approval_id=fixture["approval"].approval_id,
    )

    view = _render(
        fixture,
        guarded_readiness=guarded_blocked,
        approval_boundary_result=boundary_blocked,
    )

    assert view["sections"]["guarded_readiness"]["display_state"] == "blocked"
    assert view["sections"]["guarded_readiness"]["blocked_reason"] == (
        "LIVE_TRADING_DISABLED"
    )
    assert view["sections"]["approval_boundary_result"]["display_state"] == "blocked"
    assert view["sections"]["approval_boundary_result"]["blocked_reason"] == (
        "USER_RULE_VIOLATED"
    )


def test_false_or_stale_approval_renders_blocked() -> None:
    fixture = _fixture()

    false_approval = _render(
        fixture,
        approval=_forged(
            fixture["approval"],
            field_name="approval_granted",
            replacement=False,
        ),
    )
    assert false_approval["sections"]["approval"]["display_reason"] == (
        "approval_not_granted"
    )

    stale_approval = _render(
        fixture,
        viewed_at=fixture["approval"].valid_until,
    )
    assert stale_approval["sections"]["approval"]["display_reason"] == (
        "approval_stale_or_future"
    )


def test_unknown_or_missing_economics_are_preserved_as_missing_not_zero() -> None:
    fixture = _fixture()
    unknown_decision = replace(fixture["decision"], net_profit_usd=None, entry_ev=None)

    view = _render(fixture, decision=unknown_decision)

    economics = view["sections"]["decision"]["economics"]
    assert economics["net_profit_usd"] == {"display_state": "missing", "value": None}
    assert economics["entry_ev"]["expected_funding_usd"] == {
        "display_state": "missing",
        "value": None,
    }
    assert "0" not in str(economics)


def test_renderer_does_not_call_network_order_ledger_or_decision_paths(monkeypatch) -> None:
    fixture = _fixture()

    def forbidden_call(*args: object, **kwargs: object) -> object:
        raise AssertionError("renderer must not call owner workflow functions")

    import apps.live_runner.guarded as guarded
    import core.accounting.ledger as ledger
    import core.accounting.reconciliation as reconciliation
    import core.execution.orders as orders
    import core.execution.planning as planning
    import core.monitoring.funding_settlement as funding_settlement
    import core.pipeline.evaluate as evaluate
    import core.pipeline.snapshot as snapshot
    import core.venues.hyperliquid as hyperliquid
    import core.venues.risex as risex

    monkeypatch.setattr(evaluate, "evaluate_route", forbidden_call)
    monkeypatch.setattr(snapshot, "assemble_route_snapshot", forbidden_call)
    monkeypatch.setattr(snapshot, "assemble_route_snapshot_from_adapters", forbidden_call)
    monkeypatch.setattr(ledger, "append_decision_event", forbidden_call)
    monkeypatch.setattr(reconciliation, "reconcile_ledger", forbidden_call)
    monkeypatch.setattr(funding_settlement, "verify_funding_settlement", forbidden_call)
    monkeypatch.setattr(planning, "plan_execution_without_orders", forbidden_call)
    monkeypatch.setattr(guarded, "run_guarded_live_without_orders", forbidden_call)
    monkeypatch.setattr(orders, "run_approval_gated_order_boundary", forbidden_call)
    monkeypatch.setattr(orders, "send_order", forbidden_call)
    monkeypatch.setattr(risex.RiseXObservationAdapter, "fetch_observation", forbidden_call)
    monkeypatch.setattr(
        hyperliquid.HyperliquidObservationAdapter,
        "fetch_observation",
        forbidden_call,
    )

    view = _render(fixture)

    assert view["display_state"] == "available"
