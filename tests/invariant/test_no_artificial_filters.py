from dataclasses import fields

from core.config.product_rules import ProductRules


def test_product_rules_do_not_define_no_artificial_filter_fields() -> None:
    field_names = {field.name for field in fields(ProductRules)}

    assert field_names.isdisjoint(
        {
            "max_spread_bps",
            "max_price_impact_bps",
            "max_levels_consumed",
            "hidden_conservative_buffer",
            "conservative_buffer",
            "hidden_safety_margin",
            "safety_margin",
        }
    )
