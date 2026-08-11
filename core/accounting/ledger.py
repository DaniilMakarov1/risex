"""Append-only ledger contracts and replay helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    EstimatedValue,
    ExecutableQuote,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import CaptureState, RejectReason
from core.domain.state_machine import transition_capture


class LedgerEventType(StrEnum):
    """Accounting-owned append-only event type contract."""

    ROUTE_DECISION_RECORDED = "route_decision"
    PAPER_CAPTURE_OPENED = "paper_capture_opened"
    PAPER_SETTLEMENT_OBSERVED = "paper_settlement_observed"
    PAPER_CAPTURE_CLOSED = "paper_capture_closed"
    PAPER_REJECTION_RECORDED = "paper_rejection_recorded"
    FUNDING_CHECKPOINT_OBSERVED = "funding_checkpoint_observed"
    FUNDING_SETTLEMENT_EVIDENCE_RECORDED = "funding_settlement_evidence_recorded"
    FUNDING_SETTLEMENT_VERIFICATION_RECORDED = "funding_settlement_verification_recorded"
    LEDGER_RECONCILIATION_RECORDED = "ledger_reconciliation_recorded"
    LIVE_GATE_EVIDENCE_BUNDLE_RECORDED = "live_gate_evidence_bundle_recorded"


def _event_type_value(event_type: str | LedgerEventType) -> str:
    if isinstance(event_type, LedgerEventType):
        return event_type.value
    return str(event_type)


def _immutable_payload_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _immutable_payload_value(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_immutable_payload_value(item) for item in value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def freeze_ledger_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable, accounting-safe payload snapshot."""

    return _immutable_payload_value(payload)


def ledger_payload_to_jsonable(value: Any) -> Any:
    """Convert an immutable ledger payload value to deterministic JSON-compatible data."""

    if isinstance(value, Mapping):
        return {str(key): ledger_payload_to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [ledger_payload_to_jsonable(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    """Immutable event record."""

    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("ledger event sequence must be positive")
        validate_timezone_aware_datetime(self.recorded_at, "recorded_at")
        object.__setattr__(self, "event_type", _event_type_value(self.event_type))
        object.__setattr__(self, "payload", freeze_ledger_payload(self.payload))


class Ledger(Protocol):
    """Minimal append-only ledger writer/reader contract."""

    def append(
        self,
        *,
        event_type: str | LedgerEventType,
        payload: Mapping[str, Any],
        recorded_at: datetime | None = None,
    ) -> LedgerEvent:
        """Append one immutable event."""

    def records(self) -> tuple[LedgerEvent, ...]:
        """Return events in append sequence order."""


class InMemoryLedger:
    """Small append-only ledger.

    It exposes immutable snapshots of records and does not support update or delete.
    """

    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []

    def append(
        self,
        *,
        event_type: str | LedgerEventType,
        payload: Mapping[str, Any],
        recorded_at: datetime | None = None,
    ) -> LedgerEvent:
        event = LedgerEvent(
            sequence=len(self._events) + 1,
            event_type=_event_type_value(event_type),
            payload=payload,
            recorded_at=recorded_at or datetime.now(UTC),
        )
        self._events.append(event)
        return event

    def records(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)


def append_decision_event(
    ledger: Ledger,
    decision: DecisionResult,
    *,
    recorded_at: datetime | None = None,
) -> LedgerEvent:
    """Write a route decision event through the ledger module only."""

    return ledger.append(
        event_type=LedgerEventType.ROUTE_DECISION_RECORDED,
        payload={
            "route_id": decision.route_id,
            "mode": decision.mode.value,
            "status": decision.status.value,
            "reasons": tuple(reason.value for reason in decision.reasons),
            "net_profit_usd": str(decision.net_profit_usd) if decision.net_profit_usd is not None else None,
            "has_capture_plan": decision.capture_plan is not None,
        },
        recorded_at=recorded_at or decision.decided_at,
    )


def _capture_payload(capture: Capture, state_path: Sequence[CaptureState]) -> Mapping[str, Any]:
    return {
        "capture_id": capture.capture_id,
        "route_id": capture.route_id,
        "settlement_time": capture.settlement_time.isoformat(),
        "state": capture.state.value,
        "state_path": tuple(state.value for state in state_path),
    }


def append_paper_capture_opened_event(
    ledger: Ledger,
    *,
    capture: Capture,
    state_path: Sequence[CaptureState],
    recorded_at: datetime,
    paper_result_explanation: Mapping[str, Any] | None = None,
) -> LedgerEvent:
    """Record a fake paper capture opening lifecycle event."""

    payload = dict(_capture_payload(capture, state_path))
    if paper_result_explanation is not None:
        payload["paper_result_explanation"] = paper_result_explanation

    return ledger.append(
        event_type=LedgerEventType.PAPER_CAPTURE_OPENED,
        payload=payload,
        recorded_at=recorded_at,
    )


def append_paper_settlement_observed_event(
    ledger: Ledger,
    *,
    capture: Capture,
    state_path: Sequence[CaptureState],
    recorded_at: datetime,
) -> LedgerEvent:
    """Record a fake paper settlement observation lifecycle event."""

    return ledger.append(
        event_type=LedgerEventType.PAPER_SETTLEMENT_OBSERVED,
        payload=_capture_payload(capture, state_path),
        recorded_at=recorded_at,
    )


def append_paper_capture_closed_event(
    ledger: Ledger,
    *,
    capture: Capture,
    state_path: Sequence[CaptureState],
    recorded_at: datetime,
) -> LedgerEvent:
    """Record a fake paper capture close lifecycle event."""

    return ledger.append(
        event_type=LedgerEventType.PAPER_CAPTURE_CLOSED,
        payload=_capture_payload(capture, state_path),
        recorded_at=recorded_at,
    )


def append_paper_rejection_event(
    ledger: Ledger,
    decision: DecisionResult,
    *,
    recorded_at: datetime | None = None,
    paper_result_explanation: Mapping[str, Any] | None = None,
) -> LedgerEvent:
    """Record that a route decision did not start fake paper capture execution."""

    payload: dict[str, Any] = {
        "route_id": decision.route_id,
        "mode": decision.mode.value,
        "status": decision.status.value,
        "reasons": tuple(reason.value for reason in decision.reasons),
        "capture_started": False,
    }
    if paper_result_explanation is not None:
        payload["paper_result_explanation"] = paper_result_explanation

    return ledger.append(
        event_type=LedgerEventType.PAPER_REJECTION_RECORDED,
        payload=payload,
        recorded_at=recorded_at or decision.decided_at,
    )


def _estimated_value_payload(value: EstimatedValue) -> Mapping[str, Any]:
    if not isinstance(value, EstimatedValue):
        raise ValueError("funding settlement evidence requires EstimatedValue inputs")
    return {
        "value": str(value.value) if value.value is not None else None,
        "source": value.source.value,
        "description": value.description,
        "metadata": dict(value.metadata),
    }


def _validate_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def append_funding_checkpoint_observed_event(
    ledger: Ledger,
    *,
    capture_id: str,
    route_id: str,
    checkpoint: str,
    settlement_time: datetime,
    observed_at: datetime,
    target_notional_usd: Decimal,
    risex_expected_funding_usd: EstimatedValue,
    hedge_expected_funding_usd: EstimatedValue,
    recorded_at: datetime | None = None,
) -> LedgerEvent:
    """Record one required fake pre-settlement funding checkpoint."""

    _validate_non_empty(capture_id, "capture_id")
    _validate_non_empty(route_id, "route_id")
    _validate_non_empty(checkpoint, "checkpoint")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(observed_at, "observed_at")
    if target_notional_usd <= Decimal("0"):
        raise ValueError("target_notional_usd must be positive")

    return ledger.append(
        event_type=LedgerEventType.FUNDING_CHECKPOINT_OBSERVED,
        payload={
            "capture_id": capture_id,
            "route_id": route_id,
            "checkpoint": checkpoint,
            "settlement_time": settlement_time.isoformat(),
            "observed_at": observed_at.isoformat(),
            "target_notional_usd": str(target_notional_usd),
            "risex_expected_funding_usd": _estimated_value_payload(risex_expected_funding_usd),
            "hedge_expected_funding_usd": _estimated_value_payload(hedge_expected_funding_usd),
        },
        recorded_at=recorded_at or observed_at,
    )


def append_funding_settlement_evidence_event(
    ledger: Ledger,
    *,
    capture_id: str,
    route_id: str,
    settlement_time: datetime,
    observed_at: datetime,
    actual_risex_funding_usd: EstimatedValue,
    actual_hedge_funding_usd: EstimatedValue,
    actual_risex_notional_usd: EstimatedValue,
    actual_hedge_notional_usd: EstimatedValue,
    recorded_at: datetime | None = None,
) -> LedgerEvent:
    """Record deterministic fake observed funding and notional at settlement."""

    _validate_non_empty(capture_id, "capture_id")
    _validate_non_empty(route_id, "route_id")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(observed_at, "observed_at")

    return ledger.append(
        event_type=LedgerEventType.FUNDING_SETTLEMENT_EVIDENCE_RECORDED,
        payload={
            "capture_id": capture_id,
            "route_id": route_id,
            "settlement_time": settlement_time.isoformat(),
            "observed_at": observed_at.isoformat(),
            "actual_risex_funding_usd": _estimated_value_payload(actual_risex_funding_usd),
            "actual_hedge_funding_usd": _estimated_value_payload(actual_hedge_funding_usd),
            "actual_risex_notional_usd": _estimated_value_payload(actual_risex_notional_usd),
            "actual_hedge_notional_usd": _estimated_value_payload(actual_hedge_notional_usd),
        },
        recorded_at=recorded_at or observed_at,
    )


def append_funding_settlement_verification_event(
    ledger: Ledger,
    *,
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
    verified: bool,
    reasons: Sequence[str | Enum],
    required_checkpoints: Sequence[str | Enum],
    checkpoint_event_sequences: Sequence[int],
    settlement_event_sequence: int | None,
    recorded_at: datetime,
) -> LedgerEvent:
    """Record one deterministic funding settlement verification result."""

    _validate_non_empty(capture_id, "capture_id")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(recorded_at, "recorded_at")

    return ledger.append(
        event_type=LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED,
        payload={
            "capture_id": capture_id,
            "route_id": route_id,
            "settlement_time": settlement_time.isoformat(),
            "verified": verified,
            "reasons": tuple(reason.value if isinstance(reason, Enum) else str(reason) for reason in reasons),
            "required_checkpoints": tuple(
                checkpoint.value if isinstance(checkpoint, Enum) else str(checkpoint)
                for checkpoint in required_checkpoints
            ),
            "checkpoint_event_sequences": tuple(checkpoint_event_sequences),
            "settlement_event_sequence": settlement_event_sequence,
        },
        recorded_at=recorded_at,
    )


def append_ledger_reconciliation_event(
    ledger: Ledger,
    *,
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
    reconciled: bool,
    reasons: Sequence[str | Enum],
    route_decision_event_sequence: int | None,
    paper_event_sequences: Sequence[int],
    funding_verification_event_sequence: int | None,
    checked_event_sequences: Sequence[int],
    event_count: int,
    last_sequence: int | None,
    recorded_at: datetime,
) -> LedgerEvent:
    """Record one deterministic ledger reconciliation result."""

    _validate_non_empty(capture_id, "capture_id")
    if route_id is not None:
        _validate_non_empty(route_id, "route_id")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(recorded_at, "recorded_at")
    if event_count < 0:
        raise ValueError("event_count cannot be negative")
    if event_count == 0 and last_sequence is not None:
        raise ValueError("last_sequence must be None when event_count is zero")
    if event_count > 0 and (last_sequence is None or last_sequence <= 0):
        raise ValueError("last_sequence must be positive when event_count is positive")

    return ledger.append(
        event_type=LedgerEventType.LEDGER_RECONCILIATION_RECORDED,
        payload={
            "capture_id": capture_id,
            "route_id": route_id,
            "settlement_time": settlement_time.isoformat(),
            "reconciled": reconciled,
            "reasons": tuple(reason.value if isinstance(reason, Enum) else str(reason) for reason in reasons),
            "route_decision_event_sequence": route_decision_event_sequence,
            "paper_event_sequences": tuple(paper_event_sequences),
            "funding_verification_event_sequence": funding_verification_event_sequence,
            "checked_event_sequences": tuple(checked_event_sequences),
            "event_count": event_count,
            "last_sequence": last_sequence,
        },
        recorded_at=recorded_at,
    )


def _decimal_payload(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _executable_quote_payload(quote: ExecutableQuote) -> Mapping[str, Any]:
    if not isinstance(quote, ExecutableQuote):
        raise ValueError("live gate evidence bundle requires ExecutableQuote inputs")
    return {
        "venue": quote.venue,
        "symbol": quote.symbol,
        "side": quote.side,
        "target_notional_usd": str(quote.target_notional_usd),
        "vwap_price": _decimal_payload(quote.vwap_price),
        "executable": quote.executable,
        "source": quote.source.value,
        "consumed_base_quantity": _decimal_payload(quote.consumed_base_quantity),
        "consumed_levels": quote.consumed_levels,
        "notional_filled_usd": _decimal_payload(quote.notional_filled_usd),
        "best_price": _decimal_payload(quote.best_price),
        "worst_price": _decimal_payload(quote.worst_price),
        "price_impact_bps": _decimal_payload(quote.price_impact_bps),
    }


def _capture_plan_evidence_payload(evidence: CapturePlanFreshnessEvidence) -> Mapping[str, Any]:
    if not isinstance(evidence, CapturePlanFreshnessEvidence):
        raise ValueError("live gate evidence bundle requires CapturePlanFreshnessEvidence inputs")
    return {
        "plan_id": evidence.plan_id,
        "plan_version": evidence.plan_version,
        "capture_id": evidence.capture_id,
        "route_id": evidence.route_id,
        "settlement_time": evidence.settlement_time.isoformat(),
        "planned_at": evidence.planned_at.isoformat(),
        "valid_until": evidence.valid_until.isoformat(),
        "source": evidence.source.value,
        "ledger_reconciliation_event_sequence": evidence.ledger_reconciliation_event_sequence,
    }


def _execution_capability_evidence_payload(
    evidence: ExecutionCapabilityEvidence,
) -> Mapping[str, Any]:
    if not isinstance(evidence, ExecutionCapabilityEvidence):
        raise ValueError("live gate evidence bundle requires ExecutionCapabilityEvidence inputs")
    return {
        "capture_id": evidence.capture_id,
        "route_id": evidence.route_id,
        "settlement_time": evidence.settlement_time.isoformat(),
        "checked_at": evidence.checked_at.isoformat(),
        "valid_until": evidence.valid_until.isoformat(),
        "source": evidence.source.value,
        "risex_entry_quote": _executable_quote_payload(evidence.risex_entry_quote),
        "hedge_entry_quote": _executable_quote_payload(evidence.hedge_entry_quote),
        "risex_estimated_exit_quote": _executable_quote_payload(
            evidence.risex_estimated_exit_quote
        ),
        "hedge_estimated_exit_quote": _executable_quote_payload(
            evidence.hedge_estimated_exit_quote
        ),
    }


def _live_gate_evidence_bundle_payload(bundle: LiveGateEvidenceBundle) -> Mapping[str, Any]:
    if not isinstance(bundle, LiveGateEvidenceBundle):
        raise ValueError("live_gate_evidence_bundle must be a LiveGateEvidenceBundle")
    return {
        "capture_id": bundle.capture_id,
        "route_id": bundle.route_id,
        "settlement_time": bundle.settlement_time.isoformat(),
        "funding_settlement_verified": bundle.funding_settlement_verified,
        "ledger_explicitly_reconciled": bundle.ledger_explicitly_reconciled,
        "capture_plan_evidence": tuple(
            _capture_plan_evidence_payload(evidence)
            for evidence in bundle.capture_plan_evidence
        ),
        "execution_capability_evidence": tuple(
            _execution_capability_evidence_payload(evidence)
            for evidence in bundle.execution_capability_evidence
        ),
    }


def _route_payload(route: RouteCandidate) -> Mapping[str, Any]:
    if not isinstance(route, RouteCandidate):
        raise ValueError("route must be a RouteCandidate")
    if route.target_notional_usd <= Decimal("0"):
        raise ValueError("route.target_notional_usd must be positive")
    return {
        "route_id": route.route_id,
        "capture_id": route.capture_id,
        "risex_venue": route.risex_venue,
        "risex_symbol": route.risex_symbol,
        "risex_entry_side": route.risex_entry_side,
        "hedge_venue": route.hedge_venue,
        "hedge_symbol": route.hedge_symbol,
        "hedge_entry_side": route.hedge_entry_side,
        "target_notional_usd": str(route.target_notional_usd),
    }


def _validate_positive_sequence(value: int, field_name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")


def append_live_gate_evidence_bundle_event(
    ledger: Ledger,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    evaluated_at: datetime,
    live_gate_evidence_bundle: LiveGateEvidenceBundle,
    bundle_check_passed: bool,
    bundle_check_reason: RejectReason | None,
    route_decision_event_sequence: int,
    funding_verification_event_sequence: int,
    ledger_reconciliation_event_sequence: int,
    recorded_at: datetime,
) -> LedgerEvent:
    """Record one deterministic fake live-gate evidence bundle check result."""

    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(evaluated_at, "evaluated_at")
    validate_timezone_aware_datetime(recorded_at, "recorded_at")
    if type(bundle_check_passed) is not bool:
        raise ValueError("bundle_check_passed must be a bool")
    if bundle_check_passed and bundle_check_reason is not None:
        raise ValueError("bundle_check_reason must be None when bundle_check_passed is true")
    if not bundle_check_passed and bundle_check_reason is None:
        raise ValueError("bundle_check_reason is required when bundle_check_passed is false")
    if bundle_check_reason is not None and not isinstance(bundle_check_reason, RejectReason):
        raise ValueError("bundle_check_reason must be a RejectReason or None")
    _validate_positive_sequence(route_decision_event_sequence, "route_decision_event_sequence")
    _validate_positive_sequence(
        funding_verification_event_sequence,
        "funding_verification_event_sequence",
    )
    _validate_positive_sequence(
        ledger_reconciliation_event_sequence,
        "ledger_reconciliation_event_sequence",
    )

    return ledger.append(
        event_type=LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED,
        payload={
            "capture_id": route.capture_id,
            "route_id": route.route_id,
            "settlement_time": settlement_time.isoformat(),
            "evaluated_at": evaluated_at.isoformat(),
            "route": _route_payload(route),
            "live_gate_evidence_bundle": _live_gate_evidence_bundle_payload(
                live_gate_evidence_bundle
            ),
            "bundle_check_passed": bundle_check_passed,
            "bundle_check_reason": (
                bundle_check_reason.value if bundle_check_reason is not None else None
            ),
            "route_decision_event_sequence": route_decision_event_sequence,
            "funding_verification_event_sequence": funding_verification_event_sequence,
            "ledger_reconciliation_event_sequence": ledger_reconciliation_event_sequence,
        },
        recorded_at=recorded_at,
    )


@dataclass(frozen=True, slots=True)
class ReplayedPaperCapture:
    """Final replayed Capture state plus the ledger event sequence that produced it."""

    capture: Capture
    event_sequences: tuple[int, ...]


def _payload_state_path(event: LedgerEvent) -> tuple[CaptureState, ...]:
    raw_state_path = event.payload.get("state_path")
    if not isinstance(raw_state_path, tuple) or not raw_state_path:
        raise ValueError("paper lifecycle events require a non-empty state_path")
    return tuple(CaptureState(state) for state in raw_state_path)


def _payload_settlement_time(event: LedgerEvent) -> datetime:
    raw_settlement_time = event.payload.get("settlement_time")
    if not isinstance(raw_settlement_time, str):
        raise ValueError("paper lifecycle events require settlement_time")
    settlement_time = datetime.fromisoformat(raw_settlement_time)
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    return settlement_time


def replay_paper_captures(events: Sequence[LedgerEvent]) -> tuple[ReplayedPaperCapture, ...]:
    """Replay append-only paper lifecycle events into deterministic final Capture states."""

    replayed: dict[str, tuple[Capture, list[int]]] = {}
    for event in sorted(events, key=lambda item: item.sequence):
        if event.event_type not in {
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        }:
            continue

        capture_id = event.payload.get("capture_id")
        route_id = event.payload.get("route_id")
        if not isinstance(capture_id, str) or not isinstance(route_id, str):
            raise ValueError("paper lifecycle events require capture_id and route_id")

        state_path = _payload_state_path(event)
        settlement_time = _payload_settlement_time(event)
        if capture_id in replayed:
            capture, sequences = replayed[capture_id]
            if capture.route_id != route_id or capture.settlement_time != settlement_time:
                raise ValueError("paper lifecycle replay found inconsistent capture identity")
            if capture.state is not state_path[0]:
                raise ValueError("paper lifecycle replay found a broken state path")
        else:
            capture = Capture(
                capture_id=capture_id,
                route_id=route_id,
                settlement_time=settlement_time,
                state=state_path[0],
            )
            sequences = []

        for target_state in state_path[1:]:
            capture = transition_capture(capture, target_state)

        event_state = event.payload.get("state")
        if event_state != capture.state.value:
            raise ValueError("paper lifecycle replay event state does not match state_path")

        sequences.append(event.sequence)
        replayed[capture_id] = (capture, sequences)

    return tuple(
        ReplayedPaperCapture(capture=capture, event_sequences=tuple(sequences))
        for capture, sequences in replayed.values()
    )
