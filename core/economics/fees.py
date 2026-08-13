"""Fee calculations live here only."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from core.domain.contracts import EstimatedValue, FeeComponent, FeeModel
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError

PUBLIC_FEE_TAKER_BPS_METADATA_KEY = "public_fee_taker_bps"
PUBLIC_FEE_TAKER_RATE_METADATA_KEY = "public_fee_taker_rate"
PUBLIC_FEE_METADATA_SOURCE_KEY = "public_fee_metadata_source"
PUBLIC_FEE_METADATA_KIND_KEY = "public_fee_metadata_kind"
PUBLIC_FEE_ACCOUNT_SCOPE_KEY = "public_fee_account_scope"
PUBLIC_FEE_FILL_COUNT = Decimal("2")

ALLOWED_FEE_SOURCES = frozenset(
    {
        ValueSource.DOCUMENTED,
        ValueSource.OBSERVED,
        ValueSource.USER_CONFIGURED,
    }
)


def complete_public_taker_fee_component_cash(
    component: FeeComponent,
    *,
    target_notional_usd: Decimal,
) -> FeeComponent:
    """Complete public taker fee metadata into entry+estimated-exit USD cash."""

    amount = component.amount_usd
    if amount.source is not ValueSource.UNKNOWN:
        return component
    if component.is_default:
        return component
    if not target_notional_usd.is_finite() or target_notional_usd <= Decimal("0"):
        return component

    metadata = amount.metadata
    if metadata.get(PUBLIC_FEE_METADATA_SOURCE_KEY) != ValueSource.OBSERVED.value:
        return component
    if metadata.get(PUBLIC_FEE_METADATA_KIND_KEY) != "fee_rate_fields":
        return component
    if metadata.get(PUBLIC_FEE_ACCOUNT_SCOPE_KEY) != "account_independent":
        return component

    raw_taker_bps = metadata.get(PUBLIC_FEE_TAKER_BPS_METADATA_KEY)
    raw_taker_rate = metadata.get(PUBLIC_FEE_TAKER_RATE_METADATA_KEY)
    if (raw_taker_bps is None and raw_taker_rate is None) or (
        raw_taker_bps is not None and raw_taker_rate is not None
    ):
        return component

    try:
        if raw_taker_bps is not None:
            taker_fee_rate = Decimal(raw_taker_bps) / Decimal("10000")
            rate_metadata_key = PUBLIC_FEE_TAKER_BPS_METADATA_KEY
        else:
            taker_fee_rate = Decimal(raw_taker_rate)
            rate_metadata_key = PUBLIC_FEE_TAKER_RATE_METADATA_KEY
    except (InvalidOperation, TypeError, ValueError):
        return component

    rate_field = metadata.get(f"{rate_metadata_key}_field")
    rate_container = metadata.get(f"{rate_metadata_key}_container")
    if not isinstance(rate_field, str) or not rate_field.strip():
        return component
    if not isinstance(rate_container, str) or not rate_container.strip():
        return component

    if not taker_fee_rate.is_finite() or taker_fee_rate < Decimal("0"):
        return component

    completed_metadata = {
        **dict(metadata),
        "public_fee_completed_role": "taker",
        "public_fee_completion_basis": "route_target_notional",
        "public_fee_completed_fills": "entry+estimated_exit",
        "public_fee_fill_count": str(PUBLIC_FEE_FILL_COUNT),
        "public_fee_quote_model": "order_book_taker",
        "public_fee_rate_decimal": str(taker_fee_rate),
        "public_fee_rate_metadata_key": rate_metadata_key,
        "target_notional_usd": str(target_notional_usd),
    }
    return FeeComponent(
        name=component.name,
        amount_usd=EstimatedValue(
            value=taker_fee_rate * target_notional_usd * PUBLIC_FEE_FILL_COUNT,
            source=ValueSource.OBSERVED,
            description=(
                "Public account-independent taker fee rate converted to entry plus "
                "estimated-exit USD cash from the explicit route target notional."
            ),
            metadata=completed_metadata,
        ),
        is_default=False,
    )


def validate_fee_component(component: FeeComponent) -> None:
    """Validate source-aware fee inputs before they enter economics math."""

    source = component.amount_usd.source
    if source not in ALLOWED_FEE_SOURCES:
        raise EconomicsInputError(
            f"fee component {component.name!r} has unsupported source {source.value}"
        )
    if component.is_default and source is not ValueSource.USER_CONFIGURED:
        raise EconomicsInputError("fee defaults require ValueSource.USER_CONFIGURED")
    if component.amount_usd.require_value() < Decimal("0"):
        raise EconomicsInputError("negative fees are not modeled in RX-003")


def calculate_fee_component_usd(component: FeeComponent) -> Decimal:
    """Return one validated fee amount in USD."""

    validate_fee_component(component)
    return component.amount_usd.require_value()


def calculate_total_fees_usd(fee_model: FeeModel) -> Decimal:
    """Return total documented, observed, or user-configured fees in USD."""

    if not fee_model.components:
        raise EconomicsInputError("fee model requires at least one source-aware component")

    total = Decimal("0")
    for component in fee_model.components:
        total += calculate_fee_component_usd(component)
    return total
