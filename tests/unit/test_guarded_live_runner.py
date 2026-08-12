from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from apps.live_runner.guarded import (
    GuardedLiveRunnerResult,
    run_guarded_live_without_orders,
)
from apps.paper_runner.lifecycle import run_paper_lifecycle
from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import (
    InMemoryLedger,
    Ledger,
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
)
from core.accounting.reconciliation import (
    LedgerReconciliationResult,
    is_ledger_explicitly_reconciled,
    reconcile_ledger,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    EstimatedValue,
    ExecutableQuote,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
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
            observed_at=(
                snapshot.risex_funding_settlement_at
                - requirement.offset_before_settlement
            ),
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


def _runner_fixture() -> dict[str, object]:
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
    live_gate_evidence_bundle = LiveGateEvidenceBundle(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        funding_settlement_verified=funding_verification.verified,
        ledger_explicitly_reconciled=is_ledger_explicitly_reconciled(ledger.records()),
        capture_plan_evidence=(plan_evidence,),
        execution_capability_evidence=(execution_evidence,),
    )
    non_sending_plan, plan_reason = plan_execution_without_orders(
        capture=capture,
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        decision=decision,
        funding_verification=funding_verification,
        ledger_reconciliation=ledger_reconciliation,
        capture_plan_evidence=(plan_evidence,),
        execution_capability_evidence=(execution_evidence,),
        planned_at=snapshot.captured_at,
    )
    assert plan_reason is None
    assert non_sending_plan is not None
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
        "live_gate_evidence_bundle": live_gate_evidence_bundle,
        "non_sending_plan": non_sending_plan,
        "evaluated_at": snapshot.captured_at,
    }


def _call_runner(
    fixture: dict[str, object],
    **overrides: object,
) -> GuardedLiveRunnerResult:
    values = {
        "capture": fixture["capture"],
        "route": fixture["route"],
        "settlement_time": fixture["snapshot"].risex_funding_settlement_at,
        "non_sending_plan": fixture["non_sending_plan"],
        "funding_verification": fixture["funding_verification"],
        "ledger_reconciliation": fixture["ledger_reconciliation"],
        "live_gate_evidence_bundle": fixture["live_gate_evidence_bundle"],
        "evaluated_at": fixture["evaluated_at"],
        "rules": ProductRules(live_trading_enabled=True),
    }
    values.update(overrides)
    return run_guarded_live_without_orders(**values)


@pytest.mark.parametrize(
    "rules",
    (
        None,
        ProductRules(),
        ProductRules(live_trading_enabled=False),
        ProductRules(live_trading_enabled=1),
    ),
)
def test_live_disabled_fails_closed_before_no_order_readiness(
    rules: ProductRules | None,
) -> None:
    fixture = _runner_fixture()

    result = _call_runner(fixture, rules=rules)

    assert result.no_order_ready is False
    assert result.blocked_reason is RejectReason.LIVE_TRADING_DISABLED


def test_exact_prerequisites_reach_no_order_guarded_readiness() -> None:
    fixture = _runner_fixture()

    result = _call_runner(fixture)

    assert result == GuardedLiveRunnerResult(
        no_order_ready=True,
        blocked_reason=None,
        capture_id=fixture["route"].capture_id,
        route_id=fixture["route"].route_id,
        settlement_time=fixture["snapshot"].risex_funding_settlement_at,
        evaluated_at=fixture["snapshot"].captured_at,
    )


@pytest.mark.parametrize(
    ("field_name", "override", "expected_reason"),
    (
        ("funding_verification", None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("ledger_reconciliation", None, RejectReason.LEDGER_NOT_RECONCILED),
        ("live_gate_evidence_bundle", None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("non_sending_plan", None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        (
            "funding_verification",
            "wrong-type-funding",
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "funding_verification",
            "empty-funding-checkpoints",
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "ledger_reconciliation",
            "wrong-type-ledger",
            RejectReason.LEDGER_NOT_RECONCILED,
        ),
        (
            "live_gate_evidence_bundle",
            object(),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "non_sending_plan",
            "sendable-spoof",
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "non_sending_plan",
            "sendable-subclass",
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
    ),
)
def test_missing_or_malformed_prerequisite_evidence_fails_closed(
    field_name: str,
    override: object,
    expected_reason: RejectReason,
) -> None:
    fixture = _runner_fixture()
    if override == "wrong-type-funding":
        funding = fixture["funding_verification"]
        override = SimpleNamespace(
            capture_id=funding.capture_id,
            route_id=funding.route_id,
            settlement_time=funding.settlement_time,
            verified=True,
            checkpoint_event_sequences=funding.checkpoint_event_sequences,
            settlement_event_sequence=funding.settlement_event_sequence,
        )
    elif override == "empty-funding-checkpoints":
        override = replace(
            fixture["funding_verification"],
            checkpoint_event_sequences=(),
        )
    elif override == "wrong-type-ledger":
        ledger = fixture["ledger_reconciliation"]
        override = SimpleNamespace(
            capture_id=ledger.capture_id,
            route_id=ledger.route_id,
            settlement_time=ledger.settlement_time,
            reconciled=True,
            route_decision_event_sequence=ledger.route_decision_event_sequence,
            funding_verification_event_sequence=(
                ledger.funding_verification_event_sequence
            ),
            checked_event_sequences=ledger.checked_event_sequences,
        )
    elif override == "sendable-spoof":
        override = SimpleNamespace(
            capture_id=fixture["route"].capture_id,
            route_id=fixture["route"].route_id,
            settlement_time=fixture["snapshot"].risex_funding_settlement_at,
            payload={"orders": ()},
            endpoint="/v1/orders",
            client_order_id="order-001",
        )
    elif override == "sendable-subclass":
        class SendablePlan(NonSendingExecutionPlan):
            pass

        override = object.__new__(SendablePlan)
        for field in fields(NonSendingExecutionPlan):
            object.__setattr__(
                override,
                field.name,
                getattr(fixture["non_sending_plan"], field.name),
            )
        object.__setattr__(override, "payload", {"orders": ()})

    result = _call_runner(fixture, **{field_name: override})

    assert result.no_order_ready is False
    assert result.blocked_reason is expected_reason


@pytest.mark.parametrize(
    ("overrides", "expected_identity"),
    (
        (
            {
                "settlement_time": datetime(2026, 1, 1, 16, 0),
            },
            "missing-settlement",
        ),
        (
            {
                "evaluated_at": datetime(2026, 1, 1, 12, 0),
            },
            "missing-evaluated-at",
        ),
    ),
)
def test_naive_runner_timestamps_fail_closed(
    overrides: dict[str, object],
    expected_identity: str,
) -> None:
    fixture = _runner_fixture()

    result = _call_runner(fixture, **overrides)

    assert result.no_order_ready is False
    assert result.blocked_reason is RejectReason.REQUIRED_LIVE_DATA_MISSING
    if expected_identity == "missing-settlement":
        assert result.settlement_time is None
    else:
        assert result.evaluated_at is None


def test_no_order_ready_result_requires_exact_identity_when_constructed_directly() -> None:
    with pytest.raises(ValueError, match="exact identity"):
        GuardedLiveRunnerResult(
            no_order_ready=True,
            blocked_reason=None,
            capture_id=None,
            route_id="route",
            settlement_time=None,
            evaluated_at=None,
        )


@pytest.mark.parametrize(
    ("field_name", "override_factory", "expected_reason"),
    (
        (
            "capture",
            lambda fixture: replace(fixture["capture"], capture_id="other-capture"),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "route",
            lambda fixture: replace(fixture["route"], route_id="other-route"),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "settlement_time",
            lambda fixture: (
                fixture["snapshot"].risex_funding_settlement_at + timedelta(hours=8)
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "funding_verification",
            lambda fixture: replace(
                fixture["funding_verification"],
                route_id="other-route",
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "ledger_reconciliation",
            lambda fixture: replace(
                fixture["ledger_reconciliation"],
                capture_id="other-capture",
            ),
            RejectReason.LEDGER_NOT_RECONCILED,
        ),
        (
            "live_gate_evidence_bundle",
            lambda fixture: replace(
                fixture["live_gate_evidence_bundle"],
                settlement_time=(
                    fixture["snapshot"].risex_funding_settlement_at
                    + timedelta(hours=8)
                ),
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            "non_sending_plan",
            lambda fixture: replace(
                fixture["non_sending_plan"],
                capture_id="other-capture",
            ),
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
    ),
)
def test_cross_identity_prerequisite_evidence_fails_closed(
    field_name: str,
    override_factory,
    expected_reason: RejectReason,
) -> None:
    fixture = _runner_fixture()

    result = _call_runner(fixture, **{field_name: override_factory(fixture)})

    assert result.no_order_ready is False
    assert result.blocked_reason is expected_reason


@pytest.mark.parametrize(
    ("override_factory", "expected_reason"),
    (
        (
            lambda fixture: {
                "live_gate_evidence_bundle": replace(
                    fixture["live_gate_evidence_bundle"],
                    capture_plan_evidence=(
                        _plan_evidence(
                            route=fixture["route"],
                            snapshot=fixture["snapshot"],
                            ledger_reconciliation_event_sequence=(
                                fixture[
                                    "plan_evidence"
                                ].ledger_reconciliation_event_sequence
                            ),
                            planned_at=fixture["snapshot"].captured_at
                            - timedelta(seconds=2),
                            valid_until=fixture["snapshot"].captured_at
                            - timedelta(seconds=1),
                        ),
                    ),
                )
            },
            RejectReason.CAPTURE_PLAN_NOT_FRESH,
        ),
        (
            lambda fixture: {
                "live_gate_evidence_bundle": replace(
                    fixture["live_gate_evidence_bundle"],
                    execution_capability_evidence=(
                        _execution_evidence(
                            route=fixture["route"],
                            snapshot=fixture["snapshot"],
                            checked_at=fixture["snapshot"].captured_at
                            - timedelta(seconds=2),
                            valid_until=fixture["snapshot"].captured_at
                            - timedelta(seconds=1),
                        ),
                    ),
                )
            },
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            lambda fixture: {
                "non_sending_plan": replace(
                    fixture["non_sending_plan"],
                    planned_at=fixture["snapshot"].captured_at
                    - timedelta(minutes=2),
                    valid_until=fixture["snapshot"].captured_at
                    - timedelta(minutes=1),
                )
            },
            RejectReason.CAPTURE_PLAN_NOT_FRESH,
        ),
    ),
)
def test_stale_prerequisite_evidence_fails_closed(
    override_factory,
    expected_reason: RejectReason,
) -> None:
    fixture = _runner_fixture()

    result = _call_runner(fixture, **override_factory(fixture))

    assert result.no_order_ready is False
    assert result.blocked_reason is expected_reason


def test_non_executable_execution_capability_bundle_fails_closed() -> None:
    fixture = _runner_fixture()
    snapshot = fixture["snapshot"]
    bad_quote = replace(
        snapshot.risex_entry_quote,
        vwap_price=None,
        executable=False,
        consumed_base_quantity=Decimal("0"),
        notional_filled_usd=Decimal("0"),
    )
    execution_evidence = _execution_evidence(
        route=fixture["route"],
        snapshot=snapshot,
        risex_entry_quote=bad_quote,
    )
    live_gate_evidence_bundle = replace(
        fixture["live_gate_evidence_bundle"],
        execution_capability_evidence=(execution_evidence,),
    )

    result = _call_runner(
        fixture,
        live_gate_evidence_bundle=live_gate_evidence_bundle,
    )

    assert result.no_order_ready is False
    assert result.blocked_reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


@pytest.mark.parametrize(
    ("plan_change", "expected_reason"),
    (
        ({"risex_venue": "OtherRiseX"}, RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ({"target_notional_usd": Decimal("501")}, RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ({"capture_plan_id": "other-plan"}, RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ({"capture_plan_version": "other-version"}, RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ({"route_decision_event_sequence": 99}, RejectReason.LEDGER_NOT_RECONCILED),
        ({"funding_verification_event_sequence": 99}, RejectReason.LEDGER_NOT_RECONCILED),
        ({"ledger_reconciliation_event_sequence": 99}, RejectReason.CAPTURE_PLAN_NOT_FRESH),
        (
            {"execution_capability_checked_at": "shifted"},
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
    ),
)
def test_non_sending_plan_mismatches_fail_closed(
    plan_change: dict[str, object],
    expected_reason: RejectReason,
) -> None:
    fixture = _runner_fixture()
    if plan_change.get("execution_capability_checked_at") == "shifted":
        plan_change = {
            "execution_capability_checked_at": (
                fixture["snapshot"].captured_at + timedelta(seconds=1)
            )
        }
    non_sending_plan = replace(fixture["non_sending_plan"], **plan_change)

    result = _call_runner(fixture, non_sending_plan=non_sending_plan)

    assert result.no_order_ready is False
    assert result.blocked_reason is expected_reason


def test_runner_result_contract_has_no_sendable_request_fields() -> None:
    field_names = {field.name for field in fields(GuardedLiveRunnerResult)}

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


def test_guarded_live_runner_source_stays_downstream_and_no_order() -> None:
    source = Path("apps/live_runner/guarded.py").read_text()

    assert "send_order" not in source
    assert "core.execution.orders" not in source
    assert "evaluate_route" not in source
    assert "assemble_route_snapshot" not in source
    assert "calculate_entry_ev" not in source
    assert "core.venues" not in source
    assert "append_" not in source
    assert "reconcile_ledger" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "aiohttp" not in source
    assert "api_key" not in source.lower()
    assert "secret" not in source.lower()
    assert "private_key" not in source.lower()
