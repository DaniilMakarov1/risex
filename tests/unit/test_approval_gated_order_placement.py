from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from apps.live_runner.guarded import GuardedLiveRunnerResult
from apps.live_runner.order_placement import run_approval_gated_live_order_placement
from core.config.product_rules import ProductRules
from core.domain.enums import RejectReason
from core.execution.orders import (
    ApprovalGatedOrderPlacementResult,
    OrderPlacementApproval,
)
from core.execution.planning import NonSendingExecutionPlan
from tests.unit.test_guarded_live_runner import (
    _call_runner,
    _execution_evidence,
    _runner_fixture,
)


def _approval(
    fixture: dict[str, object],
    guarded_result: GuardedLiveRunnerResult,
    *,
    requested_at,
    **changes: object,
) -> OrderPlacementApproval:
    non_sending_plan = fixture["non_sending_plan"]
    values = {
        "approval_id": "approval-001",
        "capture_id": fixture["route"].capture_id,
        "route_id": fixture["route"].route_id,
        "settlement_time": fixture["snapshot"].risex_funding_settlement_at,
        "guarded_evaluated_at": guarded_result.evaluated_at,
        "non_sending_plan_planned_at": non_sending_plan.planned_at,
        "non_sending_plan_valid_until": non_sending_plan.valid_until,
        "capture_plan_id": non_sending_plan.capture_plan_id,
        "capture_plan_version": non_sending_plan.capture_plan_version,
        "route_decision_event_sequence": (
            non_sending_plan.route_decision_event_sequence
        ),
        "funding_verification_event_sequence": (
            non_sending_plan.funding_verification_event_sequence
        ),
        "ledger_reconciliation_event_sequence": (
            non_sending_plan.ledger_reconciliation_event_sequence
        ),
        "execution_capability_checked_at": (
            non_sending_plan.execution_capability_checked_at
        ),
        "approval_granted": True,
        "approved_at": guarded_result.evaluated_at + timedelta(seconds=1),
        "valid_until": requested_at + timedelta(seconds=15),
    }
    values.update(changes)
    return OrderPlacementApproval(**values)


def _ready_inputs() -> tuple[
    dict[str, object],
    GuardedLiveRunnerResult,
    OrderPlacementApproval,
    datetime,
]:
    fixture = _runner_fixture()
    guarded_result = _call_runner(fixture)
    assert guarded_result.no_order_ready is True
    assert guarded_result.evaluated_at is not None
    requested_at = guarded_result.evaluated_at + timedelta(seconds=30)
    approval = _approval(fixture, guarded_result, requested_at=requested_at)
    return fixture, guarded_result, approval, requested_at


def _recording_boundary(calls: list[tuple[object, object]]):
    def boundary(
        approval: OrderPlacementApproval,
        non_sending_plan: NonSendingExecutionPlan,
    ) -> bool:
        calls.append((approval, non_sending_plan))
        return True

    return boundary


def _run_boundary(
    fixture: dict[str, object],
    *,
    guarded_result: object,
    approval: object,
    requested_at: datetime,
    deterministic_order_boundary,
    **overrides: object,
) -> ApprovalGatedOrderPlacementResult:
    values = {
        "capture": fixture["capture"],
        "route": fixture["route"],
        "settlement_time": fixture["snapshot"].risex_funding_settlement_at,
        "guarded_live_runner_result": guarded_result,
        "non_sending_plan": fixture["non_sending_plan"],
        "approval": approval,
        "requested_at": requested_at,
        "deterministic_order_boundary": deterministic_order_boundary,
        "rules": ProductRules(live_trading_enabled=True),
    }
    values.update(overrides)
    return run_approval_gated_live_order_placement(**values)


def _forged_approval(
    approval: OrderPlacementApproval,
    *,
    field_name: str,
    value: object,
) -> OrderPlacementApproval:
    forged = object.__new__(OrderPlacementApproval)
    for field in fields(OrderPlacementApproval):
        object.__setattr__(forged, field.name, getattr(approval, field.name))
    object.__setattr__(forged, field_name, value)
    return forged


def test_exact_approval_invokes_injected_boundary_once_without_venue_dependency() -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
    )

    assert result == ApprovalGatedOrderPlacementResult(
        boundary_invoked=True,
        blocked_reason=None,
        capture_id=fixture["route"].capture_id,
        route_id=fixture["route"].route_id,
        settlement_time=fixture["snapshot"].risex_funding_settlement_at,
        requested_at=requested_at,
        approval_id=approval.approval_id,
    )
    assert calls == [(approval, fixture["non_sending_plan"])]


@pytest.mark.parametrize(
    "rules",
    (
        None,
        ProductRules(),
        ProductRules(live_trading_enabled=False),
        ProductRules(live_trading_enabled=1),
    ),
)
def test_live_switch_must_be_exactly_enabled_before_boundary_call(
    rules: ProductRules | None,
) -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
        rules=rules,
    )

    assert result.boundary_invoked is False
    assert result.blocked_reason is RejectReason.LIVE_TRADING_DISABLED
    assert calls == []


@pytest.mark.parametrize(
    ("guarded_override", "expected_reason"),
    (
        (None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("wrong-type", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("not-ready", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-capture", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-route", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("cross-settlement", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("stale-readiness", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("future-readiness", RejectReason.REQUIRED_LIVE_DATA_MISSING),
    ),
)
def test_missing_malformed_or_cross_identity_guarded_result_fails_closed(
    guarded_override: object,
    expected_reason: RejectReason,
) -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()
    if guarded_override == "wrong-type":
        guarded_override = object()
    elif guarded_override == "not-ready":
        guarded_override = GuardedLiveRunnerResult(
            no_order_ready=False,
            blocked_reason=RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture_id=fixture["route"].capture_id,
            route_id=fixture["route"].route_id,
            settlement_time=fixture["snapshot"].risex_funding_settlement_at,
            evaluated_at=fixture["evaluated_at"],
        )
    elif guarded_override == "cross-capture":
        guarded_override = replace(guarded_result, capture_id="other-capture")
    elif guarded_override == "cross-route":
        guarded_override = replace(guarded_result, route_id="other-route")
    elif guarded_override == "cross-settlement":
        guarded_override = replace(
            guarded_result,
            settlement_time=fixture["snapshot"].risex_funding_settlement_at
            + timedelta(hours=8),
        )
    elif guarded_override == "stale-readiness":
        guarded_override = replace(
            guarded_result,
            evaluated_at=fixture["non_sending_plan"].planned_at - timedelta(seconds=1),
        )
        approval = _approval(
            fixture,
            guarded_override,
            requested_at=requested_at,
        )
    elif guarded_override == "future-readiness":
        guarded_override = replace(
            guarded_result,
            evaluated_at=requested_at + timedelta(seconds=1),
        )
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_override,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
    )

    assert result.boundary_invoked is False
    assert result.blocked_reason is expected_reason
    assert calls == []


@pytest.mark.parametrize(
    ("runner_overrides_factory", "expected_reason"),
    (
        (
            lambda fixture: {
                "funding_verification": replace(
                    fixture["funding_verification"],
                    verified=False,
                ),
            },
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
        ),
        (
            lambda fixture: {
                "ledger_reconciliation": replace(
                    fixture["ledger_reconciliation"],
                    reconciled=False,
                ),
            },
            RejectReason.LEDGER_NOT_RECONCILED,
        ),
        (
            lambda fixture: {
                "live_gate_evidence_bundle": replace(
                    fixture["live_gate_evidence_bundle"],
                    execution_capability_evidence=(
                        _execution_evidence(
                            route=fixture["route"],
                            snapshot=fixture["snapshot"],
                            risex_entry_quote=replace(
                                fixture["snapshot"].risex_entry_quote,
                                executable=False,
                                vwap_price=None,
                                consumed_base_quantity=Decimal("0"),
                                notional_filled_usd=Decimal("0"),
                            ),
                        ),
                    ),
                ),
            },
            RejectReason.TECHNICALLY_NOT_EXECUTABLE,
        ),
    ),
)
def test_failed_existing_live_prerequisites_stop_before_order_boundary(
    runner_overrides_factory,
    expected_reason: RejectReason,
) -> None:
    fixture, ready_guarded_result, approval, requested_at = _ready_inputs()
    guarded_result = _call_runner(fixture, **runner_overrides_factory(fixture))
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
    )

    assert ready_guarded_result.no_order_ready is True
    assert guarded_result.no_order_ready is False
    assert guarded_result.blocked_reason is expected_reason
    assert result.boundary_invoked is False
    assert result.blocked_reason is expected_reason
    assert calls == []


@pytest.mark.parametrize(
    ("approval_override", "expected_reason"),
    (
        (None, RejectReason.USER_RULE_VIOLATED),
        ("wrong-type", RejectReason.USER_RULE_VIOLATED),
        ("false", RejectReason.USER_RULE_VIOLATED),
        ("truthy-non-bool", RejectReason.USER_RULE_VIOLATED),
        ("stale", RejectReason.USER_RULE_VIOLATED),
        ("before-guarded", RejectReason.USER_RULE_VIOLATED),
        ("future-approval", RejectReason.USER_RULE_VIOLATED),
        ("cross-capture", RejectReason.USER_RULE_VIOLATED),
        ("cross-route", RejectReason.USER_RULE_VIOLATED),
        ("cross-settlement", RejectReason.USER_RULE_VIOLATED),
        ("guarded-time-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("plan-id-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("plan-version-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("route-sequence-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("funding-sequence-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("ledger-sequence-mismatch", RejectReason.USER_RULE_VIOLATED),
        ("execution-time-mismatch", RejectReason.USER_RULE_VIOLATED),
    ),
)
def test_missing_false_stale_or_cross_identity_approval_fails_closed(
    approval_override: object,
    expected_reason: RejectReason,
) -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()
    if approval_override == "wrong-type":
        approval_override = object()
    elif approval_override == "false":
        approval_override = replace(approval, approval_granted=False)
    elif approval_override == "truthy-non-bool":
        approval_override = _forged_approval(
            approval,
            field_name="approval_granted",
            value=1,
        )
    elif approval_override == "stale":
        approval_override = replace(approval, valid_until=requested_at)
    elif approval_override == "before-guarded":
        approval_override = replace(
            approval,
            approved_at=guarded_result.evaluated_at - timedelta(seconds=1),
        )
    elif approval_override == "future-approval":
        approval_override = replace(
            approval,
            approved_at=requested_at + timedelta(seconds=1),
            valid_until=requested_at + timedelta(seconds=20),
        )
    elif approval_override == "cross-capture":
        approval_override = replace(approval, capture_id="other-capture")
    elif approval_override == "cross-route":
        approval_override = replace(approval, route_id="other-route")
    elif approval_override == "cross-settlement":
        approval_override = replace(
            approval,
            settlement_time=fixture["snapshot"].risex_funding_settlement_at
            + timedelta(hours=8),
        )
    elif approval_override == "guarded-time-mismatch":
        approval_override = replace(
            approval,
            guarded_evaluated_at=guarded_result.evaluated_at + timedelta(seconds=1),
        )
    elif approval_override == "plan-id-mismatch":
        approval_override = replace(approval, capture_plan_id="other-plan")
    elif approval_override == "plan-version-mismatch":
        approval_override = replace(approval, capture_plan_version="other-version")
    elif approval_override == "route-sequence-mismatch":
        approval_override = replace(
            approval,
            route_decision_event_sequence=approval.route_decision_event_sequence + 1,
        )
    elif approval_override == "funding-sequence-mismatch":
        approval_override = replace(
            approval,
            funding_verification_event_sequence=(
                approval.funding_verification_event_sequence + 1
            ),
        )
    elif approval_override == "ledger-sequence-mismatch":
        approval_override = replace(
            approval,
            ledger_reconciliation_event_sequence=(
                approval.ledger_reconciliation_event_sequence + 1
            ),
        )
    elif approval_override == "execution-time-mismatch":
        approval_override = replace(
            approval,
            execution_capability_checked_at=(
                approval.execution_capability_checked_at + timedelta(seconds=1)
            ),
        )
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval_override,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
    )

    assert result.boundary_invoked is False
    assert result.blocked_reason is expected_reason
    assert calls == []


@pytest.mark.parametrize(
    ("plan_override", "expected_reason"),
    (
        (None, RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("wrong-type", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("sendable-subclass", RejectReason.REQUIRED_LIVE_DATA_MISSING),
        ("stale", RejectReason.CAPTURE_PLAN_NOT_FRESH),
        ("route-action-mismatch", RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ("notional-mismatch", RejectReason.TECHNICALLY_NOT_EXECUTABLE),
        ("sequence-missing", RejectReason.REQUIRED_LIVE_DATA_MISSING),
    ),
)
def test_missing_stale_or_mismatched_non_sending_plan_fails_closed(
    plan_override: object,
    expected_reason: RejectReason,
) -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()
    if plan_override == "wrong-type":
        plan_override = object()
    elif plan_override == "sendable-subclass":
        class SendablePlan(NonSendingExecutionPlan):
            pass

        plan_override = object.__new__(SendablePlan)
        for field in fields(NonSendingExecutionPlan):
            object.__setattr__(
                plan_override,
                field.name,
                getattr(fixture["non_sending_plan"], field.name),
            )
        object.__setattr__(plan_override, "payload", {"legs": ()})
    elif plan_override == "stale":
        plan_override = replace(
            fixture["non_sending_plan"],
            planned_at=fixture["evaluated_at"] - timedelta(seconds=30),
            valid_until=requested_at,
        )
    elif plan_override == "route-action-mismatch":
        plan_override = replace(
            fixture["non_sending_plan"],
            risex_entry_side="sell",
            risex_unwind_side="buy",
        )
    elif plan_override == "notional-mismatch":
        plan_override = replace(
            fixture["non_sending_plan"],
            target_notional_usd=Decimal("501"),
        )
    elif plan_override == "sequence-missing":
        plan_override = object.__new__(NonSendingExecutionPlan)
        for field in fields(NonSendingExecutionPlan):
            object.__setattr__(
                plan_override,
                field.name,
                getattr(fixture["non_sending_plan"], field.name),
            )
        object.__setattr__(plan_override, "route_decision_event_sequence", 0)
    calls: list[tuple[object, object]] = []

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=_recording_boundary(calls),
        non_sending_plan=plan_override,
    )

    assert result.boundary_invoked is False
    assert result.blocked_reason is expected_reason
    assert calls == []


@pytest.mark.parametrize(
    "deterministic_order_boundary",
    (None, object(), lambda approval, plan: False),
)
def test_missing_or_refusing_injected_boundary_fails_closed(
    deterministic_order_boundary,
) -> None:
    fixture, guarded_result, approval, requested_at = _ready_inputs()

    result = _run_boundary(
        fixture,
        guarded_result=guarded_result,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=deterministic_order_boundary,
    )

    assert result.boundary_invoked is False
    assert result.blocked_reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_order_boundary_contracts_have_no_sendable_request_fields() -> None:
    field_names = {
        field.name
        for contract in (OrderPlacementApproval, ApprovalGatedOrderPlacementResult)
        for field in fields(contract)
    }

    assert field_names.isdisjoint(
        {
            "account_id",
            "client_order_id",
            "endpoint",
            "headers",
            "limit_price",
            "market_order_request",
            "order_id",
            "payload",
            "private_key",
            "secret",
            "time_in_force",
        }
    )


def test_order_boundary_source_stays_downstream_and_non_networked() -> None:
    source = "\n".join(
        Path(path).read_text()
        for path in (
            "core/execution/orders.py",
            "apps/live_runner/order_placement.py",
        )
    )
    app_wrapper_source = Path("apps/live_runner/order_placement.py").read_text()

    for forbidden in (
        "evaluate_route",
        "assemble_route_snapshot",
        "calculate_entry_ev",
        "calculate_total_fees_usd",
        "calculate_total_expected_funding_usd",
        "calculate_current_unwind_pnl_usd",
        "core.venues",
        "append_",
        "reconcile_ledger",
        "verify_funding_settlement",
        "requests",
        "httpx",
        "aiohttp",
        "api_key",
        "account_id",
        "client_order_id",
        "endpoint",
        "headers",
        "limit_price",
        "market_order_request",
        "order_id",
        "payload",
        "private_key",
        "secret_key",
        "time_in_force",
    ):
        assert forbidden not in source
    assert "send_order(" not in app_wrapper_source
