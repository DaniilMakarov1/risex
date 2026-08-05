"""Liquidity and VWAP calculations live here only."""

from __future__ import annotations

from decimal import Decimal

from core.domain.contracts import ExecutableQuote, VenueSnapshot


def quote_is_executable_for_notional(
    quote: ExecutableQuote,
    *,
    min_leg_notional_usd: Decimal,
) -> bool:
    """Check technical executability for the configured target notional.

    This is not a spread, price impact, or slippage filter. It only checks whether
    the requested notional can be represented by the provided executable VWAP.
    """

    return quote.executable and quote.target_notional_usd >= min_leg_notional_usd


def calculate_quote_roundtrip_cost_usd(
    *,
    entry_quote: ExecutableQuote,
    exit_quote: ExecutableQuote,
) -> Decimal:
    """Estimate immediate unwind cost from current executable VWAP quotes."""

    if entry_quote.vwap_price <= Decimal("0"):
        raise ValueError("entry_quote.vwap_price must be positive")
    price_delta = abs(entry_quote.vwap_price - exit_quote.vwap_price)
    return (price_delta / entry_quote.vwap_price) * entry_quote.target_notional_usd


def calculate_total_simulated_roundtrip_cost_usd(snapshot: VenueSnapshot) -> Decimal:
    """Calculate simulated immediate roundtrip cost for both legs."""

    risex_cost = calculate_quote_roundtrip_cost_usd(
        entry_quote=snapshot.risex_entry_quote,
        exit_quote=snapshot.risex_estimated_exit_quote,
    )
    hedge_cost = calculate_quote_roundtrip_cost_usd(
        entry_quote=snapshot.hedge_entry_quote,
        exit_quote=snapshot.hedge_estimated_exit_quote,
    )
    return risex_cost + hedge_cost
