from __future__ import annotations

import importlib
import sys

from apps.research_runner.fake_data import build_fake_route_candidates_and_observations
from core.config.product_rules import ProductRules
from core.domain.contracts import DecisionResult
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.pipeline import offline_scan


def test_offline_scan_iterates_multiple_fake_candidates() -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()

    decisions = offline_scan.evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )

    assert tuple(decision.route_id for decision in decisions) == tuple(route.route_id for route in routes)
    assert decisions[0].status is RouteStatus.PAPER_ELIGIBLE
    assert decisions[0].capture_plan is None
    assert decisions[1].status is RouteStatus.REJECTED
    assert decisions[1].reasons == (RejectReason.MIN_NET_PROFIT_NOT_MET,)
    assert decisions[1].capture_plan is None


def test_missing_observation_fails_closed_before_evaluation(monkeypatch) -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    route = routes[0]
    missing_hedge_observations = {
        key: observation
        for key, observation in observations.items()
        if key != (route.hedge_venue, route.hedge_symbol)
    }

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("evaluate_route must not run after snapshot assembly failure")

    monkeypatch.setattr(offline_scan, "evaluate_route", fail_if_evaluated)

    decisions = offline_scan.evaluate_offline_candidates(
        routes=(route,),
        observations=missing_hedge_observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )

    assert len(decisions) == 1
    assert decisions[0].route_id == route.route_id
    assert decisions[0].status is RouteStatus.REJECTED
    assert decisions[0].reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decisions[0].net_profit_usd is None
    assert decisions[0].entry_ev is None
    assert decisions[0].capture_plan is None
    assert decisions[0].decided_at == assembled_at


def test_offline_scan_uses_one_snapshot_assembly_path_for_each_candidate(monkeypatch) -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    real_assemble_route_snapshot = offline_scan.assemble_route_snapshot
    assembled_route_ids: list[str] = []

    def counting_assemble_route_snapshot(*, route, observations, assembled_at):
        assembled_route_ids.append(route.route_id)
        return real_assemble_route_snapshot(
            route=route,
            observations=observations,
            assembled_at=assembled_at,
        )

    monkeypatch.setattr(offline_scan, "assemble_route_snapshot", counting_assemble_route_snapshot)

    decisions = offline_scan.evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )

    assert assembled_route_ids == [route.route_id for route in routes]
    assert len(decisions) == len(routes)


def test_offline_scan_uses_evaluate_route_as_the_only_route_decision_path(monkeypatch) -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    expected_rules = ProductRules()
    evaluated_route_ids: list[str] = []

    def counting_evaluate_route(route, snapshot, mode, *, rules=None):
        evaluated_route_ids.append(route.route_id)
        assert snapshot.captured_at == assembled_at
        assert mode is EvaluationMode.DISCOVERY
        assert rules is expected_rules
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.RESEARCH_ONLY,
            reasons=(),
            capture_plan=None,
            decided_at=assembled_at,
        )

    monkeypatch.setattr(offline_scan, "evaluate_route", counting_evaluate_route)

    decisions = offline_scan.evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.DISCOVERY,
        rules=expected_rules,
    )

    assert evaluated_route_ids == [route.route_id for route in routes]
    assert tuple(decision.status for decision in decisions) == (
        RouteStatus.RESEARCH_ONLY,
        RouteStatus.RESEARCH_ONLY,
    )
    assert all(decision.capture_plan is None for decision in decisions)


def test_offline_scan_does_not_create_capture_plans_or_live_eligible_results() -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()

    decisions = offline_scan.evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert all(decision.capture_plan is None for decision in decisions)
    assert all(decision.status is not RouteStatus.LIVE_ELIGIBLE for decision in decisions)


def test_offline_scan_does_not_import_execution_or_runner_modules() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.paper_runner")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    scan_module = importlib.reload(importlib.import_module("core.pipeline.offline_scan"))
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()

    scan_module.evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.paper_runner") for module_name in sys.modules)
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
