from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    RouteCandidate,
    VenueObservation,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.liquidity import calculate_executable_quote
from core.pipeline.evaluate import evaluate_route
from core.pipeline.snapshot import SnapshotAssemblyInputError, assemble_route_snapshot

RISEX_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
HEDGE_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, 1, tzinfo=UTC)
RISEX_SETTLEMENT_AT = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
HEDGE_SETTLEMENT_AT = datetime(2026, 1, 1, 16, 0, 2, tzinfo=UTC)
ASSEMBLED_AT = datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)


def _route(target_notional_usd: Decimal = Decimal("500")) -> RouteCandidate:
    return RouteCandidate(
        route_id="route-001",
        capture_id="capture-001",
        risex_venue="RiseX",
        risex_symbol="BTC-PERP",
        risex_entry_side="buy",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        hedge_entry_side="sell",
        target_notional_usd=target_notional_usd,
    )


def _book(
    *,
    venue: str,
    symbol: str,
    bid_price: str = "99.95",
    ask_price: str = "100",
    size: str = "10",
) -> OrderBook:
    return OrderBook(
        venue=venue,
        symbol=symbol,
        bids=(OrderBookLevel(price=Decimal(bid_price), size=Decimal(size)),),
        asks=(OrderBookLevel(price=Decimal(ask_price), size=Decimal(size)),),
    )


def _fees(name: str, amount: str = "0.25") -> FeeModel:
    return FeeModel(
        components=(
            FeeComponent(
                name=name,
                amount_usd=EstimatedValue(value=Decimal(amount), source=ValueSource.DOCUMENTED),
            ),
        )
    )


def _observation(
    *,
    venue: str,
    symbol: str,
    observed_at: datetime,
    settlement_at: datetime,
    funding: EstimatedValue,
    fees: FeeModel,
    order_book: OrderBook | None = None,
) -> VenueObservation:
    return VenueObservation(
        venue=venue,
        symbol=symbol,
        observed_at=observed_at,
        order_book=order_book or _book(venue=venue, symbol=symbol),
        expected_funding_usd=funding,
        funding_settlement_at=settlement_at,
        fees=fees,
    )


def _observations() -> tuple[VenueObservation, VenueObservation]:
    risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
        fees=_fees("risex_fees"),
    )
    hedge_observation = _observation(
        venue="Hyperliquid",
        symbol="BTC",
        observed_at=HEDGE_OBSERVED_AT,
        settlement_at=HEDGE_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("-0.5"), source=ValueSource.OBSERVED),
        fees=_fees("hedge_fees"),
    )
    return risex_observation, hedge_observation


def _observation_mapping(
    risex_observation: VenueObservation,
    hedge_observation: VenueObservation,
) -> dict[tuple[str, str], VenueObservation]:
    return {
        (risex_observation.venue, risex_observation.symbol): risex_observation,
        (hedge_observation.venue, hedge_observation.symbol): hedge_observation,
    }


def test_valid_observations_assemble_route_aligned_snapshot_from_vwap_logic() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()

    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.captured_at == ASSEMBLED_AT
    assert snapshot.risex_observed_at == RISEX_OBSERVED_AT
    assert snapshot.hedge_observed_at == HEDGE_OBSERVED_AT
    assert snapshot.risex_funding_settlement_at == RISEX_SETTLEMENT_AT
    assert snapshot.hedge_funding_settlement_at == HEDGE_SETTLEMENT_AT
    assert snapshot.risex_entry_quote == calculate_executable_quote(
        order_book=risex_observation.order_book,
        side=route.risex_entry_side,
        target_notional_usd=route.target_notional_usd,
    )
    assert snapshot.hedge_entry_quote == calculate_executable_quote(
        order_book=hedge_observation.order_book,
        side=route.hedge_entry_side,
        target_notional_usd=route.target_notional_usd,
    )
    assert snapshot.risex_estimated_exit_quote == calculate_executable_quote(
        order_book=risex_observation.order_book,
        side="sell",
        target_notional_usd=route.target_notional_usd,
    )
    assert snapshot.hedge_estimated_exit_quote == calculate_executable_quote(
        order_book=hedge_observation.order_book,
        side="buy",
        target_notional_usd=route.target_notional_usd,
    )
    assert tuple(quote.target_notional_usd for quote in snapshot.executable_quotes()) == (
        route.target_notional_usd,
        route.target_notional_usd,
        route.target_notional_usd,
        route.target_notional_usd,
    )
    assert snapshot.risex_estimated_exit_quote.side != snapshot.risex_entry_quote.side
    assert snapshot.hedge_estimated_exit_quote.side != snapshot.hedge_entry_quote.side
    assert snapshot.funding.risex_funding_usd == risex_observation.expected_funding_usd
    assert snapshot.funding.hedge_funding_usd == hedge_observation.expected_funding_usd
    assert snapshot.fees.components == (
        *risex_observation.fees.components,
        *hedge_observation.fees.components,
    )


def test_missing_risex_observation_fails_explicitly() -> None:
    route = _route()
    _, hedge_observation = _observations()

    with pytest.raises(SnapshotAssemblyInputError, match="missing RiseX observation"):
        assemble_route_snapshot(
            route=route,
            observations={(hedge_observation.venue, hedge_observation.symbol): hedge_observation},
            assembled_at=ASSEMBLED_AT,
        )


def test_missing_hedge_observation_fails_explicitly() -> None:
    route = _route()
    risex_observation, _ = _observations()

    with pytest.raises(SnapshotAssemblyInputError, match="missing hedge observation"):
        assemble_route_snapshot(
            route=route,
            observations={(risex_observation.venue, risex_observation.symbol): risex_observation},
            assembled_at=ASSEMBLED_AT,
        )


def test_wrong_observation_venue_fails() -> None:
    route = _route()
    _, hedge_observation = _observations()
    wrong_risex_observation = _observation(
        venue="OtherRiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
        fees=_fees("wrong_risex_fees"),
        order_book=_book(venue="OtherRiseX", symbol="BTC-PERP"),
    )

    with pytest.raises(SnapshotAssemblyInputError, match="RiseX observation venue"):
        assemble_route_snapshot(
            route=route,
            observations={
                (route.risex_venue, route.risex_symbol): wrong_risex_observation,
                (hedge_observation.venue, hedge_observation.symbol): hedge_observation,
            },
            assembled_at=ASSEMBLED_AT,
        )


def test_wrong_observation_symbol_fails() -> None:
    route = _route()
    risex_observation, _ = _observations()
    wrong_hedge_observation = _observation(
        venue="Hyperliquid",
        symbol="ETH",
        observed_at=HEDGE_OBSERVED_AT,
        settlement_at=HEDGE_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("-0.5"), source=ValueSource.OBSERVED),
        fees=_fees("wrong_hedge_fees"),
        order_book=_book(venue="Hyperliquid", symbol="ETH"),
    )

    with pytest.raises(SnapshotAssemblyInputError, match="hedge observation symbol"):
        assemble_route_snapshot(
            route=route,
            observations={
                (risex_observation.venue, risex_observation.symbol): risex_observation,
                (route.hedge_venue, route.hedge_symbol): wrong_hedge_observation,
            },
            assembled_at=ASSEMBLED_AT,
        )


def test_observation_rejects_embedded_order_book_metadata_mismatch() -> None:
    with pytest.raises(ValueError, match="order book venue"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=_fees("risex_fees"),
            order_book=_book(venue="OtherRiseX", symbol="BTC-PERP"),
        )


def test_observation_rejects_naive_timestamps() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=datetime(2026, 1, 1, 12, 0),
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=_fees("risex_fees"),
        )


def test_assembly_rejects_naive_assembly_timestamp() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()

    with pytest.raises(ValueError, match="assembled_at"):
        assemble_route_snapshot(
            route=route,
            observations=_observation_mapping(risex_observation, hedge_observation),
            assembled_at=datetime(2026, 1, 1, 12, 0),
        )


def test_unknown_funding_survives_assembly_and_cannot_become_live_eligible() -> None:
    route = _route()
    _, hedge_observation = _observations()
    unknown_risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
        fees=_fees("risex_fees"),
    )
    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(unknown_risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.funding.risex_funding_usd.source is ValueSource.UNKNOWN
    assert snapshot.funding.risex_funding_usd.value is None

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert decision.status is RouteStatus.REJECTED
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)


def test_empty_observation_fee_input_is_rejected_before_snapshot_assembly() -> None:
    with pytest.raises(ValueError, match="source-aware fee"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=FeeModel(components=()),
        )


def test_poor_but_fully_executable_prices_affect_pnl_without_artificial_reject() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    baseline_snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )
    poor_risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("100"), source=ValueSource.OBSERVED),
        fees=_fees("risex_fees"),
        order_book=_book(venue="RiseX", symbol="BTC-PERP", bid_price="90", ask_price="100"),
    )
    poor_snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(poor_risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    baseline_decision = evaluate_route(route, baseline_snapshot, EvaluationMode.ENTRY)
    poor_decision = evaluate_route(route, poor_snapshot, EvaluationMode.ENTRY)

    assert baseline_decision.entry_ev is not None
    assert poor_decision.entry_ev is not None
    assert poor_decision.status is RouteStatus.PAPER_ELIGIBLE
    assert poor_decision.entry_ev.simulated_roundtrip_cost_usd > (
        baseline_decision.entry_ev.simulated_roundtrip_cost_usd
    )
    assert RejectReason.TECHNICALLY_NOT_EXECUTABLE not in poor_decision.reasons
    assert RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL not in poor_decision.reasons
