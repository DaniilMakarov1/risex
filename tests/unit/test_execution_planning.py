from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from apps.paper_runner.lifecycle import run_paper_lifecycle
from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import (
    InMemoryLedger,
    Ledger,
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
)
from core.accounting.reconciliation import LedgerReconciliationResult, reconcile_ledger
from core.domain.contracts import (
    Capture,
    CapturePlan,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    EstimatedValue,
    ExecutableQuote,
    ExecutionCapabilityEvidence,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.execution.planning import (
    NonSendingExecutionPlan,
    plan_execution_without_orders,
)
from core.monitoring.funding_settlement import (
    FundingSettlementVerificationResult,
    REQUIRED_FUNDING_CHECKPOINTS,
    verify_funding_settlement,
)


def _observed(value: Decimal | str) -> EstimatedValue:
    return EstimatedValue(value=Decimal(str(value)), source=ValueSource.OBSERVED)


def _append_required_checkpoints(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> None:
    for requirement in REQUIRED_FUNDING_CHECKPOINTS:
        append_funding_checkpoint_observed_event(
            ledger,
            capture_id=route.capture_id,
            route_id=route.route_id,
            checkpoint=requirement.checkpoint.value,
            settlement_time=snapshot.risex_funding_settlement_at,
            observed_at=snapshot.risex_funding_settlement_at
            - requirement.offset_before_settlement,
            target_notional_usd=route.target_notional_usd,
            risex_expected_funding_usd=snapshot.funding.risex_funding_usd,
            hedge_expected_funding_usd=snapshot.funding.hedge_funding_usd,
        )


def _append_settlement_evidence(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> None:
    append_funding_settlement_evidence_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at,
        approval_granted=True,
        actual_risex_funding_usd=snapshot.funding.risex_funding_usd,
        actual_hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        actual_risex_notional_usd=_observed(route.target_notional_usd),
        actual_hedge_notional_usd=_observed(route.target_notional_usd),
    )


def _base_decision(route: RouteCandidate, snapshot: VenueSnapshot) -> DecisionResult:
    return DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=(),
        net_profit_usd=Decimal("2"),
        decided_at=snapshot.captured_at,
    )


def _execution_evidence(
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    **changes: object,
) -> ExecutionCapabilityEvidence:
    values = {
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "checked_at": snapshot.captured_at,
        "valid_until": snapshot.captured_at + timedelta(minutes=1),
        "source": ValueSource.ESTIMATED_FROM_ORDERBOOK,
        "risex_entry_quote": snapshot.risex_entry_quote,
        "hedge_entry_quote": snapshot.hedge_entry_quote,
        "risex_estimated_exit_quote": snapshot.risex_estimated_exit_quote,
        "hedge_estimated_exit_quote": snapshot.hedge_estimated_exit_quote,
    }
    values.update(changes)
    return ExecutionCapabilityEvidence(**values)


def _plan_evidence(
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    ledger_reconciliation_event_sequence: int | None,
    **changes: object,
) -> CapturePlanFreshnessEvidence:
    values = {
        "plan_id": "fake-plan-001",
        "plan_version": "fake-v1",
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "planned_at": snapshot.captured_at,
        "valid_until": snapshot.captured_at + timedelta(minutes=5),
        "source": ValueSource.OBSERVED,
        "ledger_reconciliation_event_sequence": ledger_reconciliation_event_sequence,
    }
    values.update(changes)
    return CapturePlanFreshnessEvidence(**values)


def _planning_fixture() -> dict[str, object]:
    ledger = InMemoryLedger()
    route, snapshot = build_fake_route_and_snapshot()
    capture = Capture(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    decision = _base_decision(route, snapshot)
    run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)
    funding_verification = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    ledger_reconciliation = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    plan_evidence = _plan_evidence(
        route=route,
        snapshot=snapshot,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )
    execution_evidence = _execution_evidence(route=route, snapshot=snapshot)
    return {
        "ledger": ledger,
        "route": route,
        "snapshot": snapshot,
        "capture": capture,
        "decision": decision,
        "funding_verification": funding_verification,
        "ledger_reconciliation": ledger_reconciliation,
        "plan_evidence": plan_evidence,
        "execution_evidence": execution_evidence,
        "planned_at": snapshot.captured_at,
    }


def _call_planning(
    fixture: dict[str, object],
    **overrides: object,
) -> tuple[NonSendingExecutionPlan | None, RejectReason | None]:
    values = {
        "capture": fixture["capture"],
        "route": fixture["route"],
        "settlement_time": fixture["snapshot"].risex_funding_settlement_at,
        "decision": fixture["decision"],
        "funding_verification": fixture["funding_verification"],
        "ledger_reconciliation": fixture["ledger_reconciliation"],
        "capture_plan_evidence": (fixture["plan_evidence"],),
        "execution_capability_evidence": (fixture["execution_evidence"],),
        "planned_at": fixture["planned_at"],
    }
    values.update(overrides)
    return plan_execution_without_orders(**values)


def test_exact_prerequisites_return_non_sending_execution_plan() -> None:
    fixture = _planning_fixture()
    route = fixture["route"]
    snapshot = fixture["snapshot"]
    ledger = fixture["ledger"]
    ledger_reconciliation = fixture["ledger_reconciliation"]

    plan, reason = _call_planning(fixture)

    assert reason is None
    assert plan == NonSendingExecutionPlan(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at,
        valid_until=fixture["execution_evidence"].valid_until,
        risex_venue=route.risex_venue,
        risex_symbol=route.risex_symbol,
        risex_entry_side=route.risex_entry_side,
        risex_unwind_side="sell",
        hedge_venue=route.hedge_venue,
        hedge_symbol=route.hedge_symbol,
        hedge_entry_side=route.hedge_entry_side,
        hedge_unwind_side="buy",
        target_notional_usd=route.target_notional_usd,
        capture_plan_id=fixture["plan_evidence"].plan_id,
        capture_plan_version=fixture["plan_evidence"].plan_version,
        route_decision_event_sequence=(
            ledger_reconciliation.route_decision_event_sequence
        ),
        funding_verification_event_sequence=(
            ledger_reconciliation.funding_verification_event_sequence
        ),
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
        execution_capability_checked_at=fixture["execution_evidence"].checked_at,
    )
    assert fixture["decision"].capture_plan is None


@pytest.mark.parametrize(
    ("decision_override", "expected_reason"),
    (
        (None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        (
            DecisionResult(
                route_id="fake-risex-hl-btc",
                mode=EvaluationMode.DISCOVERY,
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(),
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            DecisionResult(
                route_id="fake-risex-hl-btc",
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.MIN_NET_PROFIT_NOT_MET,),
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            DecisionResult(
                route_id="other-route",
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(),
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
    ),
)
def test_route_decision_prerequisites_fail_closed(
    decision_override: DecisionResult | None,
    expected_reason: RejectReason,
) -> None:
    fixture = _planning_fixture()

    plan, reason = _call_planning(fixture, decision=decision_override)

    assert plan is None
    assert reason is expected_reason


def test_live_capture_plan_decision_fails_closed() -> None:
    fixture = _planning_fixture()
    route = fixture["route"]
    snapshot = fixture["snapshot"]
    decision = replace(
        fixture["decision"],
        capture_plan=CapturePlan(
            plan_id="live-plan",
            capture=fixture["capture"],
            created_at=snapshot.captured_at,
        ),
    )

    plan, reason = _call_planning(fixture, decision=decision)

    assert route.route_id == decision.route_id
    assert plan is None
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


@pytest.mark.parametrize(
    "funding_override",
    (
        None,
        lambda result: replace(result, verified=False),
        lambda result: replace(result, capture_id="other-capture"),
        lambda result: replace(result, route_id="other-route"),
        lambda result: replace(
            result,
            settlement_time=result.settlement_time + timedelta(hours=8),
        ),
        lambda result: SimpleNamespace(
            capture_id=result.capture_id,
            route_id=result.route_id,
            settlement_time=result.settlement_time,
            verified=True,
            reasons=result.reasons,
            checkpoint_event_sequences=result.checkpoint_event_sequences,
            settlement_event_sequence=result.settlement_event_sequence,
        ),
    ),
)
def test_funding_verification_prerequisites_fail_closed(funding_override: object) -> None:
    fixture = _planning_fixture()
    funding_verification = fixture["funding_verification"]
    if callable(funding_override):
        funding_verification = funding_override(funding_verification)
    else:
        funding_verification = funding_override

    plan, reason = _call_planning(
        fixture,
        funding_verification=funding_verification,
    )

    assert plan is None
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


@pytest.mark.parametrize(
    "ledger_override",
    (
        None,
        lambda result: replace(result, reconciled=False),
        lambda result: replace(result, capture_id="other-capture"),
        lambda result: replace(result, route_id="other-route"),
        lambda result: replace(
            result,
            settlement_time=result.settlement_time + timedelta(hours=8),
        ),
        lambda result: replace(result, route_decision_event_sequence=None),
        lambda result: replace(result, funding_verification_event_sequence=None),
        lambda result: LedgerReconciliationResult(
            capture_id=result.capture_id,
            route_id=result.route_id,
            settlement_time=result.settlement_time,
            reconciled=True,
            reasons=(),
            route_decision_event_sequence=result.route_decision_event_sequence,
            paper_event_sequences=result.paper_event_sequences,
            funding_verification_event_sequence=result.funding_verification_event_sequence,
            checked_event_sequences=(),
        ),
        lambda result: SimpleNamespace(
            capture_id=result.capture_id,
            route_id=result.route_id,
            settlement_time=result.settlement_time,
            reconciled=True,
            reasons=result.reasons,
            route_decision_event_sequence=result.route_decision_event_sequence,
            paper_event_sequences=result.paper_event_sequences,
            funding_verification_event_sequence=result.funding_verification_event_sequence,
            checked_event_sequences=result.checked_event_sequences,
        ),
    ),
)
def test_ledger_reconciliation_prerequisites_fail_closed(ledger_override: object) -> None:
    fixture = _planning_fixture()
    ledger_reconciliation = fixture["ledger_reconciliation"]
    if callable(ledger_override):
        ledger_reconciliation = ledger_override(ledger_reconciliation)
    else:
        ledger_reconciliation = ledger_override

    plan, reason = _call_planning(
        fixture,
        ledger_reconciliation=ledger_reconciliation,
    )

    assert plan is None
    assert reason is RejectReason.LEDGER_NOT_RECONCILED


@pytest.mark.parametrize(
    ("plan_evidence_override", "expected_reason"),
    (
        (None, RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ((), RejectReason.CAPTURE_PLAN_NOT_FRESH),
        (object(), RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ((object(),), RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("duplicate", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("stale", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("cross-capture", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("cross-route", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("cross-settlement", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("missing-reconciliation-reference", RejectReason.CAPTURE_PLAN_NOT_FRESH),
    ),
)
def test_capture_plan_prerequisites_fail_closed(
    plan_evidence_override: object,
    expected_reason: RejectReason,
) -> None:
    fixture = _planning_fixture()
    route = fixture["route"]
    snapshot = fixture["snapshot"]
    evidence = fixture["plan_evidence"]
    if plan_evidence_override == "duplicate":
        plan_evidence_override = (evidence, evidence)
    elif plan_evidence_override == "stale":
        plan_evidence_override = (
            _plan_evidence(
                route=route,
                snapshot=snapshot,
                ledger_reconciliation_event_sequence=evidence.ledger_reconciliation_event_sequence,
                planned_at=snapshot.captured_at - timedelta(seconds=2),
                valid_until=snapshot.captured_at - timedelta(seconds=1),
            ),
        )
    elif plan_evidence_override == "cross-capture":
        plan_evidence_override = (
            _plan_evidence(
                route=route,
                snapshot=snapshot,
                ledger_reconciliation_event_sequence=evidence.ledger_reconciliation_event_sequence,
                capture_id="other-capture",
            ),
        )
    elif plan_evidence_override == "cross-route":
        plan_evidence_override = (
            _plan_evidence(
                route=route,
                snapshot=snapshot,
                ledger_reconciliation_event_sequence=evidence.ledger_reconciliation_event_sequence,
                route_id="other-route",
            ),
        )
    elif plan_evidence_override == "cross-settlement":
        plan_evidence_override = (
            _plan_evidence(
                route=route,
                snapshot=snapshot,
                ledger_reconciliation_event_sequence=evidence.ledger_reconciliation_event_sequence,
                settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
            ),
        )
    elif plan_evidence_override == "missing-reconciliation-reference":
        plan_evidence_override = (
            _plan_evidence(
                route=route,
                snapshot=snapshot,
                ledger_reconciliation_event_sequence=None,
            ),
        )

    plan, reason = _call_planning(
        fixture,
        capture_plan_evidence=plan_evidence_override,
    )

    assert plan is None
    assert reason is expected_reason


@pytest.mark.parametrize(
    ("execution_evidence_override", "expected_reason"),
    (
        (None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ((), RejectReason.REQUIRED_LIVE_DATA_MISSING),
        (object(), RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ((object(),), RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("stale", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-capture", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-route", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-settlement", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("wrong-side", RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ("wrong-target", RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ("partial-fill", RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ("non-orderbook", RejectReason.REQUIRED_LIVE_DATA_MISSING),
    ),
)
def test_execution_capability_prerequisites_fail_closed(
    execution_evidence_override: object,
    expected_reason: RejectReason,
) -> None:
    fixture = _planning_fixture()
    route = fixture["route"]
    snapshot = fixture["snapshot"]
    if execution_evidence_override == "stale":
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                checked_at=snapshot.captured_at - timedelta(seconds=2),
                valid_until=snapshot.captured_at - timedelta(seconds=1),
            ),
        )
    elif execution_evidence_override == "cross-capture":
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                capture_id="other-capture",
            ),
        )
    elif execution_evidence_override == "cross-route":
        execution_evidence_override = (
            _execution_evidence(route=route, snapshot=snapshot, route_id="other-route"),
        )
    elif execution_evidence_override == "cross-settlement":
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
            ),
        )
    elif execution_evidence_override == "wrong-side":
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                risex_entry_quote=replace(snapshot.risex_entry_quote, side="sell"),
            ),
        )
    elif execution_evidence_override == "wrong-target":
        wrong_target_quote = ExecutableQuote(
            venue=snapshot.hedge_entry_quote.venue,
            symbol=snapshot.hedge_entry_quote.symbol,
            side=snapshot.hedge_entry_quote.side,
            target_notional_usd=route.target_notional_usd + Decimal("1"),
            vwap_price=Decimal("100"),
            executable=True,
            source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
            consumed_base_quantity=Decimal("5.01"),
            notional_filled_usd=route.target_notional_usd + Decimal("1"),
        )
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                hedge_entry_quote=wrong_target_quote,
            ),
        )
    elif execution_evidence_override == "partial-fill":
        partial_quote = ExecutableQuote(
            venue=snapshot.risex_entry_quote.venue,
            symbol=snapshot.risex_entry_quote.symbol,
            side=snapshot.risex_entry_quote.side,
            target_notional_usd=route.target_notional_usd,
            vwap_price=Decimal("100"),
            executable=False,
            source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
            consumed_base_quantity=Decimal("4.99"),
            notional_filled_usd=Decimal("499"),
        )
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                risex_entry_quote=partial_quote,
            ),
        )
    elif execution_evidence_override == "non-orderbook":
        execution_evidence_override = (
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                source=ValueSource.OBSERVED,
            ),
        )

    plan, reason = _call_planning(
        fixture,
        execution_capability_evidence=execution_evidence_override,
    )

    assert plan is None
    assert reason is expected_reason


def test_naive_planning_timestamps_fail_closed() -> None:
    fixture = _planning_fixture()

    plan, reason = _call_planning(fixture, planned_at=datetime(2026, 1, 1, 12, 0))
    assert plan is None
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING

    plan, reason = _call_planning(
        fixture,
        settlement_time=datetime(2026, 1, 1, 16, 0),
    )
    assert plan is None
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_cross_capture_identity_fails_closed() -> None:
    fixture = _planning_fixture()
    capture = replace(fixture["capture"], capture_id="other-capture")

    plan, reason = _call_planning(fixture, capture=capture)

    assert plan is None
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_non_sending_plan_contract_has_no_sendable_request_fields() -> None:
    field_names = {field.name for field in fields(NonSendingExecutionPlan)}

    assert field_names.isdisjoint(
        {
            "api_key",
            "secret",
            "private_key",
            "account_id",
            "client_order_id",
            "order_id",
            "time_in_force",
            "limit_price",
            "market_order_request",
            "endpoint",
            "payload",
            "headers",
        }
    )


def test_execution_planning_source_stays_non_sending_and_offline() -> None:
    source = Path("core/execution/planning.py").read_text()

    assert "send_order" not in source
    assert "evaluate_route" not in source
    assert "assemble_route_snapshot" not in source
    assert "core.venues" not in source
    assert "apps.live_runner" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "aiohttp" not in source
    assert "api_key" not in source.lower()
    assert "secret" not in source.lower()
    assert "private_key" not in source.lower()
