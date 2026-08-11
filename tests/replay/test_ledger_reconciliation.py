from __future__ import annotations

import importlib
import subprocess
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
    LedgerEvent,
    LedgerEventType,
    append_decision_event,
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
    append_funding_settlement_verification_event,
    append_live_gate_evidence_bundle_event,
    append_paper_capture_closed_event,
    append_paper_capture_opened_event,
    append_paper_settlement_observed_event,
)
from core.accounting.reconciliation import (
    LedgerReconciliationReason,
    is_ledger_explicitly_reconciled,
    reconcile_ledger,
    replay_ledger_reconciliation,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    EstimatedValue,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.monitoring.funding_settlement import REQUIRED_FUNDING_CHECKPOINTS, verify_funding_settlement
from core.pipeline.evaluate import evaluate_route
from core.risk.gates import check_ledger_reconciliation_gate, check_live_gate_evidence_bundle
from storage.sqlite.ledger import SQLiteLedger


def _observed(value: Decimal | str) -> EstimatedValue:
    return EstimatedValue(value=Decimal(str(value)), source=ValueSource.OBSERVED)


def _sourced(value: Decimal | str, source: ValueSource) -> EstimatedValue:
    return EstimatedValue(value=Decimal(str(value)), source=source)


def _started_paper_capture(ledger: Ledger) -> tuple[RouteCandidate, VenueSnapshot]:
    route, snapshot = build_fake_route_and_snapshot()
    decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=(),
        net_profit_usd=Decimal("2"),
        decided_at=snapshot.captured_at,
    )
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
    actual_risex_funding_usd: EstimatedValue | None = None,
    actual_hedge_funding_usd: EstimatedValue | None = None,
    actual_risex_notional_usd: EstimatedValue | None = None,
    actual_hedge_notional_usd: EstimatedValue | None = None,
) -> None:
    append_funding_settlement_evidence_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route_id or route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at,
        actual_risex_funding_usd=actual_risex_funding_usd or snapshot.funding.risex_funding_usd,
        actual_hedge_funding_usd=actual_hedge_funding_usd or snapshot.funding.hedge_funding_usd,
        actual_risex_notional_usd=actual_risex_notional_usd or _observed(route.target_notional_usd),
        actual_hedge_notional_usd=actual_hedge_notional_usd or _observed(route.target_notional_usd),
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


def _event_sequence(
    ledger: Ledger,
    event_type: LedgerEventType,
    *,
    route_id: str | None = None,
) -> int:
    events = tuple(
        event
        for event in ledger.records()
        if event.event_type == event_type.value
        and (route_id is None or event.payload.get("route_id") == route_id)
    )
    assert len(events) == 1
    return events[0].sequence


def _live_gate_evidence_bundle(
    *,
    ledger: Ledger,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> LiveGateEvidenceBundle:
    return LiveGateEvidenceBundle(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        funding_settlement_verified=True,
        ledger_explicitly_reconciled=is_ledger_explicitly_reconciled(ledger.records()),
        capture_plan_evidence=(
            CapturePlanFreshnessEvidence(
                plan_id="fake-plan-001",
                plan_version="fake-v1",
                capture_id=route.capture_id,
                route_id=route.route_id,
                settlement_time=snapshot.risex_funding_settlement_at,
                planned_at=snapshot.captured_at,
                valid_until=snapshot.captured_at + timedelta(minutes=5),
                source=ValueSource.OBSERVED,
                ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
            ),
        ),
        execution_capability_evidence=(
            ExecutionCapabilityEvidence(
                capture_id=route.capture_id,
                route_id=route.route_id,
                settlement_time=snapshot.risex_funding_settlement_at,
                checked_at=snapshot.captured_at,
                valid_until=snapshot.captured_at + timedelta(minutes=1),
                source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
                risex_entry_quote=snapshot.risex_entry_quote,
                hedge_entry_quote=snapshot.hedge_entry_quote,
                risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
                hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
            ),
        ),
    )


def _append_live_gate_bundle_record(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    recorded_bundle_check_passed: bool | None = None,
    recorded_bundle_check_reason: RejectReason | None = None,
) -> None:
    bundle = _live_gate_evidence_bundle(ledger=ledger, route=route, snapshot=snapshot)
    checked_passed, checked_reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
    )
    append_live_gate_evidence_bundle_event(
        ledger,
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        live_gate_evidence_bundle=bundle,
        bundle_check_passed=(
            checked_passed
            if recorded_bundle_check_passed is None
            else recorded_bundle_check_passed
        ),
        bundle_check_reason=(
            checked_reason
            if recorded_bundle_check_reason is None
            else recorded_bundle_check_reason
        ),
        route_decision_event_sequence=_event_sequence(
            ledger,
            LedgerEventType.ROUTE_DECISION_RECORDED,
            route_id=route.route_id,
        ),
        funding_verification_event_sequence=_event_sequence(
            ledger,
            LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED,
            route_id=route.route_id,
        ),
        ledger_reconciliation_event_sequence=_event_sequence(
            ledger,
            LedgerEventType.LEDGER_RECONCILIATION_RECORDED,
            route_id=route.route_id,
        ),
        recorded_at=snapshot.captured_at,
    )


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


def _replace_ledger_event(
    event: LedgerEvent,
    *,
    sequence: int | None = None,
    event_type: str | None = None,
    payload: dict | None = None,
) -> LedgerEvent:
    return LedgerEvent(
        sequence=event.sequence if sequence is None else sequence,
        event_type=event.event_type if event_type is None else event_type,
        payload=event.payload if payload is None else payload,
        recorded_at=event.recorded_at,
    )


def _funding_checkpoint_sequences(ledger: Ledger) -> tuple[int, ...]:
    return tuple(
        event.sequence
        for event in ledger.records()
        if event.event_type == LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value
    )


def _funding_settlement_evidence_sequence(ledger: Ledger) -> int:
    settlement_events = tuple(
        event
        for event in ledger.records()
        if event.event_type == LedgerEventType.FUNDING_SETTLEMENT_EVIDENCE_RECORDED.value
    )
    assert len(settlement_events) == 1
    return settlement_events[0].sequence


def _append_forged_successful_funding_verification(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    required_checkpoints: tuple[str, ...] | None = None,
) -> None:
    append_funding_settlement_verification_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        verified=True,
        reasons=(),
        required_checkpoints=required_checkpoints
        or tuple(requirement.checkpoint.value for requirement in REQUIRED_FUNDING_CHECKPOINTS),
        checkpoint_event_sequences=_funding_checkpoint_sequences(ledger),
        settlement_event_sequence=_funding_settlement_evidence_sequence(ledger),
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
    assert ledger.records()[-1].payload["event_count"] == 10
    assert ledger.records()[-1].payload["last_sequence"] == 10
    assert not hasattr(ledger, "update")
    assert not hasattr(ledger, "delete")


def test_is_ledger_explicitly_reconciled_returns_true_immediately_after_successful_reconciliation() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert is_ledger_explicitly_reconciled(ledger.records()) is True


def test_is_ledger_explicitly_reconciled_returns_false_after_later_append() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    ledger.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={
            "route_id": "later-route",
            "mode": EvaluationMode.ENTRY.value,
            "status": RouteStatus.REJECTED.value,
            "reasons": (RejectReason.USER_RULE_VIOLATED.value,),
            "capture_started": False,
        },
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert is_ledger_explicitly_reconciled(ledger.records()) is False


def test_is_ledger_explicitly_reconciled_returns_false_for_empty_ledger() -> None:
    assert is_ledger_explicitly_reconciled(()) is False


def test_is_ledger_explicitly_reconciled_returns_false_when_latest_is_not_reconciliation() -> None:
    ledger = InMemoryLedger()
    _append_verified_history(ledger)

    assert ledger.records()[-1].event_type == LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED.value
    assert is_ledger_explicitly_reconciled(ledger.records()) is False


def test_is_ledger_explicitly_reconciled_returns_false_for_malformed_reconciliation_payload() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    records = ledger.records()
    malformed_payload = dict(records[-1].payload)
    malformed_payload.pop("event_count")
    malformed_records = records[:-1] + (
        _replace_ledger_event(records[-1], payload=malformed_payload),
    )

    assert is_ledger_explicitly_reconciled(malformed_records) is False


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


def test_reconciliation_accepts_well_formed_live_gate_bundle_record_after_new_reconciliation() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    _append_live_gate_bundle_record(ledger, route=route, snapshot=snapshot)

    assert ledger.records()[-1].event_type == LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value
    assert is_ledger_explicitly_reconciled(ledger.records()) is False

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is True
    assert result.reasons == ()
    assert result.checked_event_sequences == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
    assert ledger.records()[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert ledger.records()[-1].payload["event_count"] == 12
    assert ledger.records()[-1].payload["last_sequence"] == 12
    assert is_ledger_explicitly_reconciled(ledger.records()) is True


def test_reconciliation_replays_sqlite_live_gate_bundle_record_after_new_reconciliation(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "ledger-live-gate-bundle-reconciled.sqlite"
    ledger = SQLiteLedger(db_path)
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    _append_live_gate_bundle_record(ledger, route=route, snapshot=snapshot)
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
    assert replayed_once.reconciled is True
    assert replayed_once.reasons == ()
    assert replayed_once.checked_event_sequences == (
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        12,
    )
    assert records[11].event_type == LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value
    assert records[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert records[-1].payload["event_count"] == 12
    assert records[-1].payload["last_sequence"] == 12
    assert is_ledger_explicitly_reconciled(records) is True
    reopened.close()


def test_sqlite_reopen_append_after_reconciliation_is_stale_until_later_reconciliation(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "ledger-reopen-append-reconciled.sqlite"
    ledger = SQLiteLedger(db_path)
    route, snapshot = _append_verified_history(ledger)
    first_result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    first_records = ledger.records()
    ledger.close()

    assert first_result.reconciled is True
    assert is_ledger_explicitly_reconciled(first_records) is True
    assert first_records[-1].payload["event_count"] == 10
    assert first_records[-1].payload["last_sequence"] == 10

    reopened = SQLiteLedger(db_path)
    reopened_records = reopened.records()
    assert is_ledger_explicitly_reconciled(reopened_records) is True
    assert [event.sequence for event in reopened_records] == list(range(1, 12))

    _append_live_gate_bundle_record(reopened, route=route, snapshot=snapshot)
    stale_records = reopened.records()
    reopened.close()

    assert [event.sequence for event in stale_records] == list(range(1, 13))
    assert stale_records[-1].event_type == LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value
    assert stale_records[-1].sequence == 12
    assert is_ledger_explicitly_reconciled(stale_records) is False
    assert all(
        event.payload.get("status") != RouteStatus.LIVE_ELIGIBLE.value
        for event in stale_records
    )

    stale_reopened = SQLiteLedger(db_path)
    persisted_stale_records = stale_reopened.records()
    assert is_ledger_explicitly_reconciled(persisted_stale_records) is False

    later_result = reconcile_ledger(
        stale_reopened,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    later_records = stale_reopened.records()
    stale_reopened.close()

    assert later_result.reconciled is True
    assert later_result.reasons == ()
    assert later_result.checked_event_sequences == (
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        12,
    )
    assert [event.sequence for event in later_records] == list(range(1, 14))
    assert later_records[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert later_records[-1].payload["event_count"] == 12
    assert later_records[-1].payload["last_sequence"] == 12
    assert is_ledger_explicitly_reconciled(later_records) is True

    final_reopened = SQLiteLedger(db_path)
    final_records = final_reopened.records()
    replayed_once = replay_ledger_reconciliation(
        final_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    replayed_twice = replay_ledger_reconciliation(
        final_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed_once == later_result
    assert replayed_twice == later_result
    assert is_ledger_explicitly_reconciled(final_records) is True
    final_reopened.close()


def test_reconciliation_fails_closed_on_contradictory_live_gate_bundle_record() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        recorded_bundle_check_passed=False,
        recorded_bundle_check_reason=RejectReason.REQUIRED_LIVE_DATA_MISSING,
    )

    assert ledger.records()[-1].event_type == LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert (
        LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE
        in result.reasons
    )
    assert result.checked_event_sequences == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
    assert ledger.records()[-1].event_type == LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
    assert ledger.records()[-1].payload["reconciled"] is False
    assert is_ledger_explicitly_reconciled(ledger.records()) is False


def test_reconciliation_fails_closed_on_malformed_live_gate_bundle_record_payload() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    _append_live_gate_bundle_record(ledger, route=route, snapshot=snapshot)
    records = ledger.records()
    malformed_records = records[:-1] + (
        _replace_ledger_event(records[-1], payload={}),
    )

    result = replay_ledger_reconciliation(
        malformed_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD in result.reasons
    assert is_ledger_explicitly_reconciled(malformed_records) is False


def test_accounting_and_monitoring_direct_imports_work_from_fresh_process() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    commands = (
        "import core.monitoring.funding_settlement; import core.accounting.reconciliation",
        "from core.monitoring.funding_settlement import replay_funding_settlement_verification; "
        "from core.accounting.reconciliation import replay_ledger_reconciliation, "
        "replay_live_gate_evidence_bundle_recording",
    )

    for command in commands:
        completed = subprocess.run(
            [sys.executable, "-c", command],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 0, completed.stderr


def test_forged_verified_funding_result_fails_when_raw_funding_evidence_contradicts_checkpoints() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        actual_risex_funding_usd=_observed("4"),
    )
    _append_forged_successful_funding_verification(
        ledger,
        route=route,
        snapshot=snapshot,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION in result.reasons
    assert is_ledger_explicitly_reconciled(ledger.records()) is False


def test_forged_verified_funding_result_fails_when_actual_settlement_source_is_not_observed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        actual_risex_funding_usd=_sourced(
            snapshot.funding.risex_funding_usd.require_value(),
            ValueSource.USER_CONFIGURED,
        ),
    )
    _append_forged_successful_funding_verification(
        ledger,
        route=route,
        snapshot=snapshot,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION in result.reasons
    assert is_ledger_explicitly_reconciled(ledger.records()) is False


def test_forged_verified_funding_result_fails_when_required_checkpoints_are_not_canonical() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_funding_evidence(ledger, route=route, snapshot=snapshot)
    forged_required_checkpoints = (
        "NOT_CANONICAL",
        *tuple(requirement.checkpoint.value for requirement in REQUIRED_FUNDING_CHECKPOINTS[1:]),
    )
    _append_forged_successful_funding_verification(
        ledger,
        route=route,
        snapshot=snapshot,
        required_checkpoints=forged_required_checkpoints,
    )

    result = reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION in result.reasons
    assert is_ledger_explicitly_reconciled(ledger.records()) is False


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


def test_replay_fails_closed_on_out_of_order_input_without_sorting() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    records = ledger.records()
    out_of_order_records = (records[1], records[0], *records[2:])

    result = replay_ledger_reconciliation(
        out_of_order_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.NON_CONTIGUOUS_LEDGER_SEQUENCE in result.reasons
    assert is_ledger_explicitly_reconciled(out_of_order_records) is False


def test_reconciliation_fails_closed_on_duplicate_sequence() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    records = ledger.records()
    duplicate_sequence_records = records[:1] + (
        _replace_ledger_event(records[1], sequence=1),
        *records[2:],
    )

    result = replay_ledger_reconciliation(
        duplicate_sequence_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.NON_CONTIGUOUS_LEDGER_SEQUENCE in result.reasons
    assert is_ledger_explicitly_reconciled(duplicate_sequence_records) is False


def test_reconciliation_fails_closed_on_non_contiguous_sequence() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    records = ledger.records()
    non_contiguous_records = records[:1] + (
        _replace_ledger_event(records[1], sequence=3),
        *records[2:],
    )

    result = replay_ledger_reconciliation(
        non_contiguous_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.NON_CONTIGUOUS_LEDGER_SEQUENCE in result.reasons
    assert is_ledger_explicitly_reconciled(non_contiguous_records) is False


def test_reconciliation_fails_closed_on_unknown_event_type() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    records = ledger.records()
    unknown_type_records = records[:1] + (
        _replace_ledger_event(records[1], event_type="unknown_ledger_event"),
        *records[2:],
    )

    result = replay_ledger_reconciliation(
        unknown_type_records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert result.reconciled is False
    assert LedgerReconciliationReason.UNKNOWN_LEDGER_EVENT_TYPE in result.reasons
    assert is_ledger_explicitly_reconciled(unknown_type_records) is False


def test_reconciliation_fails_closed_on_malformed_known_event_payloads() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    records = ledger.records()

    for event_index in (0, 1, 4, 8, 9, 10):
        malformed_records = records[:event_index] + (
            _replace_ledger_event(records[event_index], payload={}),
            *records[event_index + 1 :],
        )
        result = replay_ledger_reconciliation(
            malformed_records,
            capture_id=route.capture_id,
            settlement_time=snapshot.risex_funding_settlement_at,
        )

        assert result.reconciled is False
        assert LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD in result.reasons
        assert is_ledger_explicitly_reconciled(malformed_records) is False


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


def test_future_live_gate_requires_helper_derived_explicit_reconciliation() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _append_verified_history(ledger)
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    helper_derived_reconciliation = is_ledger_explicitly_reconciled(ledger.records())

    ok, reason = check_ledger_reconciliation_gate(False)
    assert ok is False
    assert reason is RejectReason.LEDGER_NOT_RECONCILED
    assert helper_derived_reconciliation is True
    assert check_ledger_reconciliation_gate(helper_derived_reconciliation) == (True, None)

    unreconciled_decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )
    missing_plan_decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        ledger_explicitly_reconciled=helper_derived_reconciliation,
    )

    assert unreconciled_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert unreconciled_decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert unreconciled_decision.capture_plan is None
    assert unreconciled_decision.reasons == (RejectReason.LEDGER_NOT_RECONCILED,)
    assert missing_plan_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert missing_plan_decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert missing_plan_decision.capture_plan is None
    assert missing_plan_decision.reasons == (RejectReason.CAPTURE_PLAN_NOT_FRESH,)

    ledger.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={
            "route_id": "later-route",
            "mode": EvaluationMode.ENTRY.value,
            "status": RouteStatus.REJECTED.value,
            "reasons": (RejectReason.USER_RULE_VIOLATED.value,),
            "capture_started": False,
        },
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    stale_reconciliation = is_ledger_explicitly_reconciled(ledger.records())
    stale_decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        ledger_explicitly_reconciled=stale_reconciliation,
    )

    assert stale_reconciliation is False
    assert stale_decision.reasons == (RejectReason.LEDGER_NOT_RECONCILED,)


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
