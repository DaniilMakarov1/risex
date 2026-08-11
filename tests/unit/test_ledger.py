from datetime import UTC, datetime, timedelta

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from apps.paper_runner.lifecycle import run_paper_lifecycle
from core.accounting.ledger import InMemoryLedger, LedgerEventType, append_decision_event, replay_paper_captures
from core.domain.enums import CaptureState, EvaluationMode
from core.pipeline.evaluate import evaluate_route
from storage.sqlite.ledger import SQLiteLedger


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

    with pytest.raises(TypeError):
        records[0].payload["reasons"] += ("MUTATED",)

    assert ledger.records()[0].payload["status"] == "PAPER_ELIGIBLE"
    assert not hasattr(ledger, "update")
    assert not hasattr(ledger, "delete")


def test_sqlite_ledger_persists_append_only_events(tmp_path) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)
    db_path = tmp_path / "ledger.sqlite"

    ledger = SQLiteLedger(db_path)
    append_decision_event(ledger, decision, recorded_at=snapshot.captured_at)
    ledger.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={"route_id": route.route_id, "reasons": ("test",)},
        recorded_at=snapshot.captured_at,
    )
    ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()

    assert [event.sequence for event in records] == [1, 2]
    assert [event.event_type for event in records] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_REJECTION_RECORDED.value,
    ]
    assert records[0].recorded_at == snapshot.captured_at
    assert records[0].payload["route_id"] == route.route_id
    assert records[1].payload["reasons"] == ("test",)
    assert not hasattr(reopened, "update")
    assert not hasattr(reopened, "delete")
    reopened.close()


def test_sqlite_ledger_continues_append_sequence_after_reopen(tmp_path) -> None:
    db_path = tmp_path / "ledger-reopen-continuity.sqlite"
    recorded_at = datetime(2026, 1, 1, tzinfo=UTC)

    ledger = SQLiteLedger(db_path)
    first = ledger.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={"route_id": "route-a", "reasons": ("first",)},
        recorded_at=recorded_at,
    )
    ledger.close()

    first_reopen = SQLiteLedger(db_path)
    second = first_reopen.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={"route_id": "route-b", "reasons": ("second",)},
        recorded_at=recorded_at + timedelta(seconds=1),
    )
    first_reopen.close()

    second_reopen = SQLiteLedger(db_path)
    third = second_reopen.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload={"route_id": "route-c", "reasons": ("third",)},
        recorded_at=recorded_at + timedelta(seconds=2),
    )
    records = second_reopen.records()

    assert (first.sequence, second.sequence, third.sequence) == (1, 2, 3)
    assert [event.sequence for event in records] == [1, 2, 3]
    assert [event.payload["route_id"] for event in records] == [
        "route-a",
        "route-b",
        "route-c",
    ]
    assert [event.payload["reasons"] for event in records] == [
        ("first",),
        ("second",),
        ("third",),
    ]
    assert not hasattr(second_reopen, "update")
    assert not hasattr(second_reopen, "delete")
    second_reopen.close()


def test_replay_from_sqlite_ledger_events_is_deterministic(tmp_path) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)
    db_path = tmp_path / "paper-ledger.sqlite"
    ledger = SQLiteLedger(db_path)

    run_paper_lifecycle(
        route=route,
        decision=decision,
        funding_settlement_at=snapshot.risex_funding_settlement_at,
        ledger=ledger,
    )
    ledger.close()

    reopened = SQLiteLedger(db_path)
    records = reopened.records()
    replayed_once = replay_paper_captures(records)
    replayed_twice = replay_paper_captures(records)

    assert replayed_once == replayed_twice
    assert len(replayed_once) == 1
    assert replayed_once[0].capture.capture_id == route.capture_id
    assert replayed_once[0].capture.route_id == route.route_id
    assert replayed_once[0].capture.settlement_time == snapshot.risex_funding_settlement_at
    assert replayed_once[0].capture.state is CaptureState.CLOSED
    reopened.close()
