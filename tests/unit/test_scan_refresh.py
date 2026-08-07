from __future__ import annotations

import importlib
import inspect
import sys

from apps.research_runner.fake_data import (
    build_fake_focused_refresh_observations,
    build_fake_route_candidates_and_observations,
)
from core.config.product_rules import ProductRules
from core.domain.contracts import DecisionResult
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.pipeline import offline_scan, scan_refresh


def test_broad_scan_iterates_fake_candidates_through_snapshot_and_evaluation_path(
    monkeypatch,
) -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    real_assemble_route_snapshot = offline_scan.assemble_route_snapshot
    assembled_route_ids: list[str] = []
    evaluated_route_ids: list[str] = []

    def counting_assemble_route_snapshot(*, route, observations, assembled_at):
        assembled_route_ids.append(route.route_id)
        return real_assemble_route_snapshot(
            route=route,
            observations=observations,
            assembled_at=assembled_at,
        )

    def counting_evaluate_route(route, snapshot, mode, *, rules=None):
        evaluated_route_ids.append(route.route_id)
        assert snapshot.captured_at == scanned_at
        assert mode is EvaluationMode.DISCOVERY
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.RESEARCH_ONLY,
            reasons=(),
            capture_plan=None,
            decided_at=scanned_at,
        )

    monkeypatch.setattr(offline_scan, "assemble_route_snapshot", counting_assemble_route_snapshot)
    monkeypatch.setattr(offline_scan, "evaluate_route", counting_evaluate_route)

    result = scan_refresh.run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
    )

    assert assembled_route_ids == [route.route_id for route in routes]
    assert evaluated_route_ids == [route.route_id for route in routes]
    assert result.refresh_candidates == routes
    assert all(decision.capture_plan is None for decision in result.decisions)


def test_broad_scan_does_not_create_capture_plans_or_live_eligible_results() -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()

    result = scan_refresh.run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert all(decision.mode is EvaluationMode.DISCOVERY for decision in result.decisions)
    assert all(decision.capture_plan is None for decision in result.decisions)
    assert all(decision.status is not RouteStatus.LIVE_ELIGIBLE for decision in result.decisions)


def test_focused_refresh_consumes_only_broad_scan_handoff_candidates() -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    broad_scan = scan_refresh.run_broad_scan(
        routes=routes[:1],
        observations=observations,
        scanned_at=scanned_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()

    focused = scan_refresh.run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
    )

    assert tuple(decision.route_id for decision in focused.decisions) == (routes[0].route_id,)
    assert "routes" not in inspect.signature(scan_refresh.run_focused_refresh).parameters


def test_focused_refresh_uses_refreshed_observations_and_entry_mode(monkeypatch) -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    broad_scan = scan_refresh.run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    real_assemble_route_snapshot = offline_scan.assemble_route_snapshot
    observed_capture_times = []
    evaluated_modes = []

    def counting_assemble_route_snapshot(*, route, observations, assembled_at):
        snapshot = real_assemble_route_snapshot(
            route=route,
            observations=observations,
            assembled_at=assembled_at,
        )
        observed_capture_times.append(
            (
                snapshot.captured_at,
                snapshot.risex_observed_at,
                snapshot.hedge_observed_at,
            )
        )
        return snapshot

    def counting_evaluate_route(route, snapshot, mode, *, rules=None):
        evaluated_modes.append(mode)
        assert snapshot.captured_at == refreshed_at
        assert snapshot.risex_observed_at > scanned_at
        assert snapshot.hedge_observed_at > scanned_at
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.PAPER_ELIGIBLE,
            reasons=(),
            capture_plan=None,
            decided_at=refreshed_at,
        )

    monkeypatch.setattr(offline_scan, "assemble_route_snapshot", counting_assemble_route_snapshot)
    monkeypatch.setattr(offline_scan, "evaluate_route", counting_evaluate_route)

    focused = scan_refresh.run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
    )

    assert len(observed_capture_times) == len(routes)
    assert evaluated_modes == [EvaluationMode.ENTRY, EvaluationMode.ENTRY]
    assert all(decision.capture_plan is None for decision in focused.decisions)


def test_broad_scan_and_focused_refresh_have_no_separate_business_rules(monkeypatch) -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    expected_rules = ProductRules()
    calls = []

    def fake_evaluate_offline_candidates(*, routes, observations, assembled_at, mode, rules=None):
        route_tuple = tuple(routes)
        calls.append(
            {
                "route_ids": tuple(route.route_id for route in route_tuple),
                "observations": observations,
                "assembled_at": assembled_at,
                "mode": mode,
                "rules": rules,
            }
        )
        return tuple(
            DecisionResult(
                route_id=route.route_id,
                mode=mode,
                status=RouteStatus.RESEARCH_ONLY,
                reasons=(),
                capture_plan=None,
                decided_at=assembled_at,
            )
            for route in route_tuple
        )

    monkeypatch.setattr(
        scan_refresh,
        "evaluate_offline_candidates",
        fake_evaluate_offline_candidates,
    )

    broad_scan = scan_refresh.run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
        rules=expected_rules,
    )
    scan_refresh.run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
        rules=expected_rules,
    )

    assert calls == [
        {
            "route_ids": tuple(route.route_id for route in routes),
            "observations": observations,
            "assembled_at": scanned_at,
            "mode": EvaluationMode.DISCOVERY,
            "rules": expected_rules,
        },
        {
            "route_ids": tuple(route.route_id for route in routes),
            "observations": refreshed_observations,
            "assembled_at": refreshed_at,
            "mode": EvaluationMode.ENTRY,
            "rules": expected_rules,
        },
    ]


def test_broad_scan_missing_observations_fail_closed_without_evaluation(monkeypatch) -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    route = routes[0]
    missing_hedge_observations = {
        key: observation
        for key, observation in observations.items()
        if key != (route.hedge_venue, route.hedge_symbol)
    }

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("evaluate_route must not run after snapshot assembly failure")

    monkeypatch.setattr(offline_scan, "evaluate_route", fail_if_evaluated)

    result = scan_refresh.run_broad_scan(
        routes=(route,),
        observations=missing_hedge_observations,
        scanned_at=scanned_at,
    )

    assert len(result.decisions) == 1
    assert result.decisions[0].status is RouteStatus.REJECTED
    assert result.decisions[0].reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert result.decisions[0].capture_plan is None


def test_focused_refresh_missing_observations_fail_closed_without_evaluation(monkeypatch) -> None:
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()
    route = routes[0]
    broad_scan = scan_refresh.run_broad_scan(
        routes=(route,),
        observations=observations,
        scanned_at=scanned_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    missing_hedge_observations = {
        key: observation
        for key, observation in refreshed_observations.items()
        if key != (route.hedge_venue, route.hedge_symbol)
    }

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("evaluate_route must not run after snapshot assembly failure")

    monkeypatch.setattr(offline_scan, "evaluate_route", fail_if_evaluated)

    result = scan_refresh.run_focused_refresh(
        broad_scan=broad_scan,
        observations=missing_hedge_observations,
        refreshed_at=refreshed_at,
    )

    assert len(result.decisions) == 1
    assert result.decisions[0].status is RouteStatus.REJECTED
    assert result.decisions[0].reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert result.decisions[0].capture_plan is None


def test_scan_refresh_does_not_import_execution_or_runner_modules() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.paper_runner")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    scan_refresh_module = importlib.reload(importlib.import_module("core.pipeline.scan_refresh"))
    routes, observations, scanned_at = build_fake_route_candidates_and_observations()

    broad_scan = scan_refresh_module.run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=scanned_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    scan_refresh_module.run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
    )

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.paper_runner") for module_name in sys.modules)
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
