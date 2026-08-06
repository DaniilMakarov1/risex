"""Funding cash-flow calculations live here only."""

from __future__ import annotations

from decimal import Decimal

from core.domain.contracts import EstimatedValue, FundingSnapshot
from core.domain.enums import ValueSource


ALLOWED_FUNDING_SOURCES = frozenset(
    {
        ValueSource.DOCUMENTED,
        ValueSource.OBSERVED,
        ValueSource.ESTIMATED_FROM_LAST_VALUE,
    }
)


def calculate_expected_funding_usd(value: EstimatedValue) -> Decimal:
    """Return one source-aware funding estimate in USD."""

    if value.source not in ALLOWED_FUNDING_SOURCES:
        raise ValueError(f"funding estimate has unsupported source {value.source.value}")
    return value.require_value()


def calculate_total_expected_funding_usd(funding: FundingSnapshot) -> Decimal:
    """Combine source-aware funding estimates from the RiseX and hedge legs."""

    return calculate_expected_funding_usd(
        funding.risex_funding_usd
    ) + calculate_expected_funding_usd(funding.hedge_funding_usd)
