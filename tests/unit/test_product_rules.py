from decimal import Decimal

from core.config.product_rules import ProductRules


def test_live_trading_disabled_by_default() -> None:
    assert ProductRules().live_trading_enabled is False


def test_min_leg_notional_is_500() -> None:
    assert ProductRules().min_leg_notional_usd == Decimal("500")


def test_min_net_profit_is_1() -> None:
    assert ProductRules().min_net_profit_usd == Decimal("1")
