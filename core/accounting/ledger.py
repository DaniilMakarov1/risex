"""Append-only ledger abstraction for RX-000 tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Mapping

from core.domain.contracts import DecisionResult


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    """Immutable event record."""

    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    recorded_at: datetime


class InMemoryLedger:
    """Small append-only ledger used by the walking skeleton.

    It exposes immutable snapshots of records and does not support update or delete.
    """

    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []

    def append(self, *, event_type: str, payload: Mapping[str, Any]) -> LedgerEvent:
        event = LedgerEvent(
            sequence=len(self._events) + 1,
            event_type=event_type,
            payload=MappingProxyType(dict(payload)),
            recorded_at=datetime.now(UTC),
        )
        self._events.append(event)
        return event

    def records(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)


def append_decision_event(ledger: InMemoryLedger, decision: DecisionResult) -> LedgerEvent:
    """Write a route decision event through the ledger module only."""

    return ledger.append(
        event_type="route_decision",
        payload={
            "route_id": decision.route_id,
            "mode": decision.mode.value,
            "status": decision.status.value,
            "reasons": list(decision.reasons),
            "net_profit_usd": str(decision.net_profit_usd) if decision.net_profit_usd is not None else None,
            "has_capture_plan": decision.capture_plan is not None,
        },
    )
