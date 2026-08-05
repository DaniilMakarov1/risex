"""Risk gates live here only."""

from __future__ import annotations

from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import RouteCandidate, VenueSnapshot
from core.economics.liquidity import quote_is_executable_for_notional


def check_min_leg_notional(route: RouteCandidate, rules: ProductRules) -> tuple[bool, str | None]:
    """Reject only if the route cannot meet the configured minimum notional."""

    if route.target_notional_usd < rules.min_leg_notional_usd:
        return False, "min_leg_notional_not_met"
    return True, None


def check_snapshot_executability(
    snapshot: VenueSnapshot,
    rules: ProductRules,
) -> tuple[bool, str | None]:
    """Reject only when the provided VWAP quotes cannot execute the required notional."""

    for quote in snapshot.executable_quotes():
        if not quote_is_executable_for_notional(
            quote,
            min_leg_notional_usd=rules.min_leg_notional_usd,
        ):
            return False, f"not_executable_for_min_notional:{quote.venue}:{quote.symbol}:{quote.side}"
    return True, None


def check_min_net_profit(net_profit_usd: Decimal, rules: ProductRules) -> tuple[bool, str | None]:
    """Reject only when explicit EV is below the configured minimum net profit."""

    if net_profit_usd < rules.min_net_profit_usd:
        return False, "min_net_profit_not_met"
    return True, None


def check_live_capture_allowed(rules: ProductRules) -> tuple[bool, str | None]:
    """RX-000 cannot authorize live capture plans."""

    if not rules.live_trading_enabled:
        return False, "live_trading_disabled"
    return False, "live_gates_not_implemented_in_rx_000"
