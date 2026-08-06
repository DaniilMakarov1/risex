"""Offline research scanning orchestration.

Broad Scan and Focused Refresh intentionally delegate all route decisions to
``evaluate_route()``. This module owns only candidate/watchlist coordination.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol

from core.config.product_rules import ProductRules
from core.domain.contracts import DecisionResult, RouteCandidate, VenueSnapshot
from core.domain.enums import EvaluationMode, RouteStatus
from core.pipeline.evaluate import evaluate_route


@dataclass(frozen=True, slots=True)
class RouteSnapshot:
    """One candidate route paired with one normalized offline snapshot."""

    route: RouteCandidate
    snapshot: VenueSnapshot


@dataclass(frozen=True, slots=True)
class WatchlistCandidate:
    """A route admitted by Broad Scan for later Focused Refresh."""

    route: RouteCandidate
    discovery_decision: DecisionResult


@dataclass(frozen=True, slots=True)
class BroadScanResult:
    """Result of one deterministic Broad Scan pass."""

    decisions: tuple[DecisionResult, ...]
    watchlist: InMemoryWatchlist


@dataclass(frozen=True, slots=True)
class FocusedRefreshResult:
    """Result of refreshing one route from the in-memory watchlist."""

    candidate: WatchlistCandidate
    snapshot: VenueSnapshot
    decision: DecisionResult


class RouteEvaluator(Protocol):
    """Callable contract for the shared route evaluator."""

    def __call__(
        self,
        route: RouteCandidate,
        snapshot: VenueSnapshot,
        mode: EvaluationMode,
        *,
        rules: ProductRules | None = None,
    ) -> DecisionResult:
        ...


SnapshotRefresher = Callable[[RouteCandidate], VenueSnapshot]


class InMemoryWatchlist:
    """Deterministic in-memory watchlist populated only from discovery results."""

    def __init__(self, candidates: Iterable[WatchlistCandidate] = ()) -> None:
        self._candidates: dict[str, WatchlistCandidate] = {}
        for candidate in candidates:
            self.add(candidate)

    def add(self, candidate: WatchlistCandidate) -> None:
        """Record one discovered candidate without creating execution artifacts."""

        decision = candidate.discovery_decision
        route = candidate.route
        if decision.route_id != route.route_id:
            raise ValueError("watchlist decision route_id must match route")
        if decision.mode is not EvaluationMode.DISCOVERY:
            raise ValueError("watchlist candidates must come from DISCOVERY evaluation")
        if decision.status is RouteStatus.REJECTED:
            raise ValueError("rejected routes cannot enter the watchlist")
        if decision.capture_plan is not None:
            raise ValueError("watchlist candidates must not carry capture plans")

        self._candidates[route.route_id] = candidate

    def get(self, route_id: str) -> WatchlistCandidate:
        return self._candidates[route_id]

    def candidates(self) -> tuple[WatchlistCandidate, ...]:
        return tuple(self._candidates.values())

    def route_ids(self) -> tuple[str, ...]:
        return tuple(self._candidates)

    def __iter__(self) -> Iterator[WatchlistCandidate]:
        return iter(self.candidates())

    def __len__(self) -> int:
        return len(self._candidates)


def run_broad_scan(
    route_snapshots: Iterable[RouteSnapshot],
    *,
    rules: ProductRules | None = None,
    watchlist: InMemoryWatchlist | None = None,
    evaluator: RouteEvaluator | None = None,
) -> BroadScanResult:
    """Evaluate fake route snapshots in discovery mode and populate a watchlist."""

    active_rules = rules or ProductRules()
    active_watchlist = watchlist if watchlist is not None else InMemoryWatchlist()
    decisions: list[DecisionResult] = []

    for route_snapshot in route_snapshots:
        decision = _evaluate_with_shared_pipeline(
            route_snapshot.route,
            route_snapshot.snapshot,
            EvaluationMode.DISCOVERY,
            rules=active_rules,
            evaluator=evaluator,
        )
        decisions.append(decision)

        if decision.status is not RouteStatus.REJECTED:
            active_watchlist.add(
                WatchlistCandidate(
                    route=route_snapshot.route,
                    discovery_decision=decision,
                )
            )

    return BroadScanResult(decisions=tuple(decisions), watchlist=active_watchlist)


def run_focused_refresh(
    watchlist: InMemoryWatchlist,
    route_id: str,
    refresh_snapshot: SnapshotRefresher,
    *,
    rules: ProductRules | None = None,
    evaluator: RouteEvaluator | None = None,
) -> FocusedRefreshResult:
    """Refresh a watched route snapshot and evaluate it in entry mode."""

    active_rules = rules or ProductRules()
    candidate = watchlist.get(route_id)
    snapshot = refresh_snapshot(candidate.route)
    decision = _evaluate_with_shared_pipeline(
        candidate.route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=active_rules,
        evaluator=evaluator,
    )
    return FocusedRefreshResult(candidate=candidate, snapshot=snapshot, decision=decision)


def _evaluate_with_shared_pipeline(
    route: RouteCandidate,
    snapshot: VenueSnapshot,
    mode: EvaluationMode,
    *,
    rules: ProductRules,
    evaluator: RouteEvaluator | None,
) -> DecisionResult:
    active_evaluator = evaluator or evaluate_route
    return active_evaluator(route, snapshot, mode, rules=rules)
