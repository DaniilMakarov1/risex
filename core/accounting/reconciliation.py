"""Deterministic offline ledger reconciliation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
from core.domain.enums import CaptureState, EvaluationMode, RouteStatus, ValueSource


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
    NON_CONTIGUOUS_LEDGER_SEQUENCE = "NON_CONTIGUOUS_LEDGER_SEQUENCE"
    UNKNOWN_LEDGER_EVENT_TYPE = "UNKNOWN_LEDGER_EVENT_TYPE"
    MALFORMED_LEDGER_EVENT_PAYLOAD = "MALFORMED_LEDGER_EVENT_PAYLOAD"


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
_LEDGER_RECONCILIATION_EVENT_TYPE = LedgerEventType.LEDGER_RECONCILIATION_RECORDED.value
_KNOWN_EVENT_TYPES = frozenset(event_type.value for event_type in LedgerEventType)

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


def _payload_optional_str(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    return value if isinstance(value, str) and value.strip() else ""


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


def _payload_optional_int(payload: Mapping[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if type(value) is int and value > 0:
        return value
    return 0


def _payload_non_negative_int(payload: Mapping[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if type(value) is int and value >= 0:
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


def _finite_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _positive_decimal_payload(payload: Mapping[str, Any], field_name: str) -> bool:
    value = _finite_decimal(payload.get(field_name))
    return value is not None and value > Decimal("0")


def _optional_decimal_payload(payload: Mapping[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    return value is None or _finite_decimal(value) is not None


def _estimated_value_payload_is_well_formed(payload: Mapping[str, Any], field_name: str) -> bool:
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, Mapping):
        return False
    try:
        source = ValueSource(str(raw_value.get("source")))
    except ValueError:
        return False
    value = raw_value.get("value")
    if source is ValueSource.UNKNOWN:
        return value is None
    return value is not None and _finite_decimal(value) is not None


def _state_path_is_well_formed(payload: Mapping[str, Any]) -> bool:
    state = payload.get("state")
    state_path = payload.get("state_path")
    if not isinstance(state_path, tuple | list) or not state_path:
        return False
    try:
        CaptureState(str(state))
        for item in state_path:
            CaptureState(str(item))
    except ValueError:
        return False
    return True


def _route_decision_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    if _payload_str(payload, "route_id") is None:
        return False
    try:
        EvaluationMode(str(payload.get("mode")))
        RouteStatus(str(payload.get("status")))
    except ValueError:
        return False
    return (
        _payload_str_sequence(payload, "reasons") is not None
        and _optional_decimal_payload(payload, "net_profit_usd")
        and type(payload.get("has_capture_plan")) is bool
    )


def _paper_lifecycle_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    return (
        _payload_str(payload, "capture_id") is not None
        and _payload_str(payload, "route_id") is not None
        and _payload_datetime(payload, "settlement_time") is not None
        and _state_path_is_well_formed(payload)
    )


def _paper_rejection_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    try:
        EvaluationMode(str(payload.get("mode")))
        RouteStatus(str(payload.get("status")))
    except ValueError:
        return False
    return (
        _payload_str(payload, "route_id") is not None
        and _payload_str_sequence(payload, "reasons") is not None
        and payload.get("capture_started") is False
    )


def _funding_checkpoint_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    return (
        _payload_str(payload, "capture_id") is not None
        and _payload_str(payload, "route_id") is not None
        and _payload_str(payload, "checkpoint") is not None
        and _payload_datetime(payload, "settlement_time") is not None
        and _payload_datetime(payload, "observed_at") is not None
        and _positive_decimal_payload(payload, "target_notional_usd")
        and _estimated_value_payload_is_well_formed(payload, "risex_expected_funding_usd")
        and _estimated_value_payload_is_well_formed(payload, "hedge_expected_funding_usd")
    )


def _funding_settlement_evidence_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    return (
        _payload_str(payload, "capture_id") is not None
        and _payload_str(payload, "route_id") is not None
        and _payload_datetime(payload, "settlement_time") is not None
        and _payload_datetime(payload, "observed_at") is not None
        and _estimated_value_payload_is_well_formed(payload, "actual_risex_funding_usd")
        and _estimated_value_payload_is_well_formed(payload, "actual_hedge_funding_usd")
        and _estimated_value_payload_is_well_formed(payload, "actual_risex_notional_usd")
        and _estimated_value_payload_is_well_formed(payload, "actual_hedge_notional_usd")
    )


def _funding_verification_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    route_id = _payload_optional_str(payload, "route_id")
    return (
        _payload_str(payload, "capture_id") is not None
        and route_id != ""
        and _payload_datetime(payload, "settlement_time") is not None
        and type(payload.get("verified")) is bool
        and _payload_str_sequence(payload, "reasons") is not None
        and _payload_str_sequence(payload, "required_checkpoints") is not None
        and _payload_int_sequence(payload, "checkpoint_event_sequences") is not None
        and _payload_optional_int(payload, "settlement_event_sequence") != 0
    )


def _ledger_reconciliation_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    route_id = _payload_optional_str(payload, "route_id")
    event_count = _payload_non_negative_int(payload, "event_count")
    last_sequence = _payload_optional_int(payload, "last_sequence")
    if event_count is None or last_sequence == 0:
        return False
    if event_count == 0 and last_sequence is not None:
        return False
    if event_count > 0 and last_sequence is None:
        return False
    return (
        _payload_str(payload, "capture_id") is not None
        and route_id != ""
        and _payload_datetime(payload, "settlement_time") is not None
        and type(payload.get("reconciled")) is bool
        and _payload_str_sequence(payload, "reasons") is not None
        and _payload_optional_int(payload, "route_decision_event_sequence") != 0
        and _payload_int_sequence(payload, "paper_event_sequences") is not None
        and _payload_optional_int(payload, "funding_verification_event_sequence") != 0
        and _payload_int_sequence(payload, "checked_event_sequences") is not None
    )


def _event_payload_is_well_formed(event: LedgerEvent) -> bool:
    payload = event.payload
    if event.event_type == _ROUTE_DECISION_EVENT_TYPE:
        return _route_decision_payload_is_well_formed(payload)
    if event.event_type in _PAPER_LIFECYCLE_EVENT_ORDER:
        return _paper_lifecycle_payload_is_well_formed(payload)
    if event.event_type == LedgerEventType.PAPER_REJECTION_RECORDED.value:
        return _paper_rejection_payload_is_well_formed(payload)
    if event.event_type == _FUNDING_CHECKPOINT_EVENT_TYPE:
        return _funding_checkpoint_payload_is_well_formed(payload)
    if event.event_type == _FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE:
        return _funding_settlement_evidence_payload_is_well_formed(payload)
    if event.event_type == _FUNDING_VERIFICATION_EVENT_TYPE:
        return _funding_verification_payload_is_well_formed(payload)
    if event.event_type == _LEDGER_RECONCILIATION_EVENT_TYPE:
        return _ledger_reconciliation_payload_is_well_formed(payload)
    return False


def _validate_supplied_ledger_history(
    events: Sequence[LedgerEvent],
    reasons: list[LedgerReconciliationReason],
) -> tuple[LedgerEvent, ...]:
    supplied_events = tuple(events)
    for expected_sequence, event in enumerate(supplied_events, start=1):
        if event.sequence != expected_sequence:
            _add_reason(reasons, LedgerReconciliationReason.NON_CONTIGUOUS_LEDGER_SEQUENCE)
        if event.event_type not in _KNOWN_EVENT_TYPES:
            _add_reason(reasons, LedgerReconciliationReason.UNKNOWN_LEDGER_EVENT_TYPE)
            continue
        if not _event_payload_is_well_formed(event):
            _add_reason(reasons, LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD)
    return supplied_events


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
    supplied_events = _validate_supplied_ledger_history(events, reasons)
    event_by_sequence = _event_by_sequence(supplied_events, reasons)
    capture_events = _capture_events(supplied_events, capture_id)
    route_id, _ = _validate_capture_identity_and_settlement_time(
        capture_events,
        settlement_time,
        reasons,
    )

    route_decision = _validate_route_decision(supplied_events, route_id, reasons)
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


def is_ledger_explicitly_reconciled(events: Sequence[LedgerEvent]) -> bool:
    """Return True only when the latest event reconciles the exact prior history."""

    reasons: list[LedgerReconciliationReason] = []
    supplied_events = _validate_supplied_ledger_history(events, reasons)
    if reasons or not supplied_events:
        return False

    reconciliation_event = supplied_events[-1]
    if reconciliation_event.event_type != _LEDGER_RECONCILIATION_EVENT_TYPE:
        return False
    if reconciliation_event.payload.get("reconciled") is not True:
        return False

    event_count = _payload_non_negative_int(reconciliation_event.payload, "event_count")
    last_sequence = _payload_optional_int(reconciliation_event.payload, "last_sequence")
    if event_count is None or last_sequence == 0:
        return False

    checked_history = supplied_events[:-1]
    expected_event_count = len(checked_history)
    expected_last_sequence = checked_history[-1].sequence if checked_history else None
    if event_count != expected_event_count or last_sequence != expected_last_sequence:
        return False

    capture_id = _payload_str(reconciliation_event.payload, "capture_id")
    settlement_time = _payload_datetime(reconciliation_event.payload, "settlement_time")
    if capture_id is None or settlement_time is None:
        return False

    replayed_result = replay_ledger_reconciliation(
        checked_history,
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    return (
        replayed_result.reconciled is True
        and reconciliation_event.payload.get("route_id") == replayed_result.route_id
        and reconciliation_event.payload.get("reasons") == tuple(
            reason.value for reason in replayed_result.reasons
        )
        and reconciliation_event.payload.get("route_decision_event_sequence")
        == replayed_result.route_decision_event_sequence
        and reconciliation_event.payload.get("paper_event_sequences")
        == replayed_result.paper_event_sequences
        and reconciliation_event.payload.get("funding_verification_event_sequence")
        == replayed_result.funding_verification_event_sequence
        and reconciliation_event.payload.get("checked_event_sequences")
        == replayed_result.checked_event_sequences
    )


def reconcile_ledger(
    ledger: Ledger,
    *,
    capture_id: str,
    settlement_time: datetime,
    recorded_at: datetime | None = None,
) -> LedgerReconciliationResult:
    """Replay ledger history and append the reconciliation result."""

    checked_events = ledger.records()
    result = replay_ledger_reconciliation(
        checked_events,
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    last_sequence = checked_events[-1].sequence if checked_events else None
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
        event_count=len(checked_events),
        last_sequence=last_sequence,
        recorded_at=recorded_at or settlement_time,
    )
    return result
