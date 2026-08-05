"""Order boundary.

RX-000 must not place live orders. This module exists only to reserve the single
execution boundary for future tasks.
"""

from __future__ import annotations


class OrderPlacementDisabled(RuntimeError):
    """Raised when code attempts to place orders in RX-000."""


def send_order(*args: object, **kwargs: object) -> None:
    """Refuse order placement in the walking skeleton."""

    raise OrderPlacementDisabled("Order placement is not implemented in RX-000.")
