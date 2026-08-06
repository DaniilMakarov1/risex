"""Fake data for the non-trading walking skeleton."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    RouteCandidate,
    VenueObservation,
    VenueSnapshot,
)
from core.domain.enums import ValueSource
from core.pipeline.snapshot import assemble_route_snapshot


def build_fake_route_and_snapshot() -> tuple[RouteCandidate, VenueSnapshot]:
    """Create a profitable fake route using offline order-book VWAP inputs."""

    target_notional = ProductRules().min_leg_notional_usd
    risex_observed_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    hedge_observed_at = datetime(2026, 1, 1, 12, 0, 1, tzinfo=UTC)
    funding_settlement_at = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
    assembled_at = datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)
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
        risex_venue="RiseX",
        risex_symbol="BTC-PERP",
        risex_entry_side="buy",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        hedge_entry_side="sell",
        target_notional_usd=target_notional,
    )
    risex_observation = VenueObservation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=risex_observed_at,
        order_book=risex_order_book,
        expected_funding_usd=EstimatedValue(
            value=Decimal("3"),
            source=ValueSource.OBSERVED,
            description="fake RiseX funding estimate",
        ),
        funding_settlement_at=funding_settlement_at,
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="fake_risex_entry_and_exit_fees",
                    amount_usd=EstimatedValue(
                        value=Decimal("0.25"),
                        source=ValueSource.DOCUMENTED,
                        description="fake documented RiseX fees",
                    ),
                ),
            )
        ),
    )
    hedge_observation = VenueObservation(
        venue="Hyperliquid",
        symbol="BTC",
        observed_at=hedge_observed_at,
        order_book=hedge_order_book,
        expected_funding_usd=EstimatedValue(
            value=Decimal("-0.5"),
            source=ValueSource.OBSERVED,
            description="fake hedge funding estimate",
        ),
        funding_settlement_at=funding_settlement_at,
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="fake_hedge_entry_and_exit_fees",
                    amount_usd=EstimatedValue(
                        value=Decimal("0.25"),
                        source=ValueSource.DOCUMENTED,
                        description="fake documented hedge fees",
                    ),
                ),
            )
        ),
    )
    snapshot = assemble_route_snapshot(
        route=route,
        observations={
            (risex_observation.venue, risex_observation.symbol): risex_observation,
            (hedge_observation.venue, hedge_observation.symbol): hedge_observation,
        },
        assembled_at=assembled_at,
    )
    return route, snapshot
