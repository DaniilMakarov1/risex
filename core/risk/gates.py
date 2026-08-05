"""Risk gates live here only."""

from __future__ import annotations

from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import RouteCandidate, VenueSnapshot
from core.domain.enums import RejectReason
from core.economics.liquidity import quote_is_executable_for_notional


def check_min_leg_notional(route: RouteCandidate, rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """Reject only if the route cannot meet the configured minimum notional."""

    if route.target_notional_usd < rules.min_leg_notional_usd:
        return False, RejectReason.MIN_LEG_NOTIONAL_NOT_MET
    return True, None


def check_snapshot_executability(
    snapshot: VenueSnapshot,
    rules: ProductRules,
) -> tuple[bool, RejectReason | None]:
    """Reject only when the provided VWAP quotes cannot execute the required notional."""

    for quote in snapshot.executable_quotes():
        if not quote_is_executable_for_notional(
            quote,
            min_leg_notional_usd=rules.min_leg_notional_usd,
        ):
            return False, RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL
    return True, None


def check_min_net_profit(net_profit_usd: Decimal, rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """Reject only when explicit EV is below the configured minimum net profit."""

    if net_profit_usd < rules.min_net_profit_usd:
        return False, RejectReason.MIN_NET_PROFIT_NOT_MET
    return True, None


def check_live_capture_allowed(rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """RX-002 cannot authorize live capture plans."""

    if not rules.live_trading_enabled:
        return False, RejectReason.LIVE_TRADING_DISABLED
    return False, RejectReason.LIVE_GATES_NOT_IMPLEMENTED
