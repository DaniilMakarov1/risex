"""Funding cash-flow calculations live here only."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from core.domain.contracts import EstimatedValue, FundingSnapshot, OrderSide
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError

PUBLIC_FUNDING_RATE_METADATA_KEY = "public_funding_rate"
PUBLIC_FUNDING_RATE_SOURCE_METADATA_KEY = "public_funding_rate_source"

ALLOWED_FUNDING_SOURCES = frozenset(
    {
        ValueSource.DOCUMENTED,
        ValueSource.OBSERVED,
        ValueSource.ESTIMATED_FROM_LAST_VALUE,
    }
)


def complete_public_funding_cash_flow(
    value: EstimatedValue,
    *,
    target_notional_usd: Decimal,
    entry_side: OrderSide,
) -> EstimatedValue:
    """Complete public funding-rate metadata into route-notional USD cash flow."""

    if value.source is not ValueSource.UNKNOWN:
        return value
    raw_rate = value.metadata.get(PUBLIC_FUNDING_RATE_METADATA_KEY)
    raw_source = value.metadata.get(PUBLIC_FUNDING_RATE_SOURCE_METADATA_KEY)
    if raw_rate is None or raw_source != ValueSource.OBSERVED.value:
        return value
    if not target_notional_usd.is_finite() or target_notional_usd <= Decimal("0"):
        return value
    try:
        funding_rate = Decimal(raw_rate)
    except (InvalidOperation, ValueError):
        return value
    if not funding_rate.is_finite():
        return value

    if entry_side == "buy":
        cash_flow_sign = Decimal("-1")
    elif entry_side == "sell":
        cash_flow_sign = Decimal("1")
    else:
        raise ValueError("entry_side must be 'buy' or 'sell'")

    metadata = {
        **dict(value.metadata),
        "entry_side": entry_side,
        "funding_cash_flow_sign": str(cash_flow_sign),
        "target_notional_usd": str(target_notional_usd),
    }
    return EstimatedValue(
        value=funding_rate * target_notional_usd * cash_flow_sign,
        source=ValueSource.OBSERVED,
        description=(
            "Public funding rate converted to USD cash flow from the "
            "explicit route target notional and entry side."
        ),
        metadata=metadata,
    )


def calculate_expected_funding_usd(value: EstimatedValue) -> Decimal:
    """Return one source-aware funding estimate in USD."""

    if value.source not in ALLOWED_FUNDING_SOURCES:
        raise EconomicsInputError(f"funding estimate has unsupported source {value.source.value}")
    return value.require_value()


def calculate_total_expected_funding_usd(funding: FundingSnapshot) -> Decimal:
    """Combine source-aware funding estimates from the RiseX and hedge legs."""

    return calculate_expected_funding_usd(
        funding.risex_funding_usd
    ) + calculate_expected_funding_usd(funding.hedge_funding_usd)
