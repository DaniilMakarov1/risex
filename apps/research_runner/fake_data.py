"""Fake data for the non-trading walking skeleton."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    FundingSnapshot,
    OrderBook,
    OrderBookLevel,
    RouteCandidate,
    VenueSnapshot,
)
from core.domain.enums import ValueSource
from core.economics.liquidity import calculate_executable_quote


def build_fake_route_and_snapshot() -> tuple[RouteCandidate, VenueSnapshot]:
    """Create a profitable fake route using offline order-book VWAP inputs."""

    target_notional = ProductRules().min_leg_notional_usd
    risex_order_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(OrderBookLevel(price=Decimal("99.95"), size=Decimal("10")),),
        asks=(OrderBookLevel(price=Decimal("100"), size=Decimal("10")),),
    )
    hedge_order_book = OrderBook(
        venue="Hyperliquid",
        symbol="BTC",
        bids=(OrderBookLevel(price=Decimal("100"), size=Decimal("10")),),
        asks=(OrderBookLevel(price=Decimal("100.05"), size=Decimal("10")),),
    )
    route = RouteCandidate(
        route_id="fake-risex-hl-btc",
        capture_id="capture-000",
        risex_symbol="BTC-PERP",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        target_notional_usd=target_notional,
    )
    snapshot = VenueSnapshot(
        captured_at=datetime.now(UTC),
        risex_entry_quote=calculate_executable_quote(
            order_book=risex_order_book,
            side="buy",
            target_notional_usd=target_notional,
        ),
        hedge_entry_quote=calculate_executable_quote(
            order_book=hedge_order_book,
            side="sell",
            target_notional_usd=target_notional,
        ),
        risex_estimated_exit_quote=calculate_executable_quote(
            order_book=risex_order_book,
            side="sell",
            target_notional_usd=target_notional,
        ),
        hedge_estimated_exit_quote=calculate_executable_quote(
            order_book=hedge_order_book,
            side="buy",
            target_notional_usd=target_notional,
        ),
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(
                value=Decimal("3"),
                source=ValueSource.OBSERVED,
                description="fake RiseX funding estimate",
            ),
            hedge_funding_usd=EstimatedValue(
                value=Decimal("-0.5"),
                source=ValueSource.OBSERVED,
                description="fake hedge funding estimate",
            ),
        ),
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="fake_entry_and_exit_fees",
                    amount_usd=EstimatedValue(
                        value=Decimal("0.5"),
                        source=ValueSource.DOCUMENTED,
                        description="fake documented total fees",
                    ),
                ),
            )
        ),
    )
    return route, snapshot
