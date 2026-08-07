"""Fake data for deterministic non-trading research runs."""

from __future__ import annotations

from dataclasses import replace
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


ObservationMap = dict[tuple[str, str], VenueObservation]


def _book(
    *,
    venue: str,
    symbol: str,
    bid_price: str,
    ask_price: str,
    size: str,
) -> OrderBook:
    return OrderBook(
        venue=venue,
        symbol=symbol,
        bids=(OrderBookLevel(price=Decimal(bid_price), size=Decimal(size)),),
        asks=(OrderBookLevel(price=Decimal(ask_price), size=Decimal(size)),),
    )


def _fees(*, name: str, amount: str, description: str) -> FeeModel:
    return FeeModel(
        components=(
            FeeComponent(
                name=name,
                amount_usd=EstimatedValue(
                    value=Decimal(amount),
                    source=ValueSource.DOCUMENTED,
                    description=description,
                ),
            ),
        )
    )


def _observed_funding(*, amount: str, description: str) -> EstimatedValue:
    return EstimatedValue(
        value=Decimal(amount),
        source=ValueSource.OBSERVED,
        description=description,
    )


def _observation(
    *,
    venue: str,
    symbol: str,
    observed_at: datetime,
    order_book: OrderBook,
    expected_funding_usd: EstimatedValue,
    funding_settlement_at: datetime,
    fees: FeeModel,
) -> VenueObservation:
    return VenueObservation(
        venue=venue,
        symbol=symbol,
        observed_at=observed_at,
        order_book=order_book,
        expected_funding_usd=expected_funding_usd,
        funding_settlement_at=funding_settlement_at,
        fees=fees,
    )


def _observation_mapping(observations: tuple[VenueObservation, ...]) -> ObservationMap:
    return {(observation.venue, observation.symbol): observation for observation in observations}


def build_fake_route_candidates_and_observations() -> tuple[
    tuple[RouteCandidate, ...],
    ObservationMap,
    datetime,
]:
    """Create fake route candidates and normalized observations for offline orchestration."""

    target_notional = ProductRules().min_leg_notional_usd
    risex_observed_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    hedge_observed_at = datetime(2026, 1, 1, 12, 0, 1, tzinfo=UTC)
    funding_settlement_at = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
    assembled_at = datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)

    btc_route = RouteCandidate(
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
    eth_route = RouteCandidate(
        route_id="fake-risex-hl-eth",
        capture_id="capture-001",
        risex_venue="RiseX",
        risex_symbol="ETH-PERP",
        risex_entry_side="sell",
        hedge_venue="Hyperliquid",
        hedge_symbol="ETH",
        hedge_entry_side="buy",
        target_notional_usd=Decimal("600"),
    )

    observations = _observation_mapping(
        (
            _observation(
                venue="RiseX",
                symbol="BTC-PERP",
                observed_at=risex_observed_at,
                order_book=_book(
                    venue="RiseX",
                    symbol="BTC-PERP",
                    bid_price="99.95",
                    ask_price="100",
                    size="10",
                ),
                expected_funding_usd=_observed_funding(
                    amount="3",
                    description="fake RiseX BTC funding estimate",
                ),
                funding_settlement_at=funding_settlement_at,
                fees=_fees(
                    name="fake_risex_btc_entry_and_exit_fees",
                    amount="0.25",
                    description="fake documented RiseX BTC fees",
                ),
            ),
            _observation(
                venue="Hyperliquid",
                symbol="BTC",
                observed_at=hedge_observed_at,
                order_book=_book(
                    venue="Hyperliquid",
                    symbol="BTC",
                    bid_price="100",
                    ask_price="100.05",
                    size="10",
                ),
                expected_funding_usd=_observed_funding(
                    amount="-0.5",
                    description="fake Hyperliquid BTC funding estimate",
                ),
                funding_settlement_at=funding_settlement_at,
                fees=_fees(
                    name="fake_hyperliquid_btc_entry_and_exit_fees",
                    amount="0.25",
                    description="fake documented Hyperliquid BTC fees",
                ),
            ),
            _observation(
                venue="RiseX",
                symbol="ETH-PERP",
                observed_at=risex_observed_at,
                order_book=_book(
                    venue="RiseX",
                    symbol="ETH-PERP",
                    bid_price="2000",
                    ask_price="2001",
                    size="1",
                ),
                expected_funding_usd=_observed_funding(
                    amount="1",
                    description="fake RiseX ETH funding estimate",
                ),
                funding_settlement_at=funding_settlement_at,
                fees=_fees(
                    name="fake_risex_eth_entry_and_exit_fees",
                    amount="0.30",
                    description="fake documented RiseX ETH fees",
                ),
            ),
            _observation(
                venue="Hyperliquid",
                symbol="ETH",
                observed_at=hedge_observed_at,
                order_book=_book(
                    venue="Hyperliquid",
                    symbol="ETH",
                    bid_price="2000",
                    ask_price="2000.5",
                    size="1",
                ),
                expected_funding_usd=_observed_funding(
                    amount="-0.2",
                    description="fake Hyperliquid ETH funding estimate",
                ),
                funding_settlement_at=funding_settlement_at,
                fees=_fees(
                    name="fake_hyperliquid_eth_entry_and_exit_fees",
                    amount="0.30",
                    description="fake documented Hyperliquid ETH fees",
                ),
            ),
        )
    )

    return (btc_route, eth_route), observations, assembled_at


def build_fake_focused_refresh_observations() -> tuple[ObservationMap, datetime]:
    """Create refreshed fake observations for the second offline scan stage."""

    _, observations, _ = build_fake_route_candidates_and_observations()
    refreshed_at = datetime(2026, 1, 1, 12, 1, 5, tzinfo=UTC)
    risex_refreshed_at = datetime(2026, 1, 1, 12, 1, tzinfo=UTC)
    hedge_refreshed_at = datetime(2026, 1, 1, 12, 1, 1, tzinfo=UTC)

    refreshed_observations = {
        key: replace(
            observation,
            observed_at=risex_refreshed_at
            if observation.venue == "RiseX"
            else hedge_refreshed_at,
        )
        for key, observation in observations.items()
    }

    return refreshed_observations, refreshed_at


def build_fake_route_and_snapshot() -> tuple[RouteCandidate, VenueSnapshot]:
    """Create the first profitable fake route using offline order-book VWAP inputs."""

    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    route = routes[0]
    snapshot = assemble_route_snapshot(
        route=route,
        observations=observations,
        assembled_at=assembled_at,
    )
    return route, snapshot
