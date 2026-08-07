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
    append_funding_checkpoint_observed_event,
    append_funding_settlement_evidence_event,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import EstimatedValue, RouteCandidate, VenueSnapshot
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.monitoring.funding_settlement import (
    REQUIRED_FUNDING_CHECKPOINTS,
    FundingCheckpointLabel,
    FundingSettlementVerificationReason,
    replay_funding_settlement_verification,
    verify_funding_settlement,
)
from core.pipeline.evaluate import evaluate_route
from storage.sqlite.ledger import SQLiteLedger


def _observed(value: Decimal | str) -> EstimatedValue:
    return EstimatedValue(value=Decimal(str(value)), source=ValueSource.OBSERVED)


def _unknown() -> EstimatedValue:
    return EstimatedValue(value=None, source=ValueSource.UNKNOWN)


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
    skip: set[FundingCheckpointLabel] | None = None,
    route_id_overrides: dict[FundingCheckpointLabel, str] | None = None,
    settlement_time_offsets: dict[FundingCheckpointLabel, timedelta] | None = None,
) -> None:
    skipped = skip or set()
    route_overrides = route_id_overrides or {}
    time_offsets = settlement_time_offsets or {}

    for requirement in REQUIRED_FUNDING_CHECKPOINTS:
        if requirement.checkpoint in skipped:
            continue
        checkpoint_settlement_time = snapshot.risex_funding_settlement_at + time_offsets.get(
            requirement.checkpoint,
            timedelta(0),
        )
        append_funding_checkpoint_observed_event(
            ledger,
            capture_id=route.capture_id,
            route_id=route_overrides.get(requirement.checkpoint, route.route_id),
            checkpoint=requirement.checkpoint.value,
            settlement_time=checkpoint_settlement_time,
            observed_at=checkpoint_settlement_time - requirement.offset_before_settlement,
            target_notional_usd=route.target_notional_usd,
            risex_expected_funding_usd=snapshot.funding.risex_funding_usd,
            hedge_expected_funding_usd=snapshot.funding.hedge_funding_usd,
        )


def _append_settlement_evidence(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    actual_risex_funding_usd: EstimatedValue | None = None,
    actual_hedge_funding_usd: EstimatedValue | None = None,
    actual_risex_notional_usd: EstimatedValue | None = None,
    actual_hedge_notional_usd: EstimatedValue | None = None,
) -> None:
    append_funding_settlement_evidence_event(
        ledger,
        capture_id=route.capture_id,
        route_id=route.route_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        observed_at=snapshot.risex_funding_settlement_at,
        actual_risex_funding_usd=actual_risex_funding_usd or snapshot.funding.risex_funding_usd,
        actual_hedge_funding_usd=actual_hedge_funding_usd or snapshot.funding.hedge_funding_usd,
        actual_risex_notional_usd=actual_risex_notional_usd or _observed(route.target_notional_usd),
        actual_hedge_notional_usd=actual_hedge_notional_usd or _observed(route.target_notional_usd),
    )


def _append_complete_evidence(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> None:
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)


def test_verifier_records_successful_fake_settlement_from_required_checkpoints() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_evidence(ledger, route=route, snapshot=snapshot)

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is True
    assert result.reasons == ()
    assert result.route_id == route.route_id
    assert len(result.checkpoint_event_sequences) == 4
    assert result.settlement_event_sequence is not None
    assert [event.event_type for event in ledger.records()][-6:] == [
        LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value,
        LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value,
        LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value,
        LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value,
        LedgerEventType.FUNDING_SETTLEMENT_EVIDENCE_RECORDED.value,
        LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED.value,
    ]

    settlement_event = ledger.records()[-2]
    result_event = ledger.records()[-1]
    assert settlement_event.payload["actual_risex_funding_usd"]["value"] == str(
        snapshot.funding.risex_funding_usd.value
    )
    assert settlement_event.payload["actual_hedge_funding_usd"]["value"] == str(
        snapshot.funding.hedge_funding_usd.value
    )
    assert result_event.payload["verified"] is True
    assert result_event.payload["reasons"] == ()
    assert result_event.payload["required_checkpoints"] == tuple(
        requirement.checkpoint.value for requirement in REQUIRED_FUNDING_CHECKPOINTS
    )


def test_verifier_result_replays_deterministically_from_sqlite_ledger_events(tmp_path: Path) -> None:
    db_path = tmp_path / "funding-settlement.sqlite"
    ledger = SQLiteLedger(db_path)
    route, snapshot = _started_paper_capture(ledger)
    _append_complete_evidence(ledger, route=route, snapshot=snapshot)
    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )
    ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()
    replayed_once = replay_funding_settlement_verification(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )
    replayed_twice = replay_funding_settlement_verification(
        records,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
    )

    assert replayed_once == result
    assert replayed_twice == result
    assert records[-1].event_type == LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED.value
    assert records[-1].payload["verified"] is True
    reopened.close()


def test_missing_required_checkpoint_fails_closed_and_records_not_verified() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(
        ledger,
        route=route,
        snapshot=snapshot,
        skip={FundingCheckpointLabel.T_MINUS_10S},
    )
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.MISSING_REQUIRED_CHECKPOINT in result.reasons
    assert ledger.records()[-1].payload["verified"] is False


def test_inconsistent_capture_identity_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(
        ledger,
        route=route,
        snapshot=snapshot,
        route_id_overrides={FundingCheckpointLabel.T_MINUS_5S: "other-route"},
    )
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.INCONSISTENT_CAPTURE_IDENTITY in result.reasons


def test_inconsistent_settlement_time_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(
        ledger,
        route=route,
        snapshot=snapshot,
        settlement_time_offsets={FundingCheckpointLabel.T_MINUS_60S: timedelta(minutes=1)},
    )
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_TIME in result.reasons


def test_inconsistent_funding_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        actual_risex_funding_usd=_observed("4"),
    )

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.INCONSISTENT_FUNDING_EVIDENCE in result.reasons


def test_inconsistent_notional_evidence_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        actual_risex_notional_usd=_observed(route.target_notional_usd + Decimal("1")),
    )

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.INCONSISTENT_NOTIONAL_EVIDENCE in result.reasons


def test_unknown_settlement_funding_or_notional_fails_closed() -> None:
    ledger = InMemoryLedger()
    route, snapshot = _started_paper_capture(ledger)
    _append_required_checkpoints(ledger, route=route, snapshot=snapshot)
    _append_settlement_evidence(
        ledger,
        route=route,
        snapshot=snapshot,
        actual_risex_funding_usd=_unknown(),
        actual_risex_notional_usd=_unknown(),
    )

    result = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    assert result.verified is False
    assert FundingSettlementVerificationReason.UNKNOWN_FUNDING_EVIDENCE in result.reasons
    assert FundingSettlementVerificationReason.UNKNOWN_NOTIONAL_EVIDENCE in result.reasons


def test_live_eligibility_remains_blocked_without_verified_settlement_mechanism() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    ledger = InMemoryLedger()
    _append_settlement_evidence(ledger, route=route, snapshot=snapshot)
    failed_verification = verify_funding_settlement(
        ledger,
        capture_id=route.capture_id,
        settlement_time=snapshot.risex_funding_settlement_at,
        recorded_at=snapshot.risex_funding_settlement_at,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert failed_verification.verified is False
    assert FundingSettlementVerificationReason.MISSING_REQUIRED_CHECKPOINT in failed_verification.reasons
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert RejectReason.LIVE_GATES_NOT_IMPLEMENTED in decision.reasons


def test_funding_settlement_verifier_stays_offline_and_downstream() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    importlib.reload(importlib.import_module("core.monitoring.funding_settlement"))
    source = Path("core/monitoring/funding_settlement.py").read_text()

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
    assert "evaluate_route" not in source
    assert "assemble_route_snapshot" not in source
    assert "calculate_entry_ev" not in source
    assert "core.economics" not in source
    assert "core.risk" not in source
    assert "core.execution" not in source
    assert "apps.live_runner" not in source
    assert "CapturePlan(" not in source
