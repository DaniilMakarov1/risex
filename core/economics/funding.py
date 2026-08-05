"""Funding cash-flow calculations live here only."""

from __future__ import annotations

from decimal import Decimal


def calculate_total_expected_funding_usd(
    *,
    expected_risex_funding_usd: Decimal,
    expected_hedge_funding_usd: Decimal,
) -> Decimal:
    """Combine explicit funding estimates from the RiseX and hedge legs."""

    return expected_risex_funding_usd + expected_hedge_funding_usd
