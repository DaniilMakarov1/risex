"""Risk gates live here only."""

from __future__ import annotations

from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import ExecutableQuote, OrderSide, RouteCandidate, VenueSnapshot
from core.domain.enums import RejectReason, ValueSource
from core.economics.liquidity import quote_is_executable_for_notional


REQUIRED_ORDERBOOK_QUOTE_SOURCE = ValueSource.ESTIMATED_FROM_ORDERBOOK
VALID_ORDER_SIDES = frozenset({"buy", "sell"})


def _side_is_valid(side: str) -> bool:
    return side in VALID_ORDER_SIDES


def _opposite_side(side: OrderSide) -> OrderSide | None:
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    return None


def _quote_matches_leg(quote: ExecutableQuote, *, venue: str, symbol: str) -> bool:
    return quote.venue == venue and quote.symbol == symbol


def check_min_leg_notional(route: RouteCandidate, rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """Reject only if the route cannot meet the configured minimum notional."""

    if route.target_notional_usd < rules.min_leg_notional_usd:
        return False, RejectReason.MIN_LEG_NOTIONAL_NOT_MET
    return True, None


def check_route_snapshot_alignment(
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> tuple[bool, RejectReason | None]:
    """Reject snapshots that do not represent the authoritative route contract."""

    if not _side_is_valid(route.risex_entry_side) or not _side_is_valid(route.hedge_entry_side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if route.risex_entry_side == route.hedge_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    risex_entry = snapshot.risex_entry_quote
    risex_exit = snapshot.risex_estimated_exit_quote
    hedge_entry = snapshot.hedge_entry_quote
    hedge_exit = snapshot.hedge_estimated_exit_quote

    if not _quote_matches_leg(risex_entry, venue=route.risex_venue, symbol=route.risex_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(risex_exit, venue=route.risex_venue, symbol=route.risex_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_entry, venue=route.hedge_venue, symbol=route.hedge_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_exit, venue=route.hedge_venue, symbol=route.hedge_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    if risex_entry.side != route.risex_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if hedge_entry.side != route.hedge_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if risex_exit.side != _opposite_side(risex_entry.side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if hedge_exit.side != _opposite_side(hedge_entry.side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    for quote in snapshot.executable_quotes():
        if quote.target_notional_usd != route.target_notional_usd:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if quote.source is not REQUIRED_ORDERBOOK_QUOTE_SOURCE:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    if not _quote_matches_leg(risex_entry, venue=risex_exit.venue, symbol=risex_exit.symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_entry, venue=hedge_exit.venue, symbol=hedge_exit.symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

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
    """Live capture plans remain blocked until future live gates are implemented."""

    if not rules.live_trading_enabled:
        return False, RejectReason.LIVE_TRADING_DISABLED
    return False, RejectReason.LIVE_GATES_NOT_IMPLEMENTED
