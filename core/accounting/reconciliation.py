"""Deterministic offline ledger reconciliation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from core.accounting.ledger import (
    Ledger,
    LedgerEvent,
    LedgerEventType,
    append_ledger_reconciliation_event,
    replay_paper_captures,
)
from core.domain.contracts import validate_timezone_aware_datetime
from core.domain.enums import EvaluationMode, RouteStatus


class LedgerReconciliationReason(StrEnum):
    """Fail-closed reasons for deterministic ledger reconciliation."""

    MISSING_ROUTE_DECISION = "MISSING_ROUTE_DECISION"
    DUPLICATED_ROUTE_DECISION_EVIDENCE = "DUPLICATED_ROUTE_DECISION_EVIDENCE"
    CONTRADICTORY_ROUTE_DECISION_EVIDENCE = "CONTRADICTORY_ROUTE_DECISION_EVIDENCE"
    MISSING_PAPER_LIFECYCLE_EVIDENCE = "MISSING_PAPER_LIFECYCLE_EVIDENCE"
    DUPLICATED_PAPER_LIFECYCLE_EVIDENCE = "DUPLICATED_PAPER_LIFECYCLE_EVIDENCE"
    PAPER_REPLAY_FAILED = "PAPER_REPLAY_FAILED"
    MISSING_FUNDING_SETTLEMENT_VERIFICATION = "MISSING_FUNDING_SETTLEMENT_VERIFICATION"
    DUPLICATED_FUNDING_SETTLEMENT_VERIFICATION = "DUPLICATED_FUNDING_SETTLEMENT_VERIFICATION"
    FUNDING_SETTLEMENT_NOT_VERIFIED = "FUNDING_SETTLEMENT_NOT_VERIFIED"
    MISSING_FUNDING_SETTLEMENT_EVIDENCE = "MISSING_FUNDING_SETTLEMENT_EVIDENCE"
    DUPLICATED_FUNDING_SETTLEMENT_EVIDENCE = "DUPLICATED_FUNDING_SETTLEMENT_EVIDENCE"
    OUT_OF_ORDER_LEDGER_EVIDENCE = "OUT_OF_ORDER_LEDGER_EVIDENCE"
    CONTRADICTORY_LEDGER_EVIDENCE = "CONTRADICTORY_LEDGER_EVIDENCE"


@dataclass(frozen=True, slots=True)
class LedgerReconciliationResult:
    """Pure replay result for one Capture ledger history."""

    capture_id: str
    route_id: str | None
    settlement_time: datetime
    reconciled: bool
    reasons: tuple[LedgerReconciliationReason, ...]
    route_decision_event_sequence: int | None
    paper_event_sequences: tuple[int, ...]
    funding_verification_event_sequence: int | None
    checked_event_sequences: tuple[int, ...]


_ROUTE_DECISION_EVENT_TYPE = LedgerEventType.ROUTE_DECISION_RECORDED.value
_PAPER_OPENED_EVENT_TYPE = LedgerEventType.PAPER_CAPTURE_OPENED.value
_PAPER_SETTLEMENT_EVENT_TYPE = LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value
_PAPER_CLOSED_EVENT_TYPE = LedgerEventType.PAPER_CAPTURE_CLOSED.value
_FUNDING_CHECKPOINT_EVENT_TYPE = LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value
_FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE = (
    LedgerEventType.FUNDING_SETTLEMENT_EVIDENCE_RECORDED.value
)
_FUNDING_VERIFICATION_EVENT_TYPE = (
    LedgerEventType.FUNDING_SETTLEMENT_VERIFICATION_RECORDED.value
)

_PAPER_LIFECYCLE_EVENT_ORDER = (
    _PAPER_OPENED_EVENT_TYPE,
    _PAPER_SETTLEMENT_EVENT_TYPE,
    _PAPER_CLOSED_EVENT_TYPE,
)
_CAPTURE_SCOPED_EVENT_TYPES = frozenset(
    {
        _PAPER_OPENED_EVENT_TYPE,
        _PAPER_SETTLEMENT_EVENT_TYPE,
        _PAPER_CLOSED_EVENT_TYPE,
        _FUNDING_CHECKPOINT_EVENT_TYPE,
        _FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE,
        _FUNDING_VERIFICATION_EVENT_TYPE,
    }
)


def _add_reason(
    reasons: list[LedgerReconciliationReason],
    reason: LedgerReconciliationReason,
) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _payload_str(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if isinstance(value, str) and value.strip():
        return value
    return None


def _payload_datetime(payload: Mapping[str, Any], field_name: str) -> datetime | None:
    value = payload.get(field_name)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        validate_timezone_aware_datetime(parsed, field_name)
    except ValueError:
        return None
    return parsed


def _payload_int(payload: Mapping[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if type(value) is int and value > 0:
        return value
    return None


def _payload_int_sequence(payload: Mapping[str, Any], field_name: str) -> tuple[int, ...] | None:
    value = payload.get(field_name)
    if not isinstance(value, tuple | list):
        return None
    parsed: list[int] = []
    for item in value:
        if type(item) is not int or item <= 0:
            return None
        parsed.append(item)
    if len(set(parsed)) != len(parsed):
        return None
    return tuple(parsed)


def _payload_str_sequence(payload: Mapping[str, Any], field_name: str) -> tuple[str, ...] | None:
    value = payload.get(field_name)
    if not isinstance(value, tuple | list):
        return None
    parsed: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        parsed.append(item)
    return tuple(parsed)


def _sorted_events(events: Sequence[LedgerEvent]) -> tuple[LedgerEvent, ...]:
    return tuple(sorted(events, key=lambda event: event.sequence))


def _event_by_sequence(
    events: Sequence[LedgerEvent],
    reasons: list[LedgerReconciliationReason],
) -> dict[int, LedgerEvent]:
    event_by_sequence: dict[int, LedgerEvent] = {}
    for event in events:
        if event.sequence in event_by_sequence:
            _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)
            continue
        event_by_sequence[event.sequence] = event
    return event_by_sequence


def _capture_events(events: Sequence[LedgerEvent], capture_id: str) -> tuple[LedgerEvent, ...]:
    return tuple(
        event
        for event in events
        if event.event_type in _CAPTURE_SCOPED_EVENT_TYPES
        and event.payload.get("capture_id") == capture_id
    )


def _route_identity(events: Sequence[LedgerEvent]) -> tuple[str | None, bool]:
    route_ids = {_payload_str(event.payload, "route_id") for event in events}
    if None in route_ids:
        return None, False
    known_route_ids = {route_id for route_id in route_ids if route_id is not None}
    if len(known_route_ids) != 1:
        return next(iter(sorted(known_route_ids))) if known_route_ids else None, False
    return next(iter(known_route_ids)), True


def _route_decision_events(events: Sequence[LedgerEvent], route_id: str | None) -> tuple[LedgerEvent, ...]:
    if route_id is None:
        return ()
    return tuple(
        event
        for event in events
        if event.event_type == _ROUTE_DECISION_EVENT_TYPE
        and event.payload.get("route_id") == route_id
        and event.payload.get("mode") == EvaluationMode.ENTRY.value
    )


def _validate_route_decision(
    events: Sequence[LedgerEvent],
    route_id: str | None,
    reasons: list[LedgerReconciliationReason],
) -> LedgerEvent | None:
    route_decisions = _route_decision_events(events, route_id)
    if not route_decisions:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_ROUTE_DECISION)
        return None
    if len(route_decisions) != 1:
        _add_reason(reasons, LedgerReconciliationReason.DUPLICATED_ROUTE_DECISION_EVIDENCE)
        return None

    route_decision = route_decisions[0]
    if (
        route_decision.payload.get("status") != RouteStatus.PAPER_ELIGIBLE.value
        or route_decision.payload.get("has_capture_plan") is not False
    ):
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_ROUTE_DECISION_EVIDENCE)
    return route_decision


def _events_of_type(events: Sequence[LedgerEvent], event_type: str) -> tuple[LedgerEvent, ...]:
    return tuple(event for event in events if event.event_type == event_type)


def _validate_paper_lifecycle(
    capture_events: Sequence[LedgerEvent],
    route_decision: LedgerEvent | None,
    capture_id: str,
    settlement_time: datetime,
    reasons: list[LedgerReconciliationReason],
) -> tuple[int, ...]:
    paper_events: list[LedgerEvent] = []
    missing_lifecycle_evidence = False
    duplicated_lifecycle_evidence = False

    for event_type in _PAPER_LIFECYCLE_EVENT_ORDER:
        matching_events = _events_of_type(capture_events, event_type)
        if not matching_events:
            missing_lifecycle_evidence = True
            continue
        if len(matching_events) != 1:
            duplicated_lifecycle_evidence = True
        paper_events.extend(matching_events)

    if missing_lifecycle_evidence:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_PAPER_LIFECYCLE_EVIDENCE)
    if duplicated_lifecycle_evidence:
        _add_reason(reasons, LedgerReconciliationReason.DUPLICATED_PAPER_LIFECYCLE_EVIDENCE)

    paper_events = list(_sorted_events(paper_events))
    paper_event_sequences = tuple(event.sequence for event in paper_events)
    if len(paper_events) == len(_PAPER_LIFECYCLE_EVENT_ORDER):
        event_sequence_by_type = {event.event_type: event.sequence for event in paper_events}
        if not (
            event_sequence_by_type[_PAPER_OPENED_EVENT_TYPE]
            < event_sequence_by_type[_PAPER_SETTLEMENT_EVENT_TYPE]
            < event_sequence_by_type[_PAPER_CLOSED_EVENT_TYPE]
        ):
            _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)
        if route_decision is not None and route_decision.sequence >= paper_event_sequences[0]:
            _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)

        try:
            replayed = replay_paper_captures(tuple(paper_events))
        except ValueError:
            _add_reason(reasons, LedgerReconciliationReason.PAPER_REPLAY_FAILED)
        else:
            if (
                len(replayed) != 1
                or replayed[0].capture.capture_id != capture_id
                or replayed[0].capture.settlement_time != settlement_time
                or replayed[0].event_sequences != paper_event_sequences
            ):
                _add_reason(reasons, LedgerReconciliationReason.PAPER_REPLAY_FAILED)

    return paper_event_sequences


def _validate_capture_identity_and_settlement_time(
    capture_events: Sequence[LedgerEvent],
    settlement_time: datetime,
    reasons: list[LedgerReconciliationReason],
) -> tuple[str | None, bool]:
    route_id, route_identity_is_consistent = _route_identity(capture_events)
    if capture_events and not route_identity_is_consistent:
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)

    for event in capture_events:
        event_settlement_time = _payload_datetime(event.payload, "settlement_time")
        if event_settlement_time != settlement_time:
            _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)

    return route_id, route_identity_is_consistent


def _validate_checkpoint_evidence(
    checkpoint_events: Sequence[LedgerEvent],
    reasons: list[LedgerReconciliationReason],
) -> None:
    checkpoint_labels: set[str] = set()
    for event in checkpoint_events:
        checkpoint = _payload_str(event.payload, "checkpoint")
        if checkpoint is None:
            _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)
            continue
        if checkpoint in checkpoint_labels:
            _add_reason(reasons, LedgerReconciliationReason.DUPLICATED_FUNDING_SETTLEMENT_EVIDENCE)
        checkpoint_labels.add(checkpoint)


def _referenced_event_matches_capture(
    event: LedgerEvent,
    *,
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
) -> bool:
    event_route_id = _payload_str(event.payload, "route_id")
    event_settlement_time = _payload_datetime(event.payload, "settlement_time")
    return (
        event.payload.get("capture_id") == capture_id
        and (route_id is None or event_route_id == route_id)
        and event_settlement_time == settlement_time
    )


def _validate_referenced_funding_evidence(
    *,
    verification_event: LedgerEvent,
    event_by_sequence: Mapping[int, LedgerEvent],
    checkpoint_events: Sequence[LedgerEvent],
    settlement_evidence_events: Sequence[LedgerEvent],
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
    reasons: list[LedgerReconciliationReason],
) -> None:
    checkpoint_sequences = _payload_int_sequence(
        verification_event.payload,
        "checkpoint_event_sequences",
    )
    settlement_sequence = _payload_int(
        verification_event.payload,
        "settlement_event_sequence",
    )
    required_checkpoints = _payload_str_sequence(
        verification_event.payload,
        "required_checkpoints",
    )

    if checkpoint_sequences is None or settlement_sequence is None:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)
        return
    if required_checkpoints is None or len(required_checkpoints) != len(checkpoint_sequences):
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)

    actual_checkpoint_sequences = {event.sequence for event in checkpoint_events}
    actual_settlement_sequences = {event.sequence for event in settlement_evidence_events}
    if actual_checkpoint_sequences != set(checkpoint_sequences):
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)
    if actual_settlement_sequences != {settlement_sequence}:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)

    for checkpoint_sequence in checkpoint_sequences:
        checkpoint_event = event_by_sequence.get(checkpoint_sequence)
        if (
            checkpoint_event is None
            or checkpoint_event.event_type != _FUNDING_CHECKPOINT_EVENT_TYPE
            or not _referenced_event_matches_capture(
                checkpoint_event,
                capture_id=capture_id,
                route_id=route_id,
                settlement_time=settlement_time,
            )
        ):
            _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)
            continue
        if checkpoint_event.sequence >= verification_event.sequence:
            _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)

    settlement_event = event_by_sequence.get(settlement_sequence)
    if (
        settlement_event is None
        or settlement_event.event_type != _FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE
        or not _referenced_event_matches_capture(
            settlement_event,
            capture_id=capture_id,
            route_id=route_id,
            settlement_time=settlement_time,
        )
    ):
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)
    elif settlement_event.sequence >= verification_event.sequence:
        _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)


def _validate_funding_verification(
    *,
    capture_events: Sequence[LedgerEvent],
    event_by_sequence: Mapping[int, LedgerEvent],
    paper_event_sequences: Sequence[int],
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
    reasons: list[LedgerReconciliationReason],
) -> LedgerEvent | None:
    verification_events = _events_of_type(capture_events, _FUNDING_VERIFICATION_EVENT_TYPE)
    if not verification_events:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_VERIFICATION)
        return None
    if len(verification_events) != 1:
        _add_reason(reasons, LedgerReconciliationReason.DUPLICATED_FUNDING_SETTLEMENT_VERIFICATION)
        return None

    verification_event = verification_events[0]
    if verification_event.payload.get("verified") is not True:
        _add_reason(reasons, LedgerReconciliationReason.FUNDING_SETTLEMENT_NOT_VERIFIED)
    if not _referenced_event_matches_capture(
        verification_event,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
    ):
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)
    if paper_event_sequences and verification_event.sequence <= max(paper_event_sequences):
        _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)

    checkpoint_events = _events_of_type(capture_events, _FUNDING_CHECKPOINT_EVENT_TYPE)
    settlement_evidence_events = _events_of_type(
        capture_events,
        _FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE,
    )
    _validate_checkpoint_evidence(checkpoint_events, reasons)
    if not settlement_evidence_events:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_EVIDENCE)
    elif len(settlement_evidence_events) != 1:
        _add_reason(reasons, LedgerReconciliationReason.DUPLICATED_FUNDING_SETTLEMENT_EVIDENCE)

    _validate_referenced_funding_evidence(
        verification_event=verification_event,
        event_by_sequence=event_by_sequence,
        checkpoint_events=checkpoint_events,
        settlement_evidence_events=settlement_evidence_events,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        reasons=reasons,
    )
    return verification_event


def replay_ledger_reconciliation(
    events: Sequence[LedgerEvent],
    *,
    capture_id: str,
    settlement_time: datetime,
) -> LedgerReconciliationResult:
    """Recompute one reconciliation result from append-only ledger evidence."""

    if not capture_id.strip():
        raise ValueError("capture_id must be non-empty")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")

    reasons: list[LedgerReconciliationReason] = []
    sorted_events = _sorted_events(events)
    event_by_sequence = _event_by_sequence(sorted_events, reasons)
    capture_events = _capture_events(sorted_events, capture_id)
    route_id, _ = _validate_capture_identity_and_settlement_time(
        capture_events,
        settlement_time,
        reasons,
    )

    route_decision = _validate_route_decision(sorted_events, route_id, reasons)
    paper_event_sequences = _validate_paper_lifecycle(
        capture_events,
        route_decision,
        capture_id,
        settlement_time,
        reasons,
    )
    funding_verification = _validate_funding_verification(
        capture_events=capture_events,
        event_by_sequence=event_by_sequence,
        paper_event_sequences=paper_event_sequences,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        reasons=reasons,
    )

    checked_event_sequences = set(paper_event_sequences)
    if route_decision is not None:
        checked_event_sequences.add(route_decision.sequence)
    if funding_verification is not None:
        checked_event_sequences.add(funding_verification.sequence)
        checkpoint_sequences = _payload_int_sequence(
            funding_verification.payload,
            "checkpoint_event_sequences",
        )
        settlement_sequence = _payload_int(
            funding_verification.payload,
            "settlement_event_sequence",
        )
        if checkpoint_sequences is not None:
            checked_event_sequences.update(checkpoint_sequences)
        if settlement_sequence is not None:
            checked_event_sequences.add(settlement_sequence)

    reconciled = (
        not reasons
        and route_decision is not None
        and len(paper_event_sequences) == len(_PAPER_LIFECYCLE_EVENT_ORDER)
        and funding_verification is not None
    )

    return LedgerReconciliationResult(
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        reconciled=reconciled,
        reasons=tuple(reasons),
        route_decision_event_sequence=route_decision.sequence if route_decision is not None else None,
        paper_event_sequences=tuple(paper_event_sequences),
        funding_verification_event_sequence=(
            funding_verification.sequence if funding_verification is not None else None
        ),
        checked_event_sequences=tuple(sorted(checked_event_sequences)),
    )


def reconcile_ledger(
    ledger: Ledger,
    *,
    capture_id: str,
    settlement_time: datetime,
    recorded_at: datetime | None = None,
) -> LedgerReconciliationResult:
    """Replay ledger history and append the reconciliation result."""

    result = replay_ledger_reconciliation(
        ledger.records(),
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    append_ledger_reconciliation_event(
        ledger,
        capture_id=result.capture_id,
        route_id=result.route_id,
        settlement_time=result.settlement_time,
        reconciled=result.reconciled,
        reasons=result.reasons,
        route_decision_event_sequence=result.route_decision_event_sequence,
        paper_event_sequences=result.paper_event_sequences,
        funding_verification_event_sequence=result.funding_verification_event_sequence,
        checked_event_sequences=result.checked_event_sequences,
        recorded_at=recorded_at or settlement_time,
    )
    return result
