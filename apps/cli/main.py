"""Minimal CLI entrypoint for deterministic offline research orchestration."""

from __future__ import annotations

from apps.research_runner.fake_data import build_fake_route_candidates_and_observations
from core.domain.enums import EvaluationMode
from core.pipeline.offline_scan import evaluate_offline_candidates


def main() -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    decisions = evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )
    for decision in decisions:
        print(f"{decision.route_id}: {decision.status.value} net_profit_usd={decision.net_profit_usd}")


if __name__ == "__main__":
    main()
