"""Venue adapter interfaces.

RX-000 intentionally ships no real exchange adapters. Future adapters may fetch and
normalize data only; EV, risk, decisions, orders, and ledger writes belong elsewhere.
"""

from __future__ import annotations

from typing import Protocol

from core.domain.contracts import OrderBook


class VenueAdapter(Protocol):
    """Read-only adapter contract for future fake or real venues."""

    name: str

    def fetch_order_book(self, symbol: str) -> OrderBook:
        """Fetch and normalize one venue's order book for one requested symbol."""
