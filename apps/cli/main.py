"""Minimal CLI entrypoint for deterministic offline scan/refresh orchestration."""

from __future__ import annotations

from apps.research_runner.fake_data import (
    build_fake_focused_refresh_observations,
    build_fake_route_candidates_and_observations,
)
from core.domain.contracts import DecisionResult
from core.pipeline.scan_refresh import run_broad_scan, run_focused_refresh


def _print_decisions(label: str, decisions: tuple[DecisionResult, ...]) -> None:
    print(label)
    for decision in decisions:
        print(f"{decision.route_id}: {decision.status.value} net_profit_usd={decision.net_profit_usd}")


def main() -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    broad_scan = run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=assembled_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    focused_refresh = run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
    )

    _print_decisions("Broad Scan", broad_scan.decisions)
    _print_decisions("Focused Refresh", focused_refresh.decisions)


if __name__ == "__main__":
    main()
