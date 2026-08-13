from decimal import Decimal

import pytest

from core.domain.contracts import EstimatedValue, FeeComponent, FeeModel
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError
from core.economics.fees import (
    calculate_total_fees_usd,
    complete_public_taker_fee_component_cash,
)


def _unknown_fee_component(metadata: dict[str, str]) -> FeeComponent:
    return FeeComponent(
        name="public_fee_cash_flow_unknown",
        amount_usd=EstimatedValue(
            value=None,
            source=ValueSource.UNKNOWN,
            metadata=metadata,
        ),
    )


def _public_taker_fee_metadata(**overrides: str) -> dict[str, str]:
    metadata = {
        "public_fee_taker_bps": "3.5",
        "public_fee_taker_bps_field": "taker_fee_bps",
        "public_fee_taker_bps_container": "market",
        "public_fee_metadata_source": "OBSERVED",
        "public_fee_metadata_kind": "fee_rate_fields",
        "public_fee_account_scope": "account_independent",
    }
    metadata.update(overrides)
    return metadata


def _public_taker_rate_fee_metadata(**overrides: str) -> dict[str, str]:
    metadata = {
        "public_fee_taker_rate": "0.00045",
        "public_fee_taker_rate_field": "takerFeeRate",
        "public_fee_taker_rate_container": "config",
        "public_fee_metadata_source": "OBSERVED",
        "public_fee_metadata_kind": "fee_rate_fields",
        "public_fee_account_scope": "account_independent",
    }
    metadata.update(overrides)
    return metadata


def test_public_taker_bps_fee_metadata_completes_entry_and_exit_cash_from_notional() -> None:
    component = _unknown_fee_component(_public_taker_fee_metadata())

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=Decimal("500"),
    )

    assert completed.amount_usd.value == Decimal("0.35000")
    assert completed.amount_usd.source is ValueSource.OBSERVED
    assert completed.amount_usd.metadata["public_fee_taker_bps"] == "3.5"
    assert completed.amount_usd.metadata["public_fee_rate_decimal"] == "0.00035"
    assert completed.amount_usd.metadata["public_fee_completed_role"] == "taker"
    assert completed.amount_usd.metadata["public_fee_completed_fills"] == (
        "entry+estimated_exit"
    )
    assert completed.amount_usd.metadata["public_fee_fill_count"] == "2"
    assert completed.amount_usd.metadata["public_fee_quote_model"] == "order_book_taker"
    assert completed.amount_usd.metadata["target_notional_usd"] == "500"


def test_public_taker_rate_fee_metadata_completes_entry_and_exit_cash_from_notional() -> None:
    component = _unknown_fee_component(_public_taker_rate_fee_metadata())

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=Decimal("500"),
    )

    assert completed.amount_usd.value == Decimal("0.45000")
    assert completed.amount_usd.source is ValueSource.OBSERVED
    assert completed.amount_usd.metadata["public_fee_rate_metadata_key"] == (
        "public_fee_taker_rate"
    )


@pytest.mark.parametrize(
    "metadata",
    (
        _public_taker_fee_metadata(public_fee_taker_bps_field=""),
        _public_taker_fee_metadata(public_fee_taker_bps_container=""),
        _public_taker_rate_fee_metadata(public_fee_taker_rate_field=""),
        _public_taker_rate_fee_metadata(public_fee_taker_rate_container=""),
    ),
)
def test_public_taker_fee_completion_requires_selected_rate_field_and_container_provenance(
    metadata: dict[str, str],
) -> None:
    component = _unknown_fee_component(metadata)

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=Decimal("500"),
    )

    assert completed is component
    assert completed.amount_usd.value is None
    assert completed.amount_usd.source is ValueSource.UNKNOWN


@pytest.mark.parametrize(
    "metadata",
    (
        {},
        {"public_fee_taker_bps": "3.5", "public_fee_metadata_source": "OBSERVED"},
        _public_taker_fee_metadata(public_fee_taker_bps="not-a-fee"),
        _public_taker_fee_metadata(public_fee_taker_bps="NaN"),
        _public_taker_fee_metadata(public_fee_taker_bps="Infinity"),
        _public_taker_fee_metadata(public_fee_taker_bps="-1"),
        _public_taker_fee_metadata(public_fee_metadata_source="DOCUMENTED"),
        _public_taker_fee_metadata(public_fee_metadata_kind="account_tier_schedule"),
        _public_taker_fee_metadata(public_fee_account_scope="account_tier_dependent"),
        _public_taker_fee_metadata(public_fee_account_scope="account_state_dependent"),
        {
            "public_fee_maker_bps": "1.25",
            "public_fee_metadata_source": "OBSERVED",
            "public_fee_metadata_kind": "fee_rate_fields",
            "public_fee_account_scope": "account_independent",
        },
        {
            "public_fee_taker_bps": "3.5",
            "public_fee_taker_rate": "0.00035",
            "public_fee_metadata_source": "OBSERVED",
            "public_fee_metadata_kind": "fee_rate_fields",
            "public_fee_account_scope": "account_independent",
        },
    ),
)
def test_public_taker_fee_completion_preserves_ungrounded_values_as_unknown(
    metadata: dict[str, str],
) -> None:
    component = _unknown_fee_component(metadata)

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=Decimal("500"),
    )

    assert completed is component
    assert completed.amount_usd.value is None
    assert completed.amount_usd.source is ValueSource.UNKNOWN


@pytest.mark.parametrize("target_notional_usd", (Decimal("0"), Decimal("-1"), Decimal("NaN")))
def test_public_taker_fee_completion_requires_grounded_route_notional(
    target_notional_usd: Decimal,
) -> None:
    component = _unknown_fee_component(_public_taker_fee_metadata())

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=target_notional_usd,
    )

    assert completed is component
    assert completed.amount_usd.value is None
    assert completed.amount_usd.source is ValueSource.UNKNOWN


def test_public_taker_fee_completion_does_not_replace_existing_known_values() -> None:
    component = FeeComponent(
        name="documented_fee",
        amount_usd=EstimatedValue(
            value=Decimal("0.25"),
            source=ValueSource.DOCUMENTED,
            metadata=_public_taker_fee_metadata(),
        ),
    )

    completed = complete_public_taker_fee_component_cash(
        component,
        target_notional_usd=Decimal("500"),
    )

    assert completed is component


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

    with pytest.raises(EconomicsInputError, match="USER_CONFIGURED"):
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

    with pytest.raises(EconomicsInputError, match="UNKNOWN"):
        calculate_total_fees_usd(fee_model)


def test_unknown_public_fee_metadata_cannot_participate_as_zero() -> None:
    fee_model = FeeModel(
        components=(
            FeeComponent(
                name="unknown_public_fee_metadata",
                amount_usd=EstimatedValue(
                    value=None,
                    source=ValueSource.UNKNOWN,
                    metadata={
                        "public_fee_maker_bps": "1.25",
                        "public_fee_metadata_source": "OBSERVED",
                    },
                ),
            ),
        )
    )

    with pytest.raises(EconomicsInputError, match="UNKNOWN"):
        calculate_total_fees_usd(fee_model)


def test_empty_fee_model_cannot_mean_zero_fees() -> None:
    with pytest.raises(EconomicsInputError, match="source-aware"):
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

    with pytest.raises(EconomicsInputError, match="negative fees"):
        calculate_total_fees_usd(fee_model)
