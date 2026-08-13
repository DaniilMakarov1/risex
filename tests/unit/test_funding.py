from decimal import Decimal

import pytest

from core.domain.contracts import EstimatedValue, FundingSnapshot
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError
from core.economics.funding import (
    calculate_total_expected_funding_usd,
    complete_public_funding_cash_flow,
)


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

    with pytest.raises(EconomicsInputError, match="UNKNOWN"):
        calculate_total_expected_funding_usd(funding)


def test_user_configured_funding_is_not_a_valid_rx003_funding_estimate() -> None:
    funding = FundingSnapshot(
        risex_funding_usd=EstimatedValue(value=Decimal("1"), source=ValueSource.USER_CONFIGURED),
        hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
    )

    with pytest.raises(EconomicsInputError, match="USER_CONFIGURED"):
        calculate_total_expected_funding_usd(funding)


def test_public_funding_rate_metadata_completes_buy_side_cash_flow_from_notional() -> None:
    value = EstimatedValue(
        value=None,
        source=ValueSource.UNKNOWN,
        metadata={
            "public_funding_rate": "0.001",
            "public_funding_rate_source": "OBSERVED",
        },
    )

    completed = complete_public_funding_cash_flow(
        value,
        target_notional_usd=Decimal("500"),
        entry_side="buy",
    )

    assert completed.value == Decimal("-0.500")
    assert completed.source is ValueSource.OBSERVED
    assert completed.metadata["public_funding_rate"] == "0.001"
    assert completed.metadata["target_notional_usd"] == "500"
    assert completed.metadata["entry_side"] == "buy"
    assert completed.metadata["funding_cash_flow_sign"] == "-1"


def test_public_funding_rate_metadata_completes_sell_side_cash_flow_from_notional() -> None:
    value = EstimatedValue(
        value=None,
        source=ValueSource.UNKNOWN,
        metadata={
            "public_funding_rate": "0.001",
            "public_funding_rate_source": "OBSERVED",
        },
    )

    completed = complete_public_funding_cash_flow(
        value,
        target_notional_usd=Decimal("500"),
        entry_side="sell",
    )

    assert completed.value == Decimal("0.500")
    assert completed.source is ValueSource.OBSERVED


@pytest.mark.parametrize(
    "metadata",
    (
        {},
        {"public_funding_rate": "not-a-rate", "public_funding_rate_source": "OBSERVED"},
        {"public_funding_rate": "NaN", "public_funding_rate_source": "OBSERVED"},
        {"public_funding_rate": "0.001", "public_funding_rate_source": "DOCUMENTED"},
    ),
)
def test_public_funding_rate_completion_preserves_ungrounded_values_as_unknown(
    metadata: dict[str, str],
) -> None:
    value = EstimatedValue(value=None, source=ValueSource.UNKNOWN, metadata=metadata)

    completed = complete_public_funding_cash_flow(
        value,
        target_notional_usd=Decimal("500"),
        entry_side="buy",
    )

    assert completed.value is None
    assert completed.source is ValueSource.UNKNOWN


def test_public_funding_completion_does_not_replace_existing_known_values() -> None:
    value = EstimatedValue(
        value=Decimal("2"),
        source=ValueSource.OBSERVED,
        metadata={
            "public_funding_rate": "0.001",
            "public_funding_rate_source": "OBSERVED",
        },
    )

    completed = complete_public_funding_cash_flow(
        value,
        target_notional_usd=Decimal("500"),
        entry_side="buy",
    )

    assert completed is value
