from decimal import Decimal

import pytest

from core.domain.contracts import EstimatedValue, FeeComponent, FeeModel
from core.domain.enums import ValueSource
from core.economics.fees import calculate_total_fees_usd


def test_user_configured_fee_default_requires_user_configured_source() -> None:
    fee_model = FeeModel(
        components=(
            FeeComponent(
                name="configured_default",
                amount_usd=EstimatedValue(value=Decimal("0.25"), source=ValueSource.USER_CONFIGURED),
                is_default=True,
            ),
        )
    )

    assert calculate_total_fees_usd(fee_model) == Decimal("0.25")


def test_non_user_configured_fee_default_is_rejected() -> None:
    fee_model = FeeModel(
        components=(
            FeeComponent(
                name="fake_default",
                amount_usd=EstimatedValue(value=Decimal("0.25"), source=ValueSource.DOCUMENTED),
                is_default=True,
            ),
        )
    )

    with pytest.raises(ValueError, match="USER_CONFIGURED"):
        calculate_total_fees_usd(fee_model)


def test_unknown_fee_cannot_participate_as_zero() -> None:
    fee_model = FeeModel(
        components=(
            FeeComponent(
                name="unknown_fee",
                amount_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
            ),
        )
    )

    with pytest.raises(ValueError, match="UNKNOWN"):
        calculate_total_fees_usd(fee_model)


def test_empty_fee_model_cannot_mean_zero_fees() -> None:
    with pytest.raises(ValueError, match="source-aware"):
        calculate_total_fees_usd(FeeModel(components=()))


def test_negative_fee_is_rejected_until_rebates_are_modeled() -> None:
    fee_model = FeeModel(
        components=(
            FeeComponent(
                name="negative_fee",
                amount_usd=EstimatedValue(value=Decimal("-0.01"), source=ValueSource.OBSERVED),
            ),
        )
    )

    with pytest.raises(ValueError, match="negative fees"):
        calculate_total_fees_usd(fee_model)
