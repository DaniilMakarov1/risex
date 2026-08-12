"""Authoritative route snapshot assembly from per-venue observations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

from core.domain.contracts import (
    FeeModel,
    FundingSnapshot,
    OrderSide,
    RouteCandidate,
    VenueObservation,
    VenueSnapshot,
    validate_timezone_aware_datetime,
)
from core.economics.liquidity import calculate_executable_quote

if TYPE_CHECKING:
    from core.venues.base import VenueAdapter

ObservationKey = tuple[str, str]


class SnapshotAssemblyInputError(ValueError):
    """Raised when normalized observations cannot form the requested route snapshot."""


def _observation_key(observation: VenueObservation) -> ObservationKey:
    return (observation.venue, observation.symbol)


def _opposite_side(side: OrderSide) -> OrderSide:
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    raise SnapshotAssemblyInputError("route entry side must be 'buy' or 'sell'")


def _validate_observation_mapping(
    observations: Mapping[ObservationKey, VenueObservation],
) -> None:
    for key, observation in observations.items():
        if key != _observation_key(observation):
            raise SnapshotAssemblyInputError(
                "observation mapping key conflicts with observation metadata"
            )


def _required_observation(
    observations: Mapping[ObservationKey, VenueObservation],
    *,
    key: ObservationKey,
    leg_name: str,
) -> VenueObservation:
    try:
        return observations[key]
    except KeyError as exc:
        raise SnapshotAssemblyInputError(f"missing {leg_name} observation") from exc


def _validate_route_observation_alignment(
    observation: VenueObservation,
    *,
    expected_venue: str,
    expected_symbol: str,
    leg_name: str,
) -> None:
    if observation.venue != expected_venue:
        raise SnapshotAssemblyInputError(f"{leg_name} observation venue conflicts with route")
    if observation.symbol != expected_symbol:
        raise SnapshotAssemblyInputError(f"{leg_name} observation symbol conflicts with route")


def assemble_route_snapshot(
    *,
    route: RouteCandidate,
    observations: Mapping[ObservationKey, VenueObservation],
    assembled_at: datetime,
) -> VenueSnapshot:
    """Build one route-aligned snapshot without evaluating route eligibility."""

    validate_timezone_aware_datetime(assembled_at, "assembled_at")

    risex_observation = _required_observation(
        observations,
        key=(route.risex_venue, route.risex_symbol),
        leg_name="RiseX",
    )
    hedge_observation = _required_observation(
        observations,
        key=(route.hedge_venue, route.hedge_symbol),
        leg_name="hedge",
    )

    _validate_route_observation_alignment(
        risex_observation,
        expected_venue=route.risex_venue,
        expected_symbol=route.risex_symbol,
        leg_name="RiseX",
    )
    _validate_route_observation_alignment(
        hedge_observation,
        expected_venue=route.hedge_venue,
        expected_symbol=route.hedge_symbol,
        leg_name="hedge",
    )
    _validate_observation_mapping(observations)

    risex_entry_quote = calculate_executable_quote(
        order_book=risex_observation.order_book,
        side=route.risex_entry_side,
        target_notional_usd=route.target_notional_usd,
    )
    hedge_entry_quote = calculate_executable_quote(
        order_book=hedge_observation.order_book,
        side=route.hedge_entry_side,
        target_notional_usd=route.target_notional_usd,
    )
    risex_exit_quote = calculate_executable_quote(
        order_book=risex_observation.order_book,
        side=_opposite_side(route.risex_entry_side),
        target_notional_usd=route.target_notional_usd,
    )
    hedge_exit_quote = calculate_executable_quote(
        order_book=hedge_observation.order_book,
        side=_opposite_side(route.hedge_entry_side),
        target_notional_usd=route.target_notional_usd,
    )

    return VenueSnapshot(
        captured_at=assembled_at,
        risex_observed_at=risex_observation.observed_at,
        hedge_observed_at=hedge_observation.observed_at,
        risex_funding_settlement_at=risex_observation.funding_settlement_at,
        hedge_funding_settlement_at=hedge_observation.funding_settlement_at,
        risex_entry_quote=risex_entry_quote,
        hedge_entry_quote=hedge_entry_quote,
        risex_estimated_exit_quote=risex_exit_quote,
        hedge_estimated_exit_quote=hedge_exit_quote,
        funding=FundingSnapshot(
            risex_funding_usd=risex_observation.expected_funding_usd,
            hedge_funding_usd=hedge_observation.expected_funding_usd,
        ),
        fees=FeeModel(
            components=risex_observation.fees.components + hedge_observation.fees.components
        ),
    )


def assemble_route_snapshot_from_adapters(
    *,
    route: RouteCandidate,
    risex_adapter: VenueAdapter,
    hedge_adapter: VenueAdapter,
    assembled_at: datetime,
) -> VenueSnapshot:
    """Fetch the two route observations and delegate snapshot construction."""

    validate_timezone_aware_datetime(assembled_at, "assembled_at")

    risex_observation = risex_adapter.fetch_observation(route.risex_symbol)
    hedge_observation = hedge_adapter.fetch_observation(route.hedge_symbol)

    if not isinstance(risex_observation, VenueObservation):
        raise SnapshotAssemblyInputError("RiseX adapter must return a VenueObservation")
    if not isinstance(hedge_observation, VenueObservation):
        raise SnapshotAssemblyInputError("hedge adapter must return a VenueObservation")

    return assemble_route_snapshot(
        route=route,
        observations={
            (route.risex_venue, route.risex_symbol): risex_observation,
            (route.hedge_venue, route.hedge_symbol): hedge_observation,
        },
        assembled_at=assembled_at,
    )
