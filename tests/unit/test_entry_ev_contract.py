from dataclasses import fields, replace
from decimal import Decimal

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.domain.contracts import EstimatedValue, FundingSnapshot, OrderBook, OrderBookLevel
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError
from core.economics.ev import EntryEV
from core.economics.ev import calculate_entry_ev
from core.economics.liquidity import calculate_executable_quote


def test_entry_ev_does_not_require_expected_basis_change() -> None:
    assert "expected_basis_change" not in {field.name for field in fields(EntryEV)}


def test_entry_ev_uses_source_aware_funding_fees_and_roundtrip_cost() -> None:
    _, snapshot = build_fake_route_and_snapshot()

    entry_ev = calculate_entry_ev(snapshot)

    assert entry_ev.expected_funding_usd == Decimal("2.5")
    assert entry_ev.total_fees_usd == Decimal("0.5")
    assert entry_ev.simulated_roundtrip_cost_usd == Decimal("0.50")
    assert entry_ev.net_profit_usd == Decimal("1.50")


def test_poor_executable_exit_price_reduces_entry_ev_net_profit() -> None:
    _, snapshot = build_fake_route_and_snapshot()
    poor_exit_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(OrderBookLevel(price=Decimal("90"), size=Decimal("10")),),
        asks=(),
    )
    poor_snapshot = snapshot.__class__(
        captured_at=snapshot.captured_at,
        risex_entry_quote=snapshot.risex_entry_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_estimated_exit_quote=calculate_executable_quote(
            order_book=poor_exit_book,
            side="sell",
            target_notional_usd=Decimal("500"),
        ),
        hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
        funding=snapshot.funding,
        fees=snapshot.fees,
    )

    assert calculate_entry_ev(poor_snapshot).net_profit_usd < calculate_entry_ev(snapshot).net_profit_usd


def test_missing_funding_estimate_cannot_produce_numeric_entry_ev() -> None:
    _, snapshot = build_fake_route_and_snapshot()
    missing_funding_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
            hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        ),
    )

    with pytest.raises(EconomicsInputError, match="UNKNOWN"):
        calculate_entry_ev(missing_funding_snapshot)
