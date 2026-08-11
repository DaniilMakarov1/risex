from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
    ExecutableQuote,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
)
from core.domain.enums import RejectReason, ValueSource
from core.risk.gates import (
    check_capture_plan_freshness_gate,
    check_execution_capability_gate,
    check_live_gate_evidence_bundle,
)


def _fresh_evidence(**changes) -> CapturePlanFreshnessEvidence:
    route, snapshot = build_fake_route_and_snapshot()
    values = {
        "plan_id": "fake-plan-001",
        "plan_version": "fake-v1",
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "planned_at": snapshot.captured_at,
        "valid_until": snapshot.captured_at + timedelta(minutes=5),
        "source": ValueSource.OBSERVED,
        "ledger_reconciliation_event_sequence": 11,
    }
    values.update(changes)
    return CapturePlanFreshnessEvidence(**values)


def _execution_evidence(**changes) -> ExecutionCapabilityEvidence:
    route, snapshot = build_fake_route_and_snapshot()
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


def _live_gate_evidence_bundle(**changes) -> LiveGateEvidenceBundle:
    route, snapshot = build_fake_route_and_snapshot()
    values = {
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "funding_settlement_verified": True,
        "ledger_explicitly_reconciled": True,
        "capture_plan_evidence": (_fresh_evidence(),),
        "execution_capability_evidence": (_execution_evidence(),),
    }
    values.update(changes)
    return LiveGateEvidenceBundle(**values)


def _forge_execution_evidence(
    evidence: ExecutionCapabilityEvidence,
    **changes,
) -> ExecutionCapabilityEvidence:
    values = {field.name: getattr(evidence, field.name) for field in fields(ExecutionCapabilityEvidence)}
    values.update(changes)
    forged = object.__new__(ExecutionCapabilityEvidence)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def test_missing_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=None,
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_stale_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(
        valid_until=snapshot.captured_at + timedelta(seconds=1),
    )

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at + timedelta(seconds=1),
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_duplicated_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence, evidence),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


@pytest.mark.parametrize(
    "changes",
    (
        {"capture_id": "other-capture"},
        {"route_id": "other-route"},
    ),
)
def test_cross_capture_or_route_plan_freshness_evidence_fails_closed(
    changes: dict[str, str],
) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(**changes)

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_cross_settlement_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(
        settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
    )

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_fresh_capture_plan_evidence_for_exact_capture_route_and_settlement_passes() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is True
    assert reason is None


def test_naive_capture_plan_freshness_timestamp_is_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="planned_at must be timezone-aware"):
        _fresh_evidence(planned_at=datetime(2026, 1, 1, 12, 0))


def test_missing_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=None,
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_stale_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(valid_until=snapshot.captured_at + timedelta(seconds=1))

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at + timedelta(seconds=1),
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


@pytest.mark.parametrize(
    "changes",
    (
        {"capture_id": "other-capture"},
        {"route_id": "other-route"},
    ),
)
def test_cross_capture_or_route_execution_capability_evidence_fails_closed(
    changes: dict[str, str],
) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(**changes)

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_cross_settlement_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(
        settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_future_dated_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(checked_at=snapshot.captured_at + timedelta(seconds=1))

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_duplicated_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence()

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence, evidence),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_partial_fill_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
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
    evidence = _execution_evidence(risex_entry_quote=partial_quote)

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_contradictory_execution_capability_quote_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(
        risex_entry_quote=replace(snapshot.risex_entry_quote, venue="OtherVenue"),
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_wrong_risex_entry_side_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(
        risex_entry_quote=replace(snapshot.risex_entry_quote, side="sell"),
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_wrong_risex_unwind_side_execution_capability_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(
        risex_estimated_exit_quote=replace(
            snapshot.risex_estimated_exit_quote,
            side="buy",
        ),
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_execution_capability_evidence_missing_required_side_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _forge_execution_evidence(
        _execution_evidence(),
        hedge_estimated_exit_quote=None,
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_execution_capability_wrong_target_notional_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
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
    evidence = _execution_evidence(hedge_entry_quote=wrong_target_quote)

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.TECHNICALLY_NOT_EXECUTABLE


def test_execution_capability_non_orderbook_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(source=ValueSource.OBSERVED)

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_execution_capability_non_orderbook_quote_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence(
        risex_entry_quote=replace(snapshot.risex_entry_quote, source=ValueSource.OBSERVED),
    )

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_unknown_execution_capability_sources_are_rejected_at_construction() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    with pytest.raises(ValueError, match="source cannot be UNKNOWN"):
        _execution_evidence(source=ValueSource.UNKNOWN)
    with pytest.raises(ValueError, match="executable quote source cannot be UNKNOWN"):
        ExecutableQuote(
            venue=snapshot.risex_entry_quote.venue,
            symbol=snapshot.risex_entry_quote.symbol,
            side=snapshot.risex_entry_quote.side,
            target_notional_usd=route.target_notional_usd,
            vwap_price=Decimal("100"),
            executable=True,
            source=ValueSource.UNKNOWN,
        )


def test_fresh_route_matching_execution_capability_evidence_passes_gate() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _execution_evidence()

    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        execution_evidence=(evidence,),
    )

    assert ok is True
    assert reason is None


def test_live_gate_evidence_bundle_rejects_naive_settlement_at_construction() -> None:
    with pytest.raises(ValueError, match="settlement_time must be timezone-aware"):
        _live_gate_evidence_bundle(settlement_time=datetime(2026, 1, 1, 12, 0))


def test_live_gate_evidence_bundle_rejects_non_bool_verification_flags() -> None:
    with pytest.raises(ValueError, match="funding_settlement_verified must be a bool"):
        _live_gate_evidence_bundle(funding_settlement_verified="true")

    with pytest.raises(ValueError, match="ledger_explicitly_reconciled must be a bool"):
        _live_gate_evidence_bundle(ledger_explicitly_reconciled=1)


def test_live_gate_evidence_bundle_rejects_missing_evidence_sequences_at_construction() -> None:
    with pytest.raises(ValueError, match="capture_plan_evidence must be a tuple"):
        _live_gate_evidence_bundle(capture_plan_evidence=None)

    with pytest.raises(ValueError, match="execution_capability_evidence must be a tuple"):
        _live_gate_evidence_bundle(execution_capability_evidence=None)


def test_missing_live_gate_evidence_bundle_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=None,
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_live_gate_evidence_bundle_requires_exact_capture_route_and_settlement() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    for bundle in (
        _live_gate_evidence_bundle(capture_id="other-capture"),
        _live_gate_evidence_bundle(route_id="other-route"),
        _live_gate_evidence_bundle(
            settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
        ),
    ):
        ok, reason = check_live_gate_evidence_bundle(
            route=route,
            settlement_time=snapshot.risex_funding_settlement_at,
            evaluated_at=snapshot.captured_at,
            live_gate_evidence_bundle=bundle,
        )

        assert ok is False
        assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_live_gate_evidence_bundle_requires_explicit_ledger_reconciliation() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(ledger_explicitly_reconciled=False)

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )

    assert ok is False
    assert reason is RejectReason.LEDGER_NOT_RECONCILED


def test_live_gate_evidence_bundle_requires_verified_funding_settlement() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(funding_settlement_verified=False)

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_live_gate_evidence_bundle_reuses_capture_plan_freshness_gate() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(capture_plan_evidence=())

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_live_gate_evidence_bundle_reuses_execution_capability_gate() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(execution_capability_evidence=())

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )

    assert ok is False
    assert reason is RejectReason.REQUIRED_LIVE_DATA_MISSING


def test_exact_live_gate_evidence_bundle_passes_fake_bundle_gate() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle()

    ok, reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )

    assert ok is True
    assert reason is None
