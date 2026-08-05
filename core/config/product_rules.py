"""Product-level defaults and switches."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProductRules:
    """Authoritative product constants for the RiseX points farmer.

    This contract intentionally contains no arbitrary max spread, max price
    impact, max levels consumed, hidden conservative buffer, or safety margin
    fields. Those market effects belong inside executable VWAP and PnL inputs.
    """

    min_leg_notional_usd: Decimal = Decimal("500")
    min_net_profit_usd: Decimal = Decimal("1")
    live_trading_enabled: bool = False
    points_value_usd: Decimal = Decimal("0")
    expected_airdrop_value_usd: Decimal = Decimal("0")
    leaderboard_rewards_base_pnl_usd: Decimal = Decimal("0")
    unreceived_rebates_usd: Decimal = Decimal("0")
