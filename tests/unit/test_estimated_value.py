from decimal import Decimal

import pytest

from core.domain.contracts import EstimatedValue
from core.domain.enums import ValueSource


def test_estimated_value_requires_known_source_for_numeric_value() -> None:
    value = EstimatedValue(
        value=Decimal("1.23"),
        source=ValueSource.USER_CONFIGURED,
        description="test default fee",
    )

    assert value.require_value() == Decimal("1.23")


def test_estimated_value_unknown_cannot_carry_numeric_zero() -> None:
    with pytest.raises(ValueError, match="UNKNOWN"):
        EstimatedValue(value=Decimal("0"), source=ValueSource.UNKNOWN)


def test_estimated_value_unknown_does_not_silently_become_zero() -> None:
    unknown = EstimatedValue(value=None, source=ValueSource.UNKNOWN)

    with pytest.raises(ValueError, match="UNKNOWN values must not silently become zero"):
        unknown.require_value()


def test_estimated_value_known_source_requires_numeric_value() -> None:
    with pytest.raises(ValueError, match="Known value sources"):
        EstimatedValue(value=None, source=ValueSource.ESTIMATED_FROM_LAST_VALUE)
