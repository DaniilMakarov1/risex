"""Capture-centric domain contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Literal

from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus, ValueSource

OrderSide = Literal["buy", "sell"]


@dataclass(frozen=True, slots=True)
class OrderBookLevel:
    """One normalized price level where size is base asset quantity."""

    price: Decimal
    size: Decimal

    def __post_init__(self) -> None:
        if self.price <= Decimal("0"):
            raise ValueError("order book level price must be positive")
        if self.size <= Decimal("0"):
            raise ValueError("order book level size must be positive")


@dataclass(frozen=True, slots=True)
class OrderBook:
    """Normalized order book used by offline VWAP calculations."""

    venue: str
    symbol: str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "bids", tuple(self.bids))
        object.__setattr__(self, "asks", tuple(self.asks))


@dataclass(frozen=True, slots=True)
class Capture:
    """One funding settlement opportunity.

    The lifecycle state is separate from route eligibility status.
    """

    capture_id: str
    route_id: str
    settlement_time: datetime
    state: CaptureState = CaptureState.DISCOVERED


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    """A potential RiseX funding capture route with one hedge venue."""

    route_id: str
    capture_id: str
    risex_symbol: str
    hedge_venue: str
    hedge_symbol: str
    target_notional_usd: Decimal


@dataclass(frozen=True, slots=True)
class ExecutableQuote:
    """Current executable VWAP quote for a target notional on one side of a book."""

    venue: str
    symbol: str
    side: OrderSide
    target_notional_usd: Decimal
    vwap_price: Decimal | None
    executable: bool
    source: ValueSource = ValueSource.ESTIMATED_FROM_ORDERBOOK
    consumed_base_quantity: Decimal | None = None
    consumed_levels: int = 0
    notional_filled_usd: Decimal | None = None
    best_price: Decimal | None = None
    worst_price: Decimal | None = None
    price_impact_bps: Decimal | None = None

    def __post_init__(self) -> None:
        if self.target_notional_usd <= Decimal("0"):
            raise ValueError("target_notional_usd must be positive")
        if self.vwap_price is not None and self.vwap_price <= Decimal("0"):
            raise ValueError("vwap_price must be positive when provided")
        if self.executable and self.vwap_price is None:
            raise ValueError("executable quotes require vwap_price")
        if self.source is ValueSource.UNKNOWN:
            raise ValueError("executable quote source cannot be UNKNOWN")

        notional_filled = self.notional_filled_usd
        if notional_filled is None:
            notional_filled = self.target_notional_usd if self.executable else Decimal("0")
            object.__setattr__(self, "notional_filled_usd", notional_filled)
        if notional_filled < Decimal("0"):
            raise ValueError("notional_filled_usd cannot be negative")

        consumed_base = self.consumed_base_quantity
        if consumed_base is None:
            if self.executable and self.vwap_price is not None:
                consumed_base = self.target_notional_usd / self.vwap_price
            else:
                consumed_base = Decimal("0")
            object.__setattr__(self, "consumed_base_quantity", consumed_base)
        if consumed_base < Decimal("0"):
            raise ValueError("consumed_base_quantity cannot be negative")
        if self.consumed_levels < 0:
            raise ValueError("consumed_levels cannot be negative")
        if self.price_impact_bps is not None and self.price_impact_bps < Decimal("0"):
            raise ValueError("price_impact_bps cannot be negative")


@dataclass(frozen=True, slots=True)
class EstimatedValue:
    """A numeric value with an explicit source.

    UNKNOWN values intentionally carry no numeric fallback. Callers must choose
    a source-aware default upstream instead of silently treating UNKNOWN as zero.
    """

    value: Decimal | None
    source: ValueSource
    description: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        if self.source is ValueSource.UNKNOWN and self.value is not None:
            raise ValueError("UNKNOWN values must not carry a numeric value")
        if self.source is not ValueSource.UNKNOWN and self.value is None:
            raise ValueError("Known value sources require a numeric value")

    def require_value(self) -> Decimal:
        """Return the numeric value, rejecting UNKNOWN instead of returning zero."""

        if self.source is ValueSource.UNKNOWN or self.value is None:
            raise ValueError("UNKNOWN values must not silently become zero")
        return self.value


@dataclass(frozen=True, slots=True)
class FeeComponent:
    """One source-aware fee input in USD."""

    name: str
    amount_usd: EstimatedValue
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class FeeModel:
    """Source-aware fee model for the current entry and immediate unwind path."""

    components: tuple[FeeComponent, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", tuple(self.components))


@dataclass(frozen=True, slots=True)
class FundingSnapshot:
    """Source-aware expected funding cash flows for one capture opportunity."""

    risex_funding_usd: EstimatedValue
    hedge_funding_usd: EstimatedValue


@dataclass(frozen=True, slots=True)
class VenueSnapshot:
    """Fake normalized snapshot used by the non-trading walking skeleton."""

    captured_at: datetime
    risex_entry_quote: ExecutableQuote
    hedge_entry_quote: ExecutableQuote
    risex_estimated_exit_quote: ExecutableQuote
    hedge_estimated_exit_quote: ExecutableQuote
    funding: FundingSnapshot
    fees: FeeModel

    def executable_quotes(self) -> tuple[ExecutableQuote, ...]:
        return (
            self.risex_entry_quote,
            self.hedge_entry_quote,
            self.risex_estimated_exit_quote,
            self.hedge_estimated_exit_quote,
        )


@dataclass(frozen=True, slots=True)
class CapturePlan:
    """Non-order plan object reserved for future live eligibility work."""

    plan_id: str
    capture: Capture
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Result returned by the single route decision pipeline."""

    route_id: str
    mode: EvaluationMode
    status: RouteStatus
    reasons: tuple[RejectReason, ...]
    net_profit_usd: Decimal | None = None
    entry_ev: Any | None = None
    capture_plan: CapturePlan | None = None
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))
