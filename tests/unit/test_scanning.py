from __future__ import annotations

import importlib
import sys
from dataclasses import replace
from decimal import Decimal

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from apps.research_runner.scanning import (
    InMemoryWatchlist,
    RouteSnapshot,
    WatchlistCandidate,
    run_broad_scan,
    run_focused_refresh,
)
from core.domain.contracts import (
    DecisionResult,
    EstimatedValue,
    FundingSnapshot,
    OrderBook,
    OrderBookLevel,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.liquidity import calculate_executable_quote


def test_broad_scan_calls_evaluate_route_with_discovery_mode() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    calls: list[tuple[RouteCandidate, VenueSnapshot, EvaluationMode]] = []

    def spy_evaluator(
        route: RouteCandidate,
        snapshot: VenueSnapshot,
        mode: EvaluationMode,
        *,
        rules=None,
    ) -> DecisionResult:
        calls.append((route, snapshot, mode))
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.PAPER_ELIGIBLE,
            reasons=(),
        )

    result = run_broad_scan(
        (RouteSnapshot(route=route, snapshot=snapshot),),
        evaluator=spy_evaluator,
    )

    assert calls == [(route, snapshot, EvaluationMode.DISCOVERY)]
    assert result.decisions[0].mode is EvaluationMode.DISCOVERY
    assert result.watchlist.route_ids() == (route.route_id,)


def test_focused_refresh_calls_evaluate_route_with_entry_mode() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    discovery = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.DISCOVERY,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=(),
    )
    watchlist = InMemoryWatchlist((WatchlistCandidate(route=route, discovery_decision=discovery),))
    calls: list[tuple[RouteCandidate, VenueSnapshot, EvaluationMode]] = []

    def spy_evaluator(
        route: RouteCandidate,
        snapshot: VenueSnapshot,
        mode: EvaluationMode,
        *,
        rules=None,
    ) -> DecisionResult:
        calls.append((route, snapshot, mode))
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.PAPER_ELIGIBLE,
            reasons=(),
        )

    result = run_focused_refresh(
        watchlist,
        route.route_id,
        lambda watched_route: snapshot,
        evaluator=spy_evaluator,
    )

    assert calls == [(route, snapshot, EvaluationMode.ENTRY)]
    assert result.candidate.route == route
    assert result.snapshot == snapshot
    assert result.decision.mode is EvaluationMode.ENTRY


def test_broad_scan_records_watchlist_candidates_without_capture_plans() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    result = run_broad_scan((RouteSnapshot(route=route, snapshot=snapshot),))

    assert len(result.decisions) == 1
    assert result.decisions[0].status is RouteStatus.PAPER_ELIGIBLE
    assert result.decisions[0].capture_plan is None
    assert result.watchlist.route_ids() == (route.route_id,)
    assert result.watchlist.get(route.route_id).discovery_decision.capture_plan is None


def test_focused_refresh_uses_same_snapshot_economics_as_discovery() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    scan_result = run_broad_scan((RouteSnapshot(route=route, snapshot=snapshot),))

    refresh_result = run_focused_refresh(
        scan_result.watchlist,
        route.route_id,
        lambda watched_route: snapshot,
    )

    discovery_decision = scan_result.decisions[0]
    entry_decision = refresh_result.decision

    assert discovery_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert entry_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert discovery_decision.net_profit_usd == entry_decision.net_profit_usd
    assert discovery_decision.entry_ev == entry_decision.entry_ev
    assert discovery_decision.mode is EvaluationMode.DISCOVERY
    assert entry_decision.mode is EvaluationMode.ENTRY


def test_rejected_routes_do_not_enter_watchlist() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_notional_route = replace(
        route,
        route_id="fake-low-notional",
        capture_id="capture-low-notional",
        target_notional_usd=Decimal("499.99"),
    )
    low_profit_route = replace(route, route_id="fake-low-profit", capture_id="capture-low-profit")
    low_profit_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=Decimal("0.1"), source=ValueSource.OBSERVED),
            hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
        ),
    )
    shallow_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(),
        asks=(OrderBookLevel(price=Decimal("100"), size=Decimal("4")),),
    )
    bad_orderbook_route = replace(route, route_id="fake-bad-orderbook", capture_id="capture-bad-orderbook")
    bad_orderbook_snapshot = replace(
        snapshot,
        risex_entry_quote=calculate_executable_quote(
            order_book=shallow_book,
            side="buy",
            target_notional_usd=Decimal("500"),
        ),
    )

    result = run_broad_scan(
        (
            RouteSnapshot(route=low_notional_route, snapshot=snapshot),
            RouteSnapshot(route=low_profit_route, snapshot=low_profit_snapshot),
            RouteSnapshot(route=bad_orderbook_route, snapshot=bad_orderbook_snapshot),
        )
    )

    assert result.watchlist.route_ids() == ()
    assert [decision.status for decision in result.decisions] == [
        RouteStatus.REJECTED,
        RouteStatus.REJECTED,
        RouteStatus.REJECTED,
    ]
    assert [decision.reasons for decision in result.decisions] == [
        (RejectReason.MIN_LEG_NOTIONAL_NOT_MET,),
        (RejectReason.MIN_NET_PROFIT_NOT_MET,),
        (RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL,),
    ]


def test_watchlist_rejects_non_discovery_or_rejected_decisions() -> None:
    route, _snapshot = build_fake_route_and_snapshot()
    watchlist = InMemoryWatchlist()

    entry_decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.ENTRY,
        status=RouteStatus.PAPER_ELIGIBLE,
        reasons=(),
    )
    rejected_decision = DecisionResult(
        route_id=route.route_id,
        mode=EvaluationMode.DISCOVERY,
        status=RouteStatus.REJECTED,
        reasons=(RejectReason.MIN_NET_PROFIT_NOT_MET,),
    )

    for decision in (entry_decision, rejected_decision):
        try:
            watchlist.add(WatchlistCandidate(route=route, discovery_decision=decision))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid watchlist candidate was accepted")

    assert len(watchlist) == 0


def test_scanning_does_not_import_execution_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "core.execution" or module_name.startswith("core.execution."):
            del sys.modules[module_name]

    scanning_module = importlib.import_module("apps.research_runner.scanning")
    scanning_module = importlib.reload(scanning_module)
    route, snapshot = build_fake_route_and_snapshot()

    result = scanning_module.run_broad_scan(
        (scanning_module.RouteSnapshot(route=route, snapshot=snapshot),)
    )

    assert result.watchlist.route_ids() == (route.route_id,)
    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
