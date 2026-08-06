"""Fee calculations live here only."""

from __future__ import annotations

from decimal import Decimal

from core.domain.contracts import FeeComponent, FeeModel
from core.domain.enums import ValueSource


ALLOWED_FEE_SOURCES = frozenset(
    {
        ValueSource.DOCUMENTED,
        ValueSource.OBSERVED,
        ValueSource.USER_CONFIGURED,
    }
)


def validate_fee_component(component: FeeComponent) -> None:
    """Validate source-aware fee inputs before they enter economics math."""

    source = component.amount_usd.source
    if source not in ALLOWED_FEE_SOURCES:
        raise ValueError(
            f"fee component {component.name!r} has unsupported source {source.value}"
        )
    if component.is_default and source is not ValueSource.USER_CONFIGURED:
        raise ValueError("fee defaults require ValueSource.USER_CONFIGURED")
    if component.amount_usd.require_value() < Decimal("0"):
        raise ValueError("negative fees are not modeled in RX-003")


def calculate_fee_component_usd(component: FeeComponent) -> Decimal:
    """Return one validated fee amount in USD."""

    validate_fee_component(component)
    return component.amount_usd.require_value()


def calculate_total_fees_usd(fee_model: FeeModel) -> Decimal:
    """Return total documented, observed, or user-configured fees in USD."""

    if not fee_model.components:
        raise ValueError("fee model requires at least one source-aware component")

    total = Decimal("0")
    for component in fee_model.components:
        total += calculate_fee_component_usd(component)
    return total
