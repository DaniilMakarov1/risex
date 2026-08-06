"""Basis and unwind tracking belongs here only."""

from __future__ import annotations

from decimal import Decimal

from core.domain.contracts import ExecutableQuote
from core.economics.liquidity import calculate_quote_roundtrip_cost_usd


def calculate_current_unwind_pnl_usd(
    *,
    risex_entry_quote: ExecutableQuote,
    hedge_entry_quote: ExecutableQuote,
    risex_exit_quote: ExecutableQuote,
    hedge_exit_quote: ExecutableQuote,
    realized_cashflows_usd: Decimal,
) -> Decimal:
    """Calculate current PnL if both legs were unwound at current executable VWAP.

    This does not predict future basis changes.
    """

    unwind_cost_usd = calculate_quote_roundtrip_cost_usd(
        entry_quote=risex_entry_quote,
        exit_quote=risex_exit_quote,
    ) + calculate_quote_roundtrip_cost_usd(
        entry_quote=hedge_entry_quote,
        exit_quote=hedge_exit_quote,
    )
    return realized_cashflows_usd - unwind_cost_usd
