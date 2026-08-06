from dataclasses import replace
from decimal import Decimal

import pytest

from core.domain.contracts import ExecutableQuote, OrderBook, OrderBookLevel
from core.domain.enums import ValueSource
from core.economics.errors import EconomicsInputError
from core.economics.liquidity import calculate_executable_quote, calculate_quote_roundtrip_cost_usd


def _executable_quote(*, side: str, venue: str = "RiseX", symbol: str = "BTC-PERP") -> ExecutableQuote:
    return ExecutableQuote(
        venue=venue,
        symbol=symbol,
        side=side,
        target_notional_usd=Decimal("500"),
        vwap_price=Decimal("100"),
        executable=True,
        source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
    )


def test_vwap_consumes_asks_for_buy_target_notional() -> None:
    order_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(),
        asks=(
            OrderBookLevel(price=Decimal("100"), size=Decimal("3")),
            OrderBookLevel(price=Decimal("101"), size=Decimal("3")),
        ),
    )

    quote = calculate_executable_quote(
        order_book=order_book,
        side="buy",
        target_notional_usd=Decimal("500"),
    )

    expected_base_quantity = Decimal("3") + (Decimal("200") / Decimal("101"))
    assert quote.executable is True
    assert quote.consumed_levels == 2
    assert quote.notional_filled_usd == Decimal("500")
    assert quote.consumed_base_quantity == expected_base_quantity
    assert quote.vwap_price == Decimal("500") / expected_base_quantity
    assert quote.best_price == Decimal("100")
    assert quote.worst_price == Decimal("101")


def test_vwap_consumes_bids_for_sell_target_notional() -> None:
    order_book = OrderBook(
        venue="Hyperliquid",
        symbol="BTC",
        bids=(
            OrderBookLevel(price=Decimal("101"), size=Decimal("2")),
            OrderBookLevel(price=Decimal("100"), size=Decimal("5")),
        ),
        asks=(),
    )

    quote = calculate_executable_quote(
        order_book=order_book,
        side="sell",
        target_notional_usd=Decimal("500"),
    )

    expected_base_quantity = Decimal("2") + (Decimal("298") / Decimal("100"))
    assert quote.executable is True
    assert quote.consumed_levels == 2
    assert quote.notional_filled_usd == Decimal("500")
    assert quote.consumed_base_quantity == expected_base_quantity
    assert quote.vwap_price == Decimal("500") / expected_base_quantity


def test_vwap_marks_insufficient_liquidity_as_non_executable() -> None:
    order_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(),
        asks=(OrderBookLevel(price=Decimal("100"), size=Decimal("4")),),
    )

    quote = calculate_executable_quote(
        order_book=order_book,
        side="buy",
        target_notional_usd=Decimal("500"),
    )

    assert quote.executable is False
    assert quote.notional_filled_usd == Decimal("400")
    assert quote.consumed_levels == 1


def test_poor_executable_prices_increase_roundtrip_cost() -> None:
    entry_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(),
        asks=(OrderBookLevel(price=Decimal("100"), size=Decimal("10")),),
    )
    good_exit_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(OrderBookLevel(price=Decimal("99.95"), size=Decimal("10")),),
        asks=(),
    )
    poor_exit_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(OrderBookLevel(price=Decimal("90"), size=Decimal("10")),),
        asks=(),
    )

    entry_quote = calculate_executable_quote(
        order_book=entry_book,
        side="buy",
        target_notional_usd=Decimal("500"),
    )
    good_exit_quote = calculate_executable_quote(
        order_book=good_exit_book,
        side="sell",
        target_notional_usd=Decimal("500"),
    )
    poor_exit_quote = calculate_executable_quote(
        order_book=poor_exit_book,
        side="sell",
        target_notional_usd=Decimal("500"),
    )

    assert calculate_quote_roundtrip_cost_usd(
        entry_quote=entry_quote,
        exit_quote=poor_exit_quote,
    ) > calculate_quote_roundtrip_cost_usd(
        entry_quote=entry_quote,
        exit_quote=good_exit_quote,
    )


@pytest.mark.parametrize(
    ("entry_quote", "exit_quote", "message"),
    (
        (
            _executable_quote(side="buy", venue="RiseX"),
            _executable_quote(side="sell", venue="Hyperliquid"),
            "same venue",
        ),
        (
            _executable_quote(side="buy", symbol="BTC-PERP"),
            _executable_quote(side="sell", symbol="ETH-PERP"),
            "same symbol",
        ),
        (
            _executable_quote(side="buy"),
            _executable_quote(side="buy"),
            "opposite sides",
        ),
        (
            _executable_quote(side="buy"),
            replace(_executable_quote(side="sell"), target_notional_usd=Decimal("1000")),
            "same target notional",
        ),
        (
            replace(_executable_quote(side="buy"), executable=False, vwap_price=None),
            _executable_quote(side="sell"),
            "entry_quote must be executable with vwap_price",
        ),
        (
            _executable_quote(side="buy"),
            replace(_executable_quote(side="sell"), executable=False, vwap_price=None),
            "exit_quote must be executable with vwap_price",
        ),
    ),
)
def test_roundtrip_cost_rejects_mismatched_quote_pairs(
    entry_quote: ExecutableQuote,
    exit_quote: ExecutableQuote,
    message: str,
) -> None:
    with pytest.raises(EconomicsInputError, match=message):
        calculate_quote_roundtrip_cost_usd(entry_quote=entry_quote, exit_quote=exit_quote)
