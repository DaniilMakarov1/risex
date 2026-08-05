"""Fee calculations live here only."""

from __future__ import annotations

from decimal import Decimal


def calculate_total_fees_usd(*, documented_fees_usd: Decimal) -> Decimal:
    """Return explicitly documented, observed, or user-configured fees.

    RX-000 accepts fake snapshots only. Unknown fees must be handled upstream by
    withholding live eligibility, not by silently converting unknown values to zero.
    """

    if documented_fees_usd < Decimal("0"):
        raise ValueError("documented_fees_usd cannot be negative")
    return documented_fees_usd
