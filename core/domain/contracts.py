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
    vwap_price: Decimal
    executable: bool


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
class VenueSnapshot:
    """Fake normalized snapshot used by the non-trading walking skeleton."""

    captured_at: datetime
    risex_entry_quote: ExecutableQuote
    hedge_entry_quote: ExecutableQuote
    risex_estimated_exit_quote: ExecutableQuote
    hedge_estimated_exit_quote: ExecutableQuote
    expected_risex_funding_usd: Decimal
    expected_hedge_funding_usd: Decimal
    documented_fees_usd: Decimal

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
