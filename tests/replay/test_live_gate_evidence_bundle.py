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
from core.accounting.reconciliation import is_ledger_explicitly_reconciled, reconcile_ledger
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
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


def _verified_reconciled_fake_history() -> tuple[
    InMemoryLedger,
    RouteCandidate,
    VenueSnapshot,
    FundingSettlementVerificationResult,
]:
    ledger = InMemoryLedger()
    route, snapshot = build_fake_route_and_snapshot()
    decision = replace(
        evaluate_route(route, snapshot, EvaluationMode.ENTRY),
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
    ledger: InMemoryLedger,
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
    ledger: InMemoryLedger,
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
