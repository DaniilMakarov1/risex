import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import InMemoryLedger
from core.domain.enums import EvaluationMode
from core.pipeline.evaluate import evaluate_route


def test_ledger_records_decision_events_append_only() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    ledger = InMemoryLedger()

    evaluate_route(route, snapshot, EvaluationMode.DISCOVERY, ledger=ledger)
    evaluate_route(route, snapshot, EvaluationMode.ENTRY, ledger=ledger)

    records = ledger.records()
    assert len(records) == 2
    assert [event.sequence for event in records] == [1, 2]
    assert [event.event_type for event in records] == ["route_decision", "route_decision"]

    with pytest.raises(TypeError):
        records[0].payload["status"] = "REJECTED"

    assert ledger.records()[0].payload["status"] == "PAPER_ELIGIBLE"
