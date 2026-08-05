"""Fake data for the non-trading walking skeleton."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.domain.contracts import ExecutableQuote, RouteCandidate, VenueSnapshot


def build_fake_route_and_snapshot() -> tuple[RouteCandidate, VenueSnapshot]:
    """Create a profitable fake route using executable VWAP inputs only."""

    target_notional = Decimal("500")
    route = RouteCandidate(
        route_id="fake-risex-hl-btc",
        capture_id="capture-000",
        risex_symbol="BTC-PERP",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        target_notional_usd=target_notional,
    )
    snapshot = VenueSnapshot(
        captured_at=datetime.now(UTC),
        risex_entry_quote=ExecutableQuote(
            venue="RiseX",
            symbol="BTC-PERP",
            side="buy",
            target_notional_usd=target_notional,
            vwap_price=Decimal("100"),
            executable=True,
        ),
        hedge_entry_quote=ExecutableQuote(
            venue="Hyperliquid",
            symbol="BTC",
            side="sell",
            target_notional_usd=target_notional,
            vwap_price=Decimal("100"),
            executable=True,
        ),
        risex_estimated_exit_quote=ExecutableQuote(
            venue="RiseX",
            symbol="BTC-PERP",
            side="sell",
            target_notional_usd=target_notional,
            vwap_price=Decimal("99.95"),
            executable=True,
        ),
        hedge_estimated_exit_quote=ExecutableQuote(
            venue="Hyperliquid",
            symbol="BTC",
            side="buy",
            target_notional_usd=target_notional,
            vwap_price=Decimal("99.95"),
            executable=True,
        ),
        expected_risex_funding_usd=Decimal("3"),
        expected_hedge_funding_usd=Decimal("-0.5"),
        documented_fees_usd=Decimal("0.5"),
    )
    return route, snapshot
