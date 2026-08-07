from __future__ import annotations

import importlib
import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from apps.paper_runner.lifecycle import run_paper_lifecycle
from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import (
    InMemoryLedger,
    Ledger,
    LedgerEventType,
    append_decision_event,
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
    append_funding_settlement_verification_event,
    append_paper_capture_closed_event,
    append_paper_capture_opened_event,
    append_paper_settlement_observed_event,
)
from core.accounting.reconciliation import (
    LedgerReconciliationReason,
    reconcile_ledger,
    replay_ledger_reconciliation,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import Capture, EstimatedValue, RouteCandidate, VenueSnapshot
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.monitoring.funding_settlement import REQUIRED_FUNDING_CHECKPOINTS, verify_funding_settlement
from core.pipeline.evaluate import evaluate_route
from core.risk.gates import check_ledger_reconciliation_gate
from storage.sqlite.ledger import SQLiteLedger


def _observed(value: Decimal | str) -> EstimatedValue:
    return EstimatedValue(value=Decimal(str(value)), source=ValueSource.OBSERVED)


def _started_paper_capture(ledger: Ledger) -> tuple[RouteCandidate, VenueSnapshot]:
    route, snapshot = build_fake_route_and_snapshot()
    decision = replace(evaluate_route(route, snapshot, EvaluationMode.ENTRY), decided_at=snapshot.captured_at)
    run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )
    return route, snapshot


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
            observed_at=snapshot.risex_funding_settlement_at - requirement.offset_before_settlement,
            target_notional_usd=route.target_notional_usd,
            risex_expected_funding_usd=snapshot.funding.risex_funding_usd,
            hedge_expected_funding_usd=snapshot.funding.hedge_funding_usd,
        )


def _append_settlement_evidence(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    route_id: str | None = None,
) -> None:
    append_funding_settlement_evidence_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route_id or route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at,
        actual_risex_funding_usd=snapshot.funding.risex_funding_usd,
        actual_hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        actual_risex_notional_usd=_observed(route.target_notional_usd),
        actual_hedge_notional_usd=_observed(route.target_notional_usd),
    )


def _append_complete_funding_evidence(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> None:
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)


def _append_verified_history(ledger: Ledger) -> tuple[RouteCandidate, VenueSnapshot]:
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    return route, snapshot


def _append_paper_lifecycle_without_route_decision(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> None:
    opened_capture = Capture(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        state=CaptureState.WAITING_SETTLEMENT,
    )
    settled_capture = replace(opened_capture, state=CaptureState.SETTLED)
    closed_capture = replace(opened_capture, state=CaptureState.CLOSED)

    append_paper_capture_opened_event(
        ledger,
        capture=opened_capture,
        state_path=(
            CaptureState.DISCOVERED,
            CaptureState.UNDERWRITING,
            CaptureState.APPROVED,
            CaptureState.ENTERING,
            CaptureState.HEDGED,
            CaptureState.WAITING_SETTLEMENT,
        ),
        recorded_at=snapshot.captured_at,
    )
    append_paper_settlement_observed_event(
        ledger,
        capture=settled_capture,
        state_path=(CaptureState.WAITING_SETTLEMENT, CaptureState.SETTLED),
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    append_paper_capture_closed_event(
        ledger,
        capture=closed_capture,
        state_path=(CaptureState.SETTLED, CaptureState.EXITING, CaptureState.CLOSED),
        recorded_at=snapshot.risex_funding_settlement_at,
    )


def test_reconciliation_records_successful_fake_history() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is True
    assert result.reasons == ()
    assert result.route_id == route.route_id
    assert result.route_decision_event_sequence == 1
    assert result.paper_event_sequences == (2, 3, 4)
    assert result.funding_verification_event_sequence == 10
    assert result.checked_event_sequences == tuple(range(1, 11))
    assert ledger.records()[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert ledger.records()[-1].payload["reconciled"] is True
    assert ledger.records()[-1].payload["reasons"] == ()
    assert not hasattr(ledger, "update")
    assert not hasattr(ledger, "delete")


def test_reconciled_replay_from_sqlite_ledger_events_is_deterministic(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger-reconciled.sqlite"
    ledger = SQLiteLedger(db_path)
    route, snapshot = _append_verified_history(ledger)
    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()
    replayed_once = replay_ledger_reconciliation(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    replayed_twice = replay_ledger_reconciliation(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed_once == result
    assert replayed_twice == result
    assert records[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert records[-1].payload["reconciled"] is True
    reopened.close()


def test_unreconciled_replay_from_missing_funding_verification_is_deterministic(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "ledger-unreconciled.sqlite"
    ledger = SQLiteLedger(db_path)
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()
    replayed_once = replay_ledger_reconciliation(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    replayed_twice = replay_ledger_reconciliation(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert replayed_once == result
    assert replayed_twice == result
    assert LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_VERIFICATION in result.reasons
    assert records[-1].payload["reconciled"] is False
    reopened.close()


def test_missing_route_decision_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = build_fake_route_and_snapshot()
    _append_paper_lifecycle_without_route_decision(ledger, route=route, snapshot=snapshot)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.MISSING_ROUTE_DECISION in result.reasons
    assert ledger.records()[-1].payload["reconciled"] is False


def test_missing_paper_lifecycle_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = build_fake_route_and_snapshot()
    decision = replace(evaluate_route(route, snapshot, EvaluationMode.ENTRY), decided_at=snapshot.captured_at)
    append_decision_event(ledger, decision, recorded_at=snapshot.captured_at)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.MISSING_PAPER_LIFECYCLE_EVIDENCE in result.reasons


def test_duplicated_route_decision_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = build_fake_route_and_snapshot()
    decision = replace(evaluate_route(route, snapshot, EvaluationMode.ENTRY), decided_at=snapshot.captured_at)
    append_decision_event(ledger, decision, recorded_at=snapshot.captured_at)
    run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.DUPLICATED_ROUTE_DECISION_EVIDENCE in result.reasons


def test_duplicated_funding_verification_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.DUPLICATED_FUNDING_SETTLEMENT_VERIFICATION in result.reasons


def test_duplicated_checkpoint_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    append_funding_checkpoint_observed_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        checkpoint=REQUIRED_FUNDING_CHECKPOINTS[0].checkpoint.value,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at
        - REQUIRED_FUNDING_CHECKPOINTS[0].offset_before_settlement,
        target_notional_usd=route.target_notional_usd,
        risex_expected_funding_usd=snapshot.funding.risex_funding_usd,
        hedge_expected_funding_usd=snapshot.funding.hedge_funding_usd,
    )
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.DUPLICATED_FUNDING_SETTLEMENT_EVIDENCE in result.reasons


def test_out_of_order_funding_verification_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    next_sequence = len(ledger.records()) + 1
    checkpoint_sequences = tuple(
        next_sequence + offset
        for offset, _requirement in enumerate(REQUIRED_FUNDING_CHECKPOINTS, start=1)
    )
    settlement_sequence = checkpoint_sequences[-1] + 1

    append_funding_settlement_verification_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        verified=True,
        reasons=(),
        required_checkpoints=tuple(requirement.checkpoint.value for requirement in REQUIRED_FUNDING_CHECKPOINTS),
        checkpoint_event_sequences=checkpoint_sequences,
        settlement_event_sequence=settlement_sequence,
        recorded_at=snapshot.risex_funding_settlement_at - timedelta(seconds=1),
    )
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE in result.reasons


def test_contradictory_capture_identity_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        route_id="other-route",
    )
    verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE in result.reasons


def test_future_live_gate_requires_explicit_reconciliation_true() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    ok, reason = check_ledger_reconciliation_gate(False)
    assert ok is False
    assert reason is RejectReason.LEDGER_NOT_RECONCILED
    assert check_ledger_reconciliation_gate(True) == (True, None)

    unreconciled_decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )
    reconciled_decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        ledger_reconciled=True,
    )

    assert unreconciled_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert unreconciled_decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert unreconciled_decision.capture_plan is None
    assert unreconciled_decision.reasons == (RejectReason.LEDGER_NOT_RECONCILED,)
    assert reconciled_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert reconciled_decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert reconciled_decision.capture_plan is None
    assert reconciled_decision.reasons == (RejectReason.LIVE_GATES_NOT_IMPLEMENTED,)


def test_ledger_reconciliation_stays_offline_and_downstream() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    importlib.reload(importlib.import_module("core.accounting.reconciliation"))
    source = Path("core/accounting/reconciliation.py").read_text()

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
    assert "evaluate_route" not in source
    assert "assemble_route_snapshot" not in source
    assert "calculate_entry_ev" not in source
    assert "core.pipeline" not in source
    assert "core.economics" not in source
    assert "core.execution" not in source
    assert "apps.live_runner" not in source
    assert "CapturePlan(" not in source
