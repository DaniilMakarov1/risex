"""Entry EV calculations live here only."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.domain.contracts import VenueSnapshot
from core.economics.fees import calculate_total_fees_usd
from core.economics.funding import calculate_total_expected_funding_usd
from core.economics.liquidity import calculate_total_simulated_roundtrip_cost_usd


@dataclass(frozen=True, slots=True)
class EntryEV:
    """Current-entry EV based on executable VWAP and explicit cash-flow inputs."""

    expected_funding_usd: Decimal
    documented_fees_usd: Decimal
    simulated_roundtrip_cost_usd: Decimal
    net_profit_usd: Decimal


def calculate_entry_ev(snapshot: VenueSnapshot) -> EntryEV:
    """Calculate entry EV without future basis prediction."""

    expected_funding_usd = calculate_total_expected_funding_usd(
        expected_risex_funding_usd=snapshot.expected_risex_funding_usd,
        expected_hedge_funding_usd=snapshot.expected_hedge_funding_usd,
    )
    documented_fees_usd = calculate_total_fees_usd(
        documented_fees_usd=snapshot.documented_fees_usd,
    )
    simulated_roundtrip_cost_usd = calculate_total_simulated_roundtrip_cost_usd(snapshot)
    net_profit_usd = expected_funding_usd - documented_fees_usd - simulated_roundtrip_cost_usd
    return EntryEV(
        expected_funding_usd=expected_funding_usd,
        documented_fees_usd=documented_fees_usd,
        simulated_roundtrip_cost_usd=simulated_roundtrip_cost_usd,
        net_profit_usd=net_profit_usd,
    )
