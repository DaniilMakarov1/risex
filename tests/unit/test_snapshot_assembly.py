from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import get_type_hints

import pytest

import core.pipeline.snapshot as snapshot_module
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
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.liquidity import calculate_executable_quote
from core.pipeline.evaluate import evaluate_route
from core.pipeline.snapshot import (
    SnapshotAssemblyInputError,
    assemble_route_snapshot,
    assemble_route_snapshot_from_adapters,
)
from core.venues.base import VenueAdapter

RISEX_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
HEDGE_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, 1, tzinfo=UTC)
RISEX_SETTLEMENT_AT = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
HEDGE_SETTLEMENT_AT = RISEX_SETTLEMENT_AT
MISMATCHED_HEDGE_SETTLEMENT_AT = datetime(2026, 1, 1, 16, 0, 2, tzinfo=UTC)
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


def _public_rate_funding(rate: str) -> EstimatedValue:
    return EstimatedValue(
        value=None,
        source=ValueSource.UNKNOWN,
        metadata={
            "public_funding_rate": rate,
            "public_funding_rate_source": "OBSERVED",
        },
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


class RecordingObservationAdapter:
    name = "recording"

    def __init__(self, observation: VenueObservation) -> None:
        self.observation = observation
        self.requested_symbols: list[str] = []

    def fetch_observation(self, symbol: str) -> VenueObservation:
        self.requested_symbols.append(symbol)
        return self.observation


class FailingObservationAdapter:
    name = "failing"

    def __init__(self) -> None:
        self.requested_symbols: list[str] = []

    def fetch_observation(self, symbol: str) -> VenueObservation:
        self.requested_symbols.append(symbol)
        raise ValueError("adapter observation unavailable")


def test_adapter_handoff_runtime_type_hints_resolve() -> None:
    hints = get_type_hints(assemble_route_snapshot_from_adapters)

    assert hints["risex_adapter"] is VenueAdapter
    assert hints["hedge_adapter"] is VenueAdapter
    assert hints["return"] is VenueSnapshot


def test_adapter_handoff_fetches_two_observations_and_returns_assembled_snapshot() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    risex_adapter = RecordingObservationAdapter(risex_observation)
    hedge_adapter = RecordingObservationAdapter(hedge_observation)

    snapshot = assemble_route_snapshot_from_adapters(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=hedge_adapter,
        assembled_at=ASSEMBLED_AT,
    )

    expected_snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )
    assert snapshot == expected_snapshot
    assert risex_adapter.requested_symbols == [route.risex_symbol]
    assert hedge_adapter.requested_symbols == [route.hedge_symbol]


def test_adapter_handoff_delegates_to_single_snapshot_assembly_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    expected_snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )
    captured: dict[str, object] = {}

    def fake_assemble_route_snapshot(*, route, observations, assembled_at):
        captured["route"] = route
        captured["observations"] = observations
        captured["assembled_at"] = assembled_at
        return expected_snapshot

    monkeypatch.setattr(
        snapshot_module,
        "assemble_route_snapshot",
        fake_assemble_route_snapshot,
    )

    snapshot = snapshot_module.assemble_route_snapshot_from_adapters(
        route=route,
        risex_adapter=RecordingObservationAdapter(risex_observation),
        hedge_adapter=RecordingObservationAdapter(hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot is expected_snapshot
    assert captured == {
        "route": route,
        "observations": {
            (route.risex_venue, route.risex_symbol): risex_observation,
            (route.hedge_venue, route.hedge_symbol): hedge_observation,
        },
        "assembled_at": ASSEMBLED_AT,
    }


def test_adapter_handoff_propagates_adapter_observation_failure() -> None:
    route = _route()
    _, hedge_observation = _observations()
    risex_adapter = FailingObservationAdapter()

    with pytest.raises(ValueError, match="adapter observation unavailable"):
        assemble_route_snapshot_from_adapters(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=RecordingObservationAdapter(hedge_observation),
            assembled_at=ASSEMBLED_AT,
        )

    assert risex_adapter.requested_symbols == [route.risex_symbol]


def test_adapter_handoff_rejects_naive_assembly_timestamp_before_fetch() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    risex_adapter = RecordingObservationAdapter(risex_observation)
    hedge_adapter = RecordingObservationAdapter(hedge_observation)

    with pytest.raises(ValueError, match="assembled_at"):
        assemble_route_snapshot_from_adapters(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=hedge_adapter,
            assembled_at=datetime(2026, 1, 1, 12, 0),
        )

    assert risex_adapter.requested_symbols == []
    assert hedge_adapter.requested_symbols == []


def test_adapter_handoff_rejects_non_observation_return() -> None:
    class NonObservationAdapter:
        name = "non-observation"

        def fetch_observation(self, symbol: str) -> object:
            return object()

    route = _route()
    _, hedge_observation = _observations()

    with pytest.raises(SnapshotAssemblyInputError, match="RiseX adapter"):
        assemble_route_snapshot_from_adapters(
            route=route,
            risex_adapter=NonObservationAdapter(),
            hedge_adapter=RecordingObservationAdapter(hedge_observation),
            assembled_at=ASSEMBLED_AT,
        )


def test_adapter_handoff_fails_closed_on_route_conflicting_observation() -> None:
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
        assemble_route_snapshot_from_adapters(
            route=route,
            risex_adapter=RecordingObservationAdapter(risex_observation),
            hedge_adapter=RecordingObservationAdapter(wrong_hedge_observation),
            assembled_at=ASSEMBLED_AT,
        )


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


def test_assembly_preserves_public_fee_metadata_without_completing_cash() -> None:
    route = _route()
    risex_fee_metadata = {
        "public_fee_maker_bps": "1.25",
        "public_fee_metadata_source": "OBSERVED",
    }
    hedge_fee_metadata = {
        "public_fee_schedule_field": "feeTiers",
        "public_fee_metadata_source": "OBSERVED",
    }
    risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="risex_fee_cash_flow_unknown",
                    amount_usd=EstimatedValue(
                        value=None,
                        source=ValueSource.UNKNOWN,
                        metadata=risex_fee_metadata,
                    ),
                ),
            )
        ),
    )
    hedge_observation = _observation(
        venue="Hyperliquid",
        symbol="BTC",
        observed_at=HEDGE_OBSERVED_AT,
        settlement_at=HEDGE_SETTLEMENT_AT,
        funding=EstimatedValue(value=Decimal("-0.5"), source=ValueSource.OBSERVED),
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="hyperliquid_fee_cash_flow_unknown",
                    amount_usd=EstimatedValue(
                        value=None,
                        source=ValueSource.UNKNOWN,
                        metadata=hedge_fee_metadata,
                    ),
                ),
            )
        ),
    )

    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.fees.components[0].amount_usd.value is None
    assert snapshot.fees.components[0].amount_usd.source is ValueSource.UNKNOWN
    assert snapshot.fees.components[0].amount_usd.metadata == risex_fee_metadata
    assert snapshot.fees.components[1].amount_usd.value is None
    assert snapshot.fees.components[1].amount_usd.source is ValueSource.UNKNOWN
    assert snapshot.fees.components[1].amount_usd.metadata == hedge_fee_metadata


def test_assembly_completes_public_funding_rate_metadata_from_route_notional() -> None:
    route = _route()
    risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=_public_rate_funding("0.001"),
        fees=_fees("risex_fees"),
    )
    hedge_observation = _observation(
        venue="Hyperliquid",
        symbol="BTC",
        observed_at=HEDGE_OBSERVED_AT,
        settlement_at=HEDGE_SETTLEMENT_AT,
        funding=_public_rate_funding("0.0004"),
        fees=_fees("hedge_fees"),
    )

    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.funding.risex_funding_usd.value == Decimal("-0.500")
    assert snapshot.funding.risex_funding_usd.source is ValueSource.OBSERVED
    assert snapshot.funding.risex_funding_usd.metadata["entry_side"] == "buy"
    assert snapshot.funding.risex_funding_usd.metadata["target_notional_usd"] == "500"
    assert snapshot.funding.hedge_funding_usd.value == Decimal("0.2000")
    assert snapshot.funding.hedge_funding_usd.source is ValueSource.OBSERVED
    assert snapshot.funding.hedge_funding_usd.metadata["entry_side"] == "sell"
    assert snapshot.funding.hedge_funding_usd.metadata["target_notional_usd"] == "500"


def test_assembly_preserves_malformed_public_funding_rate_metadata_as_unknown() -> None:
    route = _route()
    _, hedge_observation = _observations()
    risex_observation = _observation(
        venue="RiseX",
        symbol="BTC-PERP",
        observed_at=RISEX_OBSERVED_AT,
        settlement_at=RISEX_SETTLEMENT_AT,
        funding=_public_rate_funding("not-a-rate"),
        fees=_fees("risex_fees"),
    )

    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.funding.risex_funding_usd.value is None
    assert snapshot.funding.risex_funding_usd.source is ValueSource.UNKNOWN

    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)


def test_assembly_preserves_mismatched_settlement_timestamps_but_evaluation_rejects() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    mismatched_hedge_observation = _observation(
        venue=hedge_observation.venue,
        symbol=hedge_observation.symbol,
        observed_at=hedge_observation.observed_at,
        settlement_at=MISMATCHED_HEDGE_SETTLEMENT_AT,
        funding=hedge_observation.expected_funding_usd,
        fees=hedge_observation.fees,
        order_book=hedge_observation.order_book,
    )

    snapshot = assemble_route_snapshot(
        route=route,
        observations=_observation_mapping(risex_observation, mismatched_hedge_observation),
        assembled_at=ASSEMBLED_AT,
    )

    assert snapshot.risex_funding_settlement_at == RISEX_SETTLEMENT_AT
    assert snapshot.hedge_funding_settlement_at == MISMATCHED_HEDGE_SETTLEMENT_AT

    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


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


def test_observation_rejects_missing_expected_funding_before_assembly() -> None:
    with pytest.raises(ValueError, match="expected_funding_usd"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=None,
            fees=_fees("risex_fees"),
        )


def test_observation_rejects_missing_fee_model_before_assembly() -> None:
    with pytest.raises(ValueError, match="fees must be a FeeModel"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=None,
        )


def test_observation_rejects_fee_component_missing_amount_before_assembly() -> None:
    malformed_fees = FeeModel(
        components=(FeeComponent(name="missing_fee_amount", amount_usd=None),)
    )

    with pytest.raises(ValueError, match="amount_usd"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=malformed_fees,
        )


def test_observation_rejects_non_fee_component_before_assembly() -> None:
    malformed_fees = FeeModel(components=(None,))

    with pytest.raises(ValueError, match="FeeComponent"):
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            settlement_at=RISEX_SETTLEMENT_AT,
            funding=EstimatedValue(value=Decimal("3"), source=ValueSource.OBSERVED),
            fees=malformed_fees,
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
