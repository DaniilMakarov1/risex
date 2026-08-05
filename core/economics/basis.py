"""Basis and unwind tracking belongs here only."""

from __future__ import annotations

from decimal import Decimal


def calculate_current_unwind_pnl_usd(
    *,
    current_unwind_value_usd: Decimal,
    entry_value_usd: Decimal,
    realized_cashflows_usd: Decimal,
) -> Decimal:
    """Calculate current PnL if both legs were unwound now.

    This does not predict future basis changes.
    """

    return current_unwind_value_usd - entry_value_usd + realized_cashflows_usd
