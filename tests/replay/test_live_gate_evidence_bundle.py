from __future__ import annotations

import importlib
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from apps.paper_runner.lifecycle import run_paper_lifecycle
from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import (
    InMemoryLedger,
    Ledger,
    LedgerEventType,
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
    append_live_gate_evidence_bundle_event,
)
from core.accounting.reconciliation import (
    LedgerReconciliationReason,
    is_ledger_explicitly_reconciled,
    reconcile_ledger,
    replay_live_gate_evidence_bundle_recording,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import (
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
from core.monitoring.funding_settlement import (
    REQUIRED_FUNDING_CHECKPOINTS,
    FundingSettlementVerificationResult,
    verify_funding_settlement,
)
from core.pipeline.evaluate import evaluate_route
from core.risk.gates import check_live_gate_evidence_bundle
from storage.sqlite.ledger import SQLiteLedger


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
) -> None:
    append_funding_settlement_evidence_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at,
        actual_risex_funding_usd=snapshot.funding.risex_funding_usd,
        actual_hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        actual_risex_notional_usd=_observed(route.target_notional_usd),
        actual_hedge_notional_usd=_observed(route.target_notional_usd),
    )


def _verified_reconciled_fake_history(
    ledger: Ledger | None = None,
) -> tuple[
    Ledger,
    RouteCandidate,
    VenueSnapshot,
    FundingSettlementVerificationResult,
]:
    ledger = ledger or InMemoryLedger()
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
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)
    funding_result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    reconcile_ledger(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    return ledger, route, snapshot, funding_result


def _fresh_plan_evidence(
    *,
    ledger: Ledger,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> CapturePlanFreshnessEvidence:
    return CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="fake-v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at,
        valid_until=snapshot.captured_at + timedelta(minutes=5),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )


def _execution_evidence(
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    risex_entry_quote: ExecutableQuote | None = None,
) -> ExecutionCapabilityEvidence:
    return ExecutionCapabilityEvidence(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        checked_at=snapshot.captured_at,
        valid_until=snapshot.captured_at + timedelta(minutes=1),
        source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
        risex_entry_quote=risex_entry_quote or snapshot.risex_entry_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
        hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
    )


def _live_gate_evidence_bundle(
    *,
    ledger: Ledger,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    funding_result: FundingSettlementVerificationResult,
    ledger_explicitly_reconciled: bool | None = None,
    capture_plan_evidence: tuple[CapturePlanFreshnessEvidence, ...] | None = None,
    execution_capability_evidence: tuple[ExecutionCapabilityEvidence, ...] | None = None,
    funding_settlement_verified: bool | None = None,
) -> LiveGateEvidenceBundle:
    return LiveGateEvidenceBundle(
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        funding_settlement_verified=(
            funding_result.verified
            if funding_settlement_verified is None
            else funding_settlement_verified
        ),
        ledger_explicitly_reconciled=(
            is_ledger_explicitly_reconciled(ledger.records())
            if ledger_explicitly_reconciled is None
            else ledger_explicitly_reconciled
        ),
        capture_plan_evidence=(
            (_fresh_plan_evidence(ledger=ledger, route=route, snapshot=snapshot),)
            if capture_plan_evidence is None
            else capture_plan_evidence
        ),
        execution_capability_evidence=(
            (_execution_evidence(route=route, snapshot=snapshot),)
            if execution_capability_evidence is None
            else execution_capability_evidence
        ),
    )


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


_USE_CHECKED_BUNDLE_RESULT = object()


def _append_live_gate_bundle_record(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    bundle: LiveGateEvidenceBundle,
    bundle_check_passed: bool | object = _USE_CHECKED_BUNDLE_RESULT,
    bundle_check_reason: RejectReason | None | object = _USE_CHECKED_BUNDLE_RESULT,
) -> None:
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
            if bundle_check_passed is _USE_CHECKED_BUNDLE_RESULT
            else bundle_check_passed
        ),
        bundle_check_reason=(
            checked_reason
            if bundle_check_reason is _USE_CHECKED_BUNDLE_RESULT
            else bundle_check_reason
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


def test_exact_fake_live_gate_evidence_bundle_still_stops_at_unimplemented_live_gates() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    helper_derived_reconciliation = is_ledger_explicitly_reconciled(ledger.records())
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        ledger_explicitly_reconciled=helper_derived_reconciliation,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert funding_result.verified is True
    assert helper_derived_reconciliation is True
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_GATES_NOT_IMPLEMENTED,)


def test_successful_live_gate_evidence_bundle_record_replays_without_enabling_live() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    helper_derived_reconciliation = is_ledger_explicitly_reconciled(ledger.records())
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        ledger_explicitly_reconciled=helper_derived_reconciliation,
    )

    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )
    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert replayed.replayed is True
    assert replayed.bundle_check_passed is True
    assert replayed.bundle_check_reason is None
    assert replayed.route_id == route.route_id
    assert replayed.live_gate_evidence_bundle_event_sequence == 12
    assert replayed.route_decision_event_sequence == 1
    assert replayed.funding_verification_event_sequence == 10
    assert replayed.ledger_reconciliation_event_sequence == 11
    assert is_ledger_explicitly_reconciled(ledger.records()) is False
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_GATES_NOT_IMPLEMENTED,)


def test_successful_live_gate_evidence_bundle_record_replays_after_sqlite_round_trip(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "live-gate-bundle.sqlite"
    sqlite_ledger = SQLiteLedger(db_path)
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history(
        sqlite_ledger
    )
    helper_derived_reconciliation = is_ledger_explicitly_reconciled(ledger.records())
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        ledger_explicitly_reconciled=helper_derived_reconciliation,
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )
    pre_close_replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    sqlite_ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()
    replayed_once = replay_live_gate_evidence_bundle_recording(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    replayed_twice = replay_live_gate_evidence_bundle_recording(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed_once == pre_close_replayed
    assert replayed_twice == pre_close_replayed
    assert replayed_once.replayed is True
    assert replayed_once.bundle_check_passed is True
    assert replayed_once.bundle_check_reason is None
    assert replayed_once.live_gate_evidence_bundle_event_sequence == 12
    assert replayed_once.route_decision_event_sequence == 1
    assert replayed_once.funding_verification_event_sequence == 10
    assert replayed_once.ledger_reconciliation_event_sequence == 11
    assert records[-1].event_type == LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value
    assert is_ledger_explicitly_reconciled(records) is False
    reopened.close()


def test_failed_live_gate_evidence_bundle_record_replays_fail_closed_reason() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    stale_plan = CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="fake-v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at - timedelta(seconds=2),
        valid_until=snapshot.captured_at - timedelta(seconds=1),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        capture_plan_evidence=(stale_plan,),
    )

    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )
    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is True
    assert replayed.bundle_check_passed is False
    assert replayed.bundle_check_reason is RejectReason.CAPTURE_PLAN_NOT_FRESH
    assert replayed.reasons == ()


def test_contradictory_live_gate_evidence_bundle_record_fails_after_sqlite_round_trip(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "live-gate-bundle-contradictory.sqlite"
    sqlite_ledger = SQLiteLedger(db_path)
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history(
        sqlite_ledger
    )
    stale_plan = CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="fake-v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at - timedelta(seconds=2),
        valid_until=snapshot.captured_at - timedelta(seconds=1),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        capture_plan_evidence=(stale_plan,),
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
        bundle_check_passed=True,
        bundle_check_reason=None,
    )
    sqlite_ledger.close()

    reopened = SQLiteLedger(db_path)
    replayed = replay_live_gate_evidence_bundle_recording(
        reopened.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is False
    assert (
        LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE
        in replayed.reasons
    )
    reopened.close()


def test_malformed_live_gate_evidence_bundle_record_fails_after_sqlite_round_trip(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "live-gate-bundle-malformed.sqlite"
    sqlite_ledger = SQLiteLedger(db_path)
    ledger, route, snapshot, _funding_result = _verified_reconciled_fake_history(
        sqlite_ledger
    )
    ledger.append(
        event_type=LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED,
        payload={"capture_id": route.capture_id},
        recorded_at=snapshot.captured_at,
    )
    sqlite_ledger.close()

    reopened = SQLiteLedger(db_path)
    replayed = replay_live_gate_evidence_bundle_recording(
        reopened.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is False
    assert LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD in replayed.reasons
    assert replayed.live_gate_evidence_bundle_event_sequence == 12
    reopened.close()


def test_live_gate_evidence_bundle_recording_replay_fails_closed_when_missing() -> None:
    ledger, route, snapshot, _funding_result = _verified_reconciled_fake_history()

    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is False
    assert replayed.bundle_check_passed is False
    assert (
        LedgerReconciliationReason.MISSING_LIVE_GATE_EVIDENCE_BUNDLE
        in replayed.reasons
    )


def test_live_gate_evidence_bundle_recording_replay_fails_closed_when_duplicated() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )

    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is False
    assert (
        LedgerReconciliationReason.DUPLICATED_LIVE_GATE_EVIDENCE_BUNDLE
        in replayed.reasons
    )


def test_live_gate_evidence_bundle_recording_replay_fails_closed_on_contradictory_result() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    stale_plan = CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="fake-v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at - timedelta(seconds=2),
        valid_until=snapshot.captured_at - timedelta(seconds=1),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        capture_plan_evidence=(stale_plan,),
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
        bundle_check_passed=True,
        bundle_check_reason=None,
    )

    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed.replayed is False
    assert (
        LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE
        in replayed.reasons
    )


def test_live_gate_evidence_bundle_recording_replay_fails_closed_on_stale_reconciliation_reference() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
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
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        ledger_explicitly_reconciled=True,
    )
    _append_live_gate_bundle_record(
        ledger,
        route=route,
        snapshot=snapshot,
        bundle=bundle,
    )

    replayed = replay_live_gate_evidence_bundle_recording(
        ledger.records(),
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert is_ledger_explicitly_reconciled(ledger.records()) is False
    assert replayed.replayed is False
    assert (
        LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE
        in replayed.reasons
    )


def test_live_gate_evidence_bundle_does_not_bypass_live_disabled() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=False),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_TRADING_DISABLED,)


def test_live_gate_evidence_bundle_requires_helper_derived_reconciliation() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
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
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        ledger_explicitly_reconciled=stale_reconciliation,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert stale_reconciliation is False
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LEDGER_NOT_RECONCILED,)


def test_live_gate_evidence_bundle_requires_verified_funding_settlement_result() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        funding_settlement_verified=False,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert funding_result.verified is True
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)


def test_live_gate_evidence_bundle_reuses_capture_plan_freshness_fail_closed_behavior() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
    stale_plan = CapturePlanFreshnessEvidence(
        plan_id="fake-plan-001",
        plan_version="fake-v1",
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        planned_at=snapshot.captured_at - timedelta(seconds=2),
        valid_until=snapshot.captured_at - timedelta(seconds=1),
        source=ValueSource.OBSERVED,
        ledger_reconciliation_event_sequence=ledger.records()[-1].sequence,
    )
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        capture_plan_evidence=(stale_plan,),
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.CAPTURE_PLAN_NOT_FRESH,)


def test_live_gate_evidence_bundle_reuses_execution_capability_fail_closed_behavior() -> None:
    ledger, route, snapshot, funding_result = _verified_reconciled_fake_history()
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
    bundle = _live_gate_evidence_bundle(
        ledger=ledger,
        route=route,
        snapshot=snapshot,
        funding_result=funding_result,
        execution_capability_evidence=(
            _execution_evidence(
                route=route,
                snapshot=snapshot,
                risex_entry_quote=partial_quote,
            ),
        ),
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_live_gate_evidence_bundle_path_stays_offline_and_non_executable() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    importlib.reload(importlib.import_module("core.risk.gates"))
    importlib.reload(importlib.import_module("core.pipeline.evaluate"))
    repo_root = Path(__file__).resolve().parents[2]
    checked_sources = (
        repo_root / "core/domain/contracts.py",
        repo_root / "core/risk/gates.py",
        repo_root / "core/pipeline/evaluate.py",
    )
    source = "\n".join(path.read_text() for path in checked_sources)

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
    assert "core.execution" not in source
    assert "apps.live_runner" not in source
    assert "core.venues" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "aiohttp" not in source
    assert "CapturePlan(" not in source
