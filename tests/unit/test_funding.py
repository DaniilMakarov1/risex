from decimal import Decimal

import pytest

from core.domain.contracts import EstimatedValue, FundingSnapshot
from core.domain.enums import ValueSource
from core.economics.funding import calculate_total_expected_funding_usd


def test_last_observed_funding_fallback_uses_last_value_source() -> None:
    funding = FundingSnapshot(
        risex_funding_usd=EstimatedValue(
            value=Decimal("2"),
            source=ValueSource.ESTIMATED_FROM_LAST_VALUE,
        ),
        hedge_funding_usd=EstimatedValue(
            value=Decimal("-0.25"),
            source=ValueSource.OBSERVED,
        ),
    )

    assert calculate_total_expected_funding_usd(funding) == Decimal("1.75")


def test_missing_funding_estimate_cannot_become_zero() -> None:
    funding = FundingSnapshot(
        risex_funding_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
        hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
    )

    with pytest.raises(ValueError, match="UNKNOWN"):
        calculate_total_expected_funding_usd(funding)


def test_user_configured_funding_is_not_a_valid_rx003_funding_estimate() -> None:
    funding = FundingSnapshot(
        risex_funding_usd=EstimatedValue(value=Decimal("1"), source=ValueSource.USER_CONFIGURED),
        hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
    )

    with pytest.raises(ValueError, match="USER_CONFIGURED"):
        calculate_total_expected_funding_usd(funding)
