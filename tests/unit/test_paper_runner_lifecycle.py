from __future__ import annotations

import importlib
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from apps.research_runner.fake_data import (
    build_fake_route_and_snapshot,
    build_fake_route_candidates_and_observations,
)
from core.accounting.ledger import (
    InMemoryLedger,
    LedgerEventType,
    replay_paper_captures,
)
from core.domain.contracts import (
    DecisionResult,
    EstimatedValue,
    FeeComponent,
    FeeModel,
    FundingSnapshot,
)
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus
from core.pipeline.evaluate import evaluate_route
from core.pipeline.scan_refresh import run_broad_scan


def _paper_eligible_decision() -> tuple:
    route, snapshot = build_fake_route_and_snapshot()
    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)
    return route, snapshot, replace(decision, decided_at=snapshot.captured_at)


def _below_min_profit_decision() -> tuple:
    route, snapshot = build_fake_route_and_snapshot()
    low_profit_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(
                value=Decimal("0.1"),
                source=snapshot.funding.risex_funding_usd.source,
            ),
            hedge_funding_usd=EstimatedValue(
                value=Decimal("0"),
                source=snapshot.funding.hedge_funding_usd.source,
            ),
        ),
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="zero_fees",
                    amount_usd=EstimatedValue(
                        value=Decimal("0"),
                        source=snapshot.fees.components[0].amount_usd.source,
                    ),
                ),
            )
        ),
    )
    decision = evaluate_route(route, low_profit_snapshot, EvaluationMode.ENTRY)
    return route, low_profit_snapshot, replace(decision, decided_at=snapshot.captured_at)


def _assert_explanation_preserves_decision_pnl(result, decision: DecisionResult) -> None:
    assert result.explanation.net_profit_usd == decision.net_profit_usd
    if decision.entry_ev is None:
        assert result.explanation.expected_funding_usd is None
        assert result.explanation.total_fees_usd is None
        assert result.explanation.simulated_roundtrip_cost_usd is None
        return

    assert result.explanation.expected_funding_usd == decision.entry_ev.expected_funding_usd
    assert result.explanation.total_fees_usd == decision.entry_ev.total_fees_usd
    assert result.explanation.simulated_roundtrip_cost_usd == (
        decision.entry_ev.simulated_roundtrip_cost_usd
    )


def _assert_non_started_with_rejection_events(result, ledger: InMemoryLedger) -> None:
    assert result.started is False
    assert result.capture is None
    assert result.state_path == ()
    assert [event.event_type for event in ledger.records()] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_REJECTION_RECORDED.value,
    ]
    assert ledger.records()[1].payload["capture_started"] is False
    paper_explanation = ledger.records()[1].payload["paper_result_explanation"]
    assert paper_explanation["paper_started"] is False
    assert paper_explanation["paper_start_blockers"]
    expected_net_profit = (
        str(result.explanation.net_profit_usd)
        if result.explanation.net_profit_usd is not None
        else None
    )
    assert paper_explanation["pnl_explanation"]["net_profit_usd"] == (
        expected_net_profit
    )


def test_paper_lifecycle_starts_only_from_entry_paper_eligible_decision() -> None:
    route, snapshot, decision = _paper_eligible_decision()
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    assert result.started is True
    assert result.capture is not None
    assert result.capture.capture_id == route.capture_id
    assert result.capture.route_id == route.route_id
    assert result.capture.settlement_time == snapshot.risex_funding_settlement_at
    assert result.capture.state is CaptureState.CLOSED
    assert result.explanation.paper_started is True
    assert result.explanation.paper_start_attribution == "entry_paper_eligible_decision"
    assert result.explanation.paper_start_blockers == ()
    _assert_explanation_preserves_decision_pnl(result, decision)
    assert result.state_path == (
        CaptureState.DISCOVERED,
        CaptureState.UNDERWRITING,
        CaptureState.APPROVED,
        CaptureState.ENTERING,
        CaptureState.HEDGED,
        CaptureState.WAITING_SETTLEMENT,
        CaptureState.SETTLED,
        CaptureState.EXITING,
        CaptureState.CLOSED,
    )
    assert [event.event_type for event in ledger.records()] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_CAPTURE_OPENED.value,
        LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
        LedgerEventType.PAPER_CAPTURE_CLOSED.value,
    ]
    paper_explanation = ledger.records()[1].payload["paper_result_explanation"]
    assert paper_explanation["paper_started"] is True
    assert paper_explanation["paper_start_attribution"] == "entry_paper_eligible_decision"
    assert paper_explanation["paper_start_blockers"] == ()
    assert paper_explanation["pnl_explanation"] == {
        "expected_funding_usd": str(decision.entry_ev.expected_funding_usd),
        "total_fees_usd": str(decision.entry_ev.total_fees_usd),
        "simulated_roundtrip_cost_usd": str(decision.entry_ev.simulated_roundtrip_cost_usd),
        "net_profit_usd": str(decision.net_profit_usd),
    }


def test_paper_eligible_discovery_decision_does_not_start_capture_execution() -> None:
    route, snapshot, entry_decision = _paper_eligible_decision()
    discovery_decision = replace(entry_decision, mode=EvaluationMode.DISCOVERY)
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=discovery_decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    _assert_non_started_with_rejection_events(result, ledger)
    assert result.decision is discovery_decision
    assert discovery_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert discovery_decision.mode is EvaluationMode.DISCOVERY
    assert result.explanation.paper_start_attribution == "paper_start_blocked_by_decision"
    assert result.explanation.paper_start_blockers == ("decision_mode_not_entry",)
    _assert_explanation_preserves_decision_pnl(result, discovery_decision)


def test_broad_scan_paper_eligible_decisions_do_not_start_capture_execution() -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    broad_scan = run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
    )
    eligible_index = next(
        index
        for index, decision in enumerate(broad_scan.decisions)
        if decision.status is RouteStatus.PAPER_ELIGIBLE
    )
    route = routes[eligible_index]
    decision = broad_scan.decisions[eligible_index]
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=observations[(route.risex_venue, route.risex_symbol)].funding_settlement_at,
        ledger=ledger,
    )

    assert decision.mode is EvaluationMode.DISCOVERY
    _assert_non_started_with_rejection_events(result, ledger)
    assert result.explanation.paper_start_blockers == ("decision_mode_not_entry",)


@pytest.mark.parametrize(
    "status",
    (RouteStatus.REJECTED, RouteStatus.RESEARCH_ONLY, RouteStatus.LIVE_ELIGIBLE),
)
def test_non_paper_eligible_decisions_do_not_start_capture_execution(status: RouteStatus) -> None:
    route, snapshot, _ = _paper_eligible_decision()
    ledger = InMemoryLedger()
    decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=status,
        reasons=(RejectReason.MIN_NET_PROFIT_NOT_MET,) if status is RouteStatus.REJECTED else (),
        capture_plan=None,
        decided_at=snapshot.captured_at,
    )
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    _assert_non_started_with_rejection_events(result, ledger)
    assert result.explanation.paper_start_blockers == ("decision_status_not_paper_eligible",)


def test_rejected_entry_decision_preserves_existing_pnl_explanation_without_starting() -> None:
    route, snapshot, decision = _below_min_profit_decision()
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.MIN_NET_PROFIT_NOT_MET,)
    assert decision.entry_ev is not None

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    _assert_non_started_with_rejection_events(result, ledger)
    assert result.explanation.paper_start_blockers == ("decision_status_not_paper_eligible",)
    _assert_explanation_preserves_decision_pnl(result, decision)
    paper_explanation = ledger.records()[1].payload["paper_result_explanation"]
    assert paper_explanation["decision_reasons"] == (RejectReason.MIN_NET_PROFIT_NOT_MET.value,)
    assert paper_explanation["pnl_explanation"] == {
        "expected_funding_usd": str(decision.entry_ev.expected_funding_usd),
        "total_fees_usd": str(decision.entry_ev.total_fees_usd),
        "simulated_roundtrip_cost_usd": str(decision.entry_ev.simulated_roundtrip_cost_usd),
        "net_profit_usd": str(decision.net_profit_usd),
    }


def test_missing_entry_ev_stays_unknown_in_paper_pnl_explanation() -> None:
    route, snapshot, _ = _paper_eligible_decision()
    ledger = InMemoryLedger()
    decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=RouteStatus.REJECTED,
        reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
        net_profit_usd=None,
        entry_ev=None,
        capture_plan=None,
        decided_at=snapshot.captured_at,
    )
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    _assert_non_started_with_rejection_events(result, ledger)
    assert result.explanation.expected_funding_usd is None
    assert result.explanation.total_fees_usd is None
    assert result.explanation.simulated_roundtrip_cost_usd is None
    assert result.explanation.net_profit_usd is None
    assert ledger.records()[1].payload["paper_result_explanation"]["pnl_explanation"] == {
        "expected_funding_usd": None,
        "total_fees_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "net_profit_usd": None,
    }


def test_lifecycle_transitions_use_single_capture_state_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    route, snapshot, decision = _paper_eligible_decision()
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")
    real_transition_capture = paper_runner.transition_capture
    target_states: list[CaptureState] = []

    def counting_transition_capture(capture, target):
        target_states.append(target)
        return real_transition_capture(capture, target)

    monkeypatch.setattr(paper_runner, "transition_capture", counting_transition_capture)

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    assert result.capture is not None
    assert result.capture.state is CaptureState.CLOSED
    assert target_states == [
        CaptureState.UNDERWRITING,
        CaptureState.APPROVED,
        CaptureState.ENTERING,
        CaptureState.HEDGED,
        CaptureState.WAITING_SETTLEMENT,
        CaptureState.SETTLED,
        CaptureState.EXITING,
        CaptureState.CLOSED,
    ]


def test_one_capture_represents_one_funding_settlement_opportunity() -> None:
    route, snapshot, decision = _paper_eligible_decision()
    ledger = InMemoryLedger()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )

    paper_events = tuple(
        event
        for event in ledger.records()
        if event.event_type
        in {
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        }
    )
    assert {event.payload["capture_id"] for event in paper_events} == {route.capture_id}
    assert {event.payload["settlement_time"] for event in paper_events} == {
        snapshot.risex_funding_settlement_at.isoformat()
    }

    replayed_once = replay_paper_captures(ledger.records())
    replayed_twice = replay_paper_captures(ledger.records())
    assert replayed_once == replayed_twice
    assert len(replayed_once) == 1
    assert replayed_once[0].capture.capture_id == route.capture_id
    assert replayed_once[0].capture.state is CaptureState.CLOSED
    assert replayed_once[0].event_sequences == tuple(event.sequence for event in paper_events)


def test_paper_runner_does_not_import_live_runner_or_execution_modules() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    paper_runner = importlib.reload(importlib.import_module("apps.paper_runner.lifecycle"))
    route, snapshot, decision = _paper_eligible_decision()

    paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=InMemoryLedger(),
    )

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)


def test_paper_runner_does_not_create_capture_plans_or_second_decision_logic() -> None:
    source = Path("apps/paper_runner/lifecycle.py").read_text()
    route, snapshot, decision = _paper_eligible_decision()
    paper_runner = importlib.import_module("apps.paper_runner.lifecycle")

    result = paper_runner.run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=InMemoryLedger(),
    )

    assert result.decision is decision
    assert decision.capture_plan is None
    assert "CapturePlan(" not in source
    assert "evaluate_route" not in source
    assert "assemble_route_snapshot" not in source
    assert "calculate_entry_ev" not in source
    assert "core.execution" not in source
    assert "apps.live_runner" not in source
