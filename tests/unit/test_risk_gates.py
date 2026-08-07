from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.domain.contracts import CapturePlanFreshnessEvidence
from core.domain.enums import RejectReason, ValueSource
from core.risk.gates import check_capture_plan_freshness_gate


def _fresh_evidence(**changes) -> CapturePlanFreshnessEvidence:
    route, snapshot = build_fake_route_and_snapshot()
    values = {
        "plan_id": "fake-plan-001",
        "plan_version": "fake-v1",
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "planned_at": snapshot.captured_at,
        "valid_until": snapshot.captured_at + timedelta(minutes=5),
        "source": ValueSource.OBSERVED,
        "ledger_reconciliation_event_sequence": 11,
    }
    values.update(changes)
    return CapturePlanFreshnessEvidence(**values)


def test_missing_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=None,
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_stale_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(
        valid_until=snapshot.captured_at + timedelta(seconds=1),
    )

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at + timedelta(seconds=1),
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_duplicated_capture_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence, evidence),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


@pytest.mark.parametrize(
    "changes",
    (
        {"capture_id": "other-capture"},
        {"route_id": "other-route"},
    ),
)
def test_cross_capture_or_route_plan_freshness_evidence_fails_closed(
    changes: dict[str, str],
) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(**changes)

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_cross_settlement_plan_freshness_evidence_fails_closed() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence(
        settlement_time=snapshot.risex_funding_settlement_at + timedelta(hours=8),
    )

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is False
    assert reason is RejectReason.CAPTURE_PLAN_NOT_FRESH


def test_fresh_capture_plan_evidence_for_exact_capture_route_and_settlement_passes() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evidence = _fresh_evidence()

    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=snapshot.risex_funding_settlement_at,
        evaluated_at=snapshot.captured_at,
        plan_evidence=(evidence,),
    )

    assert ok is True
    assert reason is None


def test_naive_capture_plan_freshness_timestamp_is_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="planned_at must be timezone-aware"):
        _fresh_evidence(planned_at=datetime(2026, 1, 1, 12, 0))
