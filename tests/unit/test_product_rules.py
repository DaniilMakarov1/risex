from dataclasses import fields
from decimal import Decimal

from core.config.product_rules import ProductRules


def test_live_trading_disabled_by_default() -> None:
    assert ProductRules().live_trading_enabled is False


def test_min_leg_notional_is_500() -> None:
    assert ProductRules().min_leg_notional_usd == Decimal("500")


def test_min_net_profit_is_1() -> None:
    assert ProductRules().min_net_profit_usd == Decimal("1")


def test_product_rules_zero_value_components_are_zero() -> None:
    rules = ProductRules()

    assert rules.points_value_usd == Decimal("0")
    assert rules.expected_airdrop_value_usd == Decimal("0")
    assert rules.leaderboard_rewards_base_pnl_usd == Decimal("0")
    assert rules.unreceived_rebates_usd == Decimal("0")


def test_product_rules_do_not_contain_artificial_filter_fields() -> None:
    product_rule_fields = {field.name for field in fields(ProductRules)}

    assert "max_spread_bps" not in product_rule_fields
    assert "max_price_impact_bps" not in product_rule_fields
    assert "max_levels_consumed" not in product_rule_fields
    assert "conservative_buffer" not in product_rule_fields
    assert "safety_margin" not in product_rule_fields
