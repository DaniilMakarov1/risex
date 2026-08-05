"""Minimal CLI entrypoint for the RX-000 walking skeleton."""

from __future__ import annotations

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import InMemoryLedger
from core.domain.enums import EvaluationMode
from core.pipeline.evaluate import evaluate_route


def main() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    ledger = InMemoryLedger()
    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY, ledger=ledger)
    print(f"{decision.route_id}: {decision.status.value} net_profit_usd={decision.net_profit_usd}")


if __name__ == "__main__":
    main()
