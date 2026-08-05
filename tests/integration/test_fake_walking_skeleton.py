from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import InMemoryLedger
from core.domain.enums import EvaluationMode, RouteStatus
from core.pipeline.evaluate import evaluate_route


def test_fake_walking_skeleton_evaluates_without_exchange_api() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    ledger = InMemoryLedger()

    decision = evaluate_route(route, snapshot, EvaluationMode.DISCOVERY, ledger=ledger)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.capture_plan is None
    assert len(ledger.records()) == 1
