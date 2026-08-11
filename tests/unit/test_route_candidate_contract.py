from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.domain.contracts import RouteCandidate
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.pipeline.evaluate import evaluate_route


BASE_ROUTE_VALUES = {
    "route_id": "route-001",
    "capture_id": "capture-001",
    "risex_venue": "RiseX",
    "risex_symbol": "BTC-PERP",
    "risex_entry_side": "buy",
    "hedge_venue": "Hyperliquid",
    "hedge_symbol": "BTC",
    "hedge_entry_side": "sell",
    "target_notional_usd": Decimal("500"),
}


def test_route_candidate_accepts_valid_identity_and_notional_contract() -> None:
    route = RouteCandidate(**BASE_ROUTE_VALUES)

    assert route.route_id == "route-001"
    assert route.capture_id == "capture-001"
    assert route.risex_entry_side == "buy"
    assert route.hedge_entry_side == "sell"
    assert route.target_notional_usd == Decimal("500")


@pytest.mark.parametrize(
    "field_name",
    (
        "route_id",
        "capture_id",
        "risex_venue",
        "risex_symbol",
        "hedge_venue",
        "hedge_symbol",
    ),
)
@pytest.mark.parametrize("malformed_value", ("", "   ", None, 123))
def test_route_candidate_rejects_malformed_identity_fields(
    field_name: str,
    malformed_value: object,
) -> None:
    values = dict(BASE_ROUTE_VALUES)
    values[field_name] = malformed_value

    with pytest.raises(ValueError, match=f"{field_name} must be non-empty"):
        RouteCandidate(**values)


@pytest.mark.parametrize(
    ("risex_entry_side", "hedge_entry_side"),
    (("buy", "buy"), ("sell", "sell")),
)
def test_route_candidate_rejects_non_opposing_entry_sides(
    risex_entry_side: str,
    hedge_entry_side: str,
) -> None:
    values = dict(BASE_ROUTE_VALUES)
    values["risex_entry_side"] = risex_entry_side
    values["hedge_entry_side"] = hedge_entry_side

    with pytest.raises(ValueError, match="entry sides must be opposing"):
        RouteCandidate(**values)


def test_route_candidate_rejects_invalid_entry_side_string() -> None:
    values = dict(BASE_ROUTE_VALUES)
    values["risex_entry_side"] = "hold"

    with pytest.raises(ValueError, match="order side"):
        RouteCandidate(**values)


@pytest.mark.parametrize(
    "target_notional_usd",
    (
        None,
        "500",
        500,
        500.0,
        Decimal("0"),
        Decimal("-1"),
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ),
)
def test_route_candidate_rejects_malformed_target_notional(
    target_notional_usd: object,
) -> None:
    values = dict(BASE_ROUTE_VALUES)
    values["target_notional_usd"] = target_notional_usd

    with pytest.raises(ValueError, match="target_notional_usd"):
        RouteCandidate(**values)


def test_below_minimum_positive_notional_still_fails_through_existing_risk_gate() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_notional_route = replace(route, target_notional_usd=Decimal("499.99"))

    decision = evaluate_route(low_notional_route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.MIN_LEG_NOTIONAL_NOT_MET,)
