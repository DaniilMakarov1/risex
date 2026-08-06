"""Liquidity and VWAP calculations live here only."""

from __future__ import annotations

from decimal import Decimal

from core.domain.contracts import (
    ExecutableQuote,
    OrderBook,
    OrderBookLevel,
    OrderSide,
    VALID_ORDER_SIDES,
    VenueSnapshot,
    validate_order_side,
)
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError


BPS = Decimal("10000")


def _levels_for_side(order_book: OrderBook, side: OrderSide) -> tuple[OrderBookLevel, ...]:
    validate_order_side(side)
    if side == "buy":
        return tuple(sorted(order_book.asks, key=lambda level: level.price))
    return tuple(sorted(order_book.bids, key=lambda level: level.price, reverse=True))


def calculate_executable_quote(
    *,
    order_book: OrderBook,
    side: OrderSide,
    target_notional_usd: Decimal,
) -> ExecutableQuote:
    """Calculate a source-aware executable VWAP quote from order-book levels."""

    if target_notional_usd <= Decimal("0"):
        raise ValueError("target_notional_usd must be positive")

    remaining_notional = target_notional_usd
    filled_notional = Decimal("0")
    consumed_base_quantity = Decimal("0")
    consumed_levels = 0
    best_price: Decimal | None = None
    worst_price: Decimal | None = None

    for level in _levels_for_side(order_book, side):
        if remaining_notional <= Decimal("0"):
            break

        level_notional = level.price * level.size
        fill_notional = min(level_notional, remaining_notional)
        if fill_notional <= Decimal("0"):
            continue

        if best_price is None:
            best_price = level.price
        worst_price = level.price
        consumed_levels += 1
        filled_notional += fill_notional
        consumed_base_quantity += fill_notional / level.price
        remaining_notional -= fill_notional

    executable = remaining_notional <= Decimal("0")
    vwap_price = (
        filled_notional / consumed_base_quantity
        if consumed_base_quantity > Decimal("0")
        else None
    )
    price_impact_bps = (
        (abs(worst_price - best_price) / best_price) * BPS
        if best_price is not None and worst_price is not None
        else None
    )

    return ExecutableQuote(
        venue=order_book.venue,
        symbol=order_book.symbol,
        side=side,
        target_notional_usd=target_notional_usd,
        vwap_price=vwap_price,
        executable=executable,
        source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
        consumed_base_quantity=consumed_base_quantity,
        consumed_levels=consumed_levels,
        notional_filled_usd=filled_notional,
        best_price=best_price,
        worst_price=worst_price,
        price_impact_bps=price_impact_bps,
    )


def quote_is_executable_for_notional(
    quote: ExecutableQuote,
    *,
    min_leg_notional_usd: Decimal,
) -> bool:
    """Check technical executability for the configured target notional.

    This is not a spread, price impact, or slippage filter. It only checks whether
    the quote fully executes its own target notional and still meets the product
    minimum notional.
    """

    notional_filled = quote.notional_filled_usd or Decimal("0")
    consumed_base_quantity = quote.consumed_base_quantity or Decimal("0")
    return (
        quote.executable
        and quote.vwap_price is not None
        and quote.vwap_price > Decimal("0")
        and quote.side in VALID_ORDER_SIDES
        and quote.target_notional_usd >= min_leg_notional_usd
        and notional_filled >= quote.target_notional_usd
        and consumed_base_quantity > Decimal("0")
    )


def calculate_quote_roundtrip_cost_usd(
    *,
    entry_quote: ExecutableQuote,
    exit_quote: ExecutableQuote,
) -> Decimal:
    """Estimate immediate unwind cost from current executable VWAP quotes."""

    if not entry_quote.executable or entry_quote.vwap_price is None:
        raise EconomicsInputError("entry_quote must be executable with vwap_price")
    if not exit_quote.executable or exit_quote.vwap_price is None:
        raise EconomicsInputError("exit_quote must be executable with vwap_price")
    if entry_quote.side not in VALID_ORDER_SIDES:
        raise EconomicsInputError("entry_quote side must be buy or sell")
    if exit_quote.side not in VALID_ORDER_SIDES:
        raise EconomicsInputError("exit_quote side must be buy or sell")
    if entry_quote.venue != exit_quote.venue:
        raise EconomicsInputError("entry and exit quotes must use the same venue")
    if entry_quote.symbol != exit_quote.symbol:
        raise EconomicsInputError("entry and exit quotes must use the same symbol")
    if entry_quote.side == exit_quote.side:
        raise EconomicsInputError("entry and exit quotes must use opposite sides")
    if entry_quote.target_notional_usd != exit_quote.target_notional_usd:
        raise EconomicsInputError("entry and exit quotes must use the same target notional")
    if entry_quote.target_notional_usd <= Decimal("0"):
        raise EconomicsInputError("entry_quote.target_notional_usd must be positive")
    if not quote_is_executable_for_notional(
        entry_quote,
        min_leg_notional_usd=entry_quote.target_notional_usd,
    ):
        raise EconomicsInputError("entry_quote must fully fill target_notional_usd")
    if not quote_is_executable_for_notional(
        exit_quote,
        min_leg_notional_usd=exit_quote.target_notional_usd,
    ):
        raise EconomicsInputError("exit_quote must fully fill target_notional_usd")

    if entry_quote.side == "buy":
        price_delta = entry_quote.vwap_price - exit_quote.vwap_price
    else:
        price_delta = exit_quote.vwap_price - entry_quote.vwap_price
    return (price_delta / entry_quote.vwap_price) * entry_quote.target_notional_usd


def calculate_total_simulated_roundtrip_cost_usd(snapshot: VenueSnapshot) -> Decimal:
    """Calculate simulated immediate roundtrip cost for both legs."""

    risex_cost = calculate_quote_roundtrip_cost_usd(
        entry_quote=snapshot.risex_entry_quote,
        exit_quote=snapshot.risex_estimated_exit_quote,
    )
    hedge_cost = calculate_quote_roundtrip_cost_usd(
        entry_quote=snapshot.hedge_entry_quote,
        exit_quote=snapshot.hedge_estimated_exit_quote,
    )
    return risex_cost + hedge_cost
