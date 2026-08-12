"""Deterministic offline funding settlement verification."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from core.accounting.ledger import (
    Ledger,
    LedgerEvent,
    LedgerEventType,
    append_funding_settlement_evidence_event,
    append_funding_settlement_verification_event,
)
from core.domain.contracts import (
    Capture,
    EstimatedValue,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import ValueSource


class FundingCheckpointLabel(StrEnum):
    """Required pre-settlement observation checkpoint labels."""

    T_MINUS_20M = "T_MINUS_20M"
    T_MINUS_60S = "T_MINUS_60S"
    T_MINUS_10S = "T_MINUS_10S"
    T_MINUS_5S = "T_MINUS_5S"


@dataclass(frozen=True, slots=True)
class FundingCheckpointRequirement:
    """One required offset before the settlement timestamp."""

    checkpoint: FundingCheckpointLabel
    offset_before_settlement: timedelta


REQUIRED_FUNDING_CHECKPOINTS = (
    FundingCheckpointRequirement(FundingCheckpointLabel.T_MINUS_20M, timedelta(minutes=20)),
    FundingCheckpointRequirement(FundingCheckpointLabel.T_MINUS_60S, timedelta(seconds=60)),
    FundingCheckpointRequirement(FundingCheckpointLabel.T_MINUS_10S, timedelta(seconds=10)),
    FundingCheckpointRequirement(FundingCheckpointLabel.T_MINUS_5S, timedelta(seconds=5)),
)


class FundingSettlementVerificationReason(StrEnum):
    """Fail-closed reasons for funding settlement verification."""

    MISSING_REQUIRED_CHECKPOINT = "MISSING_REQUIRED_CHECKPOINT"
    MISSING_SETTLEMENT_EVIDENCE = "MISSING_SETTLEMENT_EVIDENCE"
    INCONSISTENT_CAPTURE_IDENTITY = "INCONSISTENT_CAPTURE_IDENTITY"
    INCONSISTENT_SETTLEMENT_TIME = "INCONSISTENT_SETTLEMENT_TIME"
    INCONSISTENT_CHECKPOINT_TIME = "INCONSISTENT_CHECKPOINT_TIME"
    INCONSISTENT_CHECKPOINT_EVIDENCE = "INCONSISTENT_CHECKPOINT_EVIDENCE"
    INCONSISTENT_SETTLEMENT_EVIDENCE = "INCONSISTENT_SETTLEMENT_EVIDENCE"
    INCONSISTENT_FUNDING_EVIDENCE = "INCONSISTENT_FUNDING_EVIDENCE"
    INCONSISTENT_NOTIONAL_EVIDENCE = "INCONSISTENT_NOTIONAL_EVIDENCE"
    UNOBSERVED_SETTLEMENT_EVIDENCE = "UNOBSERVED_SETTLEMENT_EVIDENCE"
    UNKNOWN_FUNDING_EVIDENCE = "UNKNOWN_FUNDING_EVIDENCE"
    UNKNOWN_NOTIONAL_EVIDENCE = "UNKNOWN_NOTIONAL_EVIDENCE"


@dataclass(frozen=True, slots=True)
class FundingSettlementVerificationResult:
    """Pure replay result for one capture funding settlement."""

    capture_id: str
    route_id: str | None
    settlement_time: datetime
    verified: bool
    reasons: tuple[FundingSettlementVerificationReason, ...]
    checkpoint_event_sequences: tuple[int, ...]
    settlement_event_sequence: int | None


@dataclass(frozen=True, slots=True)
class _CheckpointEvidence:
    event: LedgerEvent
    checkpoint: FundingCheckpointLabel
    observed_at: datetime | None
    settlement_time: datetime | None
    target_notional_usd: Decimal | None
    risex_expected_funding_usd: Decimal | None
    hedge_expected_funding_usd: Decimal | None
    has_unknown_funding: bool
    has_unknown_notional: bool


@dataclass(frozen=True, slots=True)
class _SettlementEvidence:
    event: LedgerEvent
    observed_at: datetime | None
    settlement_time: datetime | None
    approval_granted: bool
    actual_risex_funding_usd: Decimal | None
    actual_hedge_funding_usd: Decimal | None
    actual_risex_notional_usd: Decimal | None
    actual_hedge_notional_usd: Decimal | None
    has_unknown_funding: bool
    has_unknown_notional: bool
    has_unobserved_evidence: bool


_CHECKPOINT_EVENT_TYPE = LedgerEventType.FUNDING_CHECKPOINT_OBSERVED.value
_SETTLEMENT_EVIDENCE_EVENT_TYPE = LedgerEventType.FUNDING_SETTLEMENT_EVIDENCE_RECORDED.value
_IDENTITY_EVENT_TYPES = frozenset(
    {
        LedgerEventType.PAPER_CAPTURE_OPENED.value,
        LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
        LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        _CHECKPOINT_EVENT_TYPE,
        _SETTLEMENT_EVIDENCE_EVENT_TYPE,
    }
)


def _required_checkpoint_labels() -> tuple[FundingCheckpointLabel, ...]:
    return tuple(requirement.checkpoint for requirement in REQUIRED_FUNDING_CHECKPOINTS)


def _add_reason(
    reasons: list[FundingSettlementVerificationReason],
    reason: FundingSettlementVerificationReason,
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


def _finite_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _payload_decimal(payload: Mapping[str, Any], field_name: str) -> Decimal | None:
    return _finite_decimal(payload.get(field_name))


def _estimated_decimal(payload: Mapping[str, Any], field_name: str) -> tuple[Decimal | None, bool]:
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, Mapping):
        return None, True
    source = raw_value.get("source")
    value = raw_value.get("value")
    try:
        parsed_source = ValueSource(str(source))
    except ValueError:
        return None, True
    if parsed_source is ValueSource.UNKNOWN or value is None:
        return None, True
    parsed_value = _finite_decimal(value)
    if parsed_value is None:
        return None, True
    return parsed_value, False


def _observed_estimated_decimal(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[Decimal | None, bool, bool]:
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, Mapping):
        return None, True, True
    source = raw_value.get("source")
    value = raw_value.get("value")
    try:
        parsed_source = ValueSource(str(source))
    except ValueError:
        return None, True, True

    source_is_unobserved = parsed_source is not ValueSource.OBSERVED
    if parsed_source is ValueSource.UNKNOWN or value is None:
        return None, True, source_is_unobserved
    parsed_value = _finite_decimal(value)
    if parsed_value is None:
        return None, True, source_is_unobserved
    return parsed_value, False, source_is_unobserved


def _positive_observed_estimated_decimal(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[Decimal | None, bool, bool]:
    value, unknown, source_is_unobserved = _observed_estimated_decimal(payload, field_name)
    if unknown or value is None or value <= Decimal("0"):
        return None, True, source_is_unobserved
    return value, False, source_is_unobserved


def _checkpoint_label(event: LedgerEvent) -> FundingCheckpointLabel | None:
    raw_checkpoint = event.payload.get("checkpoint")
    try:
        return FundingCheckpointLabel(str(raw_checkpoint))
    except ValueError:
        return None


def _parse_checkpoint(event: LedgerEvent) -> _CheckpointEvidence | None:
    checkpoint = _checkpoint_label(event)
    if checkpoint is None:
        return None

    risex_funding, unknown_risex_funding = _estimated_decimal(
        event.payload,
        "risex_expected_funding_usd",
    )
    hedge_funding, unknown_hedge_funding = _estimated_decimal(
        event.payload,
        "hedge_expected_funding_usd",
    )
    target_notional = _payload_decimal(event.payload, "target_notional_usd")

    return _CheckpointEvidence(
        event=event,
        checkpoint=checkpoint,
        observed_at=_payload_datetime(event.payload, "observed_at"),
        settlement_time=_payload_datetime(event.payload, "settlement_time"),
        target_notional_usd=target_notional if target_notional is not None and target_notional > 0 else None,
        risex_expected_funding_usd=risex_funding,
        hedge_expected_funding_usd=hedge_funding,
        has_unknown_funding=unknown_risex_funding or unknown_hedge_funding,
        has_unknown_notional=target_notional is None or target_notional <= 0,
    )


def _parse_settlement(event: LedgerEvent) -> _SettlementEvidence:
    risex_funding, unknown_risex_funding, unobserved_risex_funding = _observed_estimated_decimal(
        event.payload,
        "actual_risex_funding_usd",
    )
    hedge_funding, unknown_hedge_funding, unobserved_hedge_funding = _observed_estimated_decimal(
        event.payload,
        "actual_hedge_funding_usd",
    )
    risex_notional, unknown_risex_notional, unobserved_risex_notional = _positive_observed_estimated_decimal(
        event.payload,
        "actual_risex_notional_usd",
    )
    hedge_notional, unknown_hedge_notional, unobserved_hedge_notional = _positive_observed_estimated_decimal(
        event.payload,
        "actual_hedge_notional_usd",
    )

    return _SettlementEvidence(
        event=event,
        observed_at=_payload_datetime(event.payload, "observed_at"),
        settlement_time=_payload_datetime(event.payload, "settlement_time"),
        approval_granted=event.payload.get("approval_granted") is True,
        actual_risex_funding_usd=risex_funding,
        actual_hedge_funding_usd=hedge_funding,
        actual_risex_notional_usd=risex_notional,
        actual_hedge_notional_usd=hedge_notional,
        has_unknown_funding=unknown_risex_funding or unknown_hedge_funding,
        has_unknown_notional=unknown_risex_notional or unknown_hedge_notional,
        has_unobserved_evidence=(
            unobserved_risex_funding
            or unobserved_hedge_funding
            or unobserved_risex_notional
            or unobserved_hedge_notional
        ),
    )


def _capture_events(events: Sequence[LedgerEvent], capture_id: str) -> tuple[LedgerEvent, ...]:
    return tuple(
        event
        for event in sorted(events, key=lambda item: item.sequence)
        if event.event_type in _IDENTITY_EVENT_TYPES and event.payload.get("capture_id") == capture_id
    )


def _route_identity(events: Sequence[LedgerEvent]) -> tuple[str | None, bool]:
    route_ids = {_payload_str(event.payload, "route_id") for event in events}
    if None in route_ids:
        return None, False
    known_route_ids = {route_id for route_id in route_ids if route_id is not None}
    if len(known_route_ids) != 1:
        return next(iter(sorted(known_route_ids))) if known_route_ids else None, False
    return next(iter(known_route_ids)), True


def replay_funding_settlement_verification(
    events: Sequence[LedgerEvent],
    *,
    capture_id: str,
    settlement_time: datetime,
) -> FundingSettlementVerificationResult:
    """Recompute one verifier result from append-only ledger evidence."""

    if not capture_id.strip():
        raise ValueError("capture_id must be non-empty")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")

    reasons: list[FundingSettlementVerificationReason] = []
    capture_events = _capture_events(events, capture_id)
    route_id, route_identity_is_consistent = _route_identity(capture_events)
    if capture_events and not route_identity_is_consistent:
        _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_CAPTURE_IDENTITY)

    for event in capture_events:
        event_settlement_time = _payload_datetime(event.payload, "settlement_time")
        if event_settlement_time != settlement_time:
            _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_TIME)

    checkpoint_candidates = tuple(
        event for event in capture_events if event.event_type == _CHECKPOINT_EVENT_TYPE
    )
    checkpoint_evidence_by_label: dict[FundingCheckpointLabel, _CheckpointEvidence] = {}
    duplicate_labels: set[FundingCheckpointLabel] = set()
    for event in checkpoint_candidates:
        checkpoint_evidence = _parse_checkpoint(event)
        if checkpoint_evidence is None:
            _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_CHECKPOINT_EVIDENCE)
            continue
        if checkpoint_evidence.checkpoint in checkpoint_evidence_by_label:
            duplicate_labels.add(checkpoint_evidence.checkpoint)
            continue
        checkpoint_evidence_by_label[checkpoint_evidence.checkpoint] = checkpoint_evidence

    if duplicate_labels:
        _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_CHECKPOINT_EVIDENCE)

    required_checkpoint_evidence: list[_CheckpointEvidence] = []
    for requirement in REQUIRED_FUNDING_CHECKPOINTS:
        checkpoint_evidence = checkpoint_evidence_by_label.get(requirement.checkpoint)
        if checkpoint_evidence is None:
            _add_reason(reasons, FundingSettlementVerificationReason.MISSING_REQUIRED_CHECKPOINT)
            continue
        required_checkpoint_evidence.append(checkpoint_evidence)
        if checkpoint_evidence.settlement_time != settlement_time:
            _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_TIME)
        expected_observed_at = settlement_time - requirement.offset_before_settlement
        if checkpoint_evidence.observed_at != expected_observed_at:
            _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_CHECKPOINT_TIME)
        if checkpoint_evidence.has_unknown_funding:
            _add_reason(reasons, FundingSettlementVerificationReason.UNKNOWN_FUNDING_EVIDENCE)
        if checkpoint_evidence.has_unknown_notional:
            _add_reason(reasons, FundingSettlementVerificationReason.UNKNOWN_NOTIONAL_EVIDENCE)

    settlement_events = tuple(
        event for event in capture_events if event.event_type == _SETTLEMENT_EVIDENCE_EVENT_TYPE
    )
    settlement_evidence: _SettlementEvidence | None = None
    if not settlement_events:
        _add_reason(reasons, FundingSettlementVerificationReason.MISSING_SETTLEMENT_EVIDENCE)
    elif len(settlement_events) != 1:
        _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_EVIDENCE)
    else:
        settlement_evidence = _parse_settlement(settlement_events[0])
        if settlement_evidence.settlement_time != settlement_time:
            _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_TIME)
        if settlement_evidence.observed_at != settlement_time:
            _add_reason(
                reasons,
                FundingSettlementVerificationReason.INCONSISTENT_SETTLEMENT_EVIDENCE,
            )
        if settlement_evidence.approval_granted is not True:
            _add_reason(reasons, FundingSettlementVerificationReason.UNOBSERVED_SETTLEMENT_EVIDENCE)
        if settlement_evidence.has_unknown_funding:
            _add_reason(reasons, FundingSettlementVerificationReason.UNKNOWN_FUNDING_EVIDENCE)
        if settlement_evidence.has_unknown_notional:
            _add_reason(reasons, FundingSettlementVerificationReason.UNKNOWN_NOTIONAL_EVIDENCE)
        if settlement_evidence.has_unobserved_evidence:
            _add_reason(reasons, FundingSettlementVerificationReason.UNOBSERVED_SETTLEMENT_EVIDENCE)

    if settlement_evidence is not None:
        for checkpoint_evidence in required_checkpoint_evidence:
            funding_can_be_compared = (
                not checkpoint_evidence.has_unknown_funding
                and not settlement_evidence.has_unknown_funding
            )
            if funding_can_be_compared and (
                checkpoint_evidence.risex_expected_funding_usd
                != settlement_evidence.actual_risex_funding_usd
                or checkpoint_evidence.hedge_expected_funding_usd
                != settlement_evidence.actual_hedge_funding_usd
            ):
                _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_FUNDING_EVIDENCE)
            notional_can_be_compared = (
                not checkpoint_evidence.has_unknown_notional
                and not settlement_evidence.has_unknown_notional
            )
            if notional_can_be_compared and (
                checkpoint_evidence.target_notional_usd
                != settlement_evidence.actual_risex_notional_usd
                or checkpoint_evidence.target_notional_usd
                != settlement_evidence.actual_hedge_notional_usd
            ):
                _add_reason(reasons, FundingSettlementVerificationReason.INCONSISTENT_NOTIONAL_EVIDENCE)

    checkpoint_event_sequences = tuple(
        checkpoint_evidence.event.sequence for checkpoint_evidence in required_checkpoint_evidence
    )
    settlement_event_sequence = (
        settlement_evidence.event.sequence if settlement_evidence is not None else None
    )
    verified = (
        not reasons
        and len(checkpoint_event_sequences) == len(REQUIRED_FUNDING_CHECKPOINTS)
        and settlement_event_sequence is not None
    )

    return FundingSettlementVerificationResult(
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        verified=verified,
        reasons=tuple(reasons),
        checkpoint_event_sequences=checkpoint_event_sequences,
        settlement_event_sequence=settlement_event_sequence,
    )


def verify_funding_settlement(
    ledger: Ledger,
    *,
    capture_id: str,
    settlement_time: datetime,
    recorded_at: datetime | None = None,
) -> FundingSettlementVerificationResult:
    """Replay ledger evidence and append the verification result."""

    result = replay_funding_settlement_verification(
        ledger.records(),
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    append_funding_settlement_verification_event(
        ledger,
        capture_id=result.capture_id,
        route_id=result.route_id,
        settlement_time=result.settlement_time,
        verified=result.verified,
        reasons=result.reasons,
        required_checkpoints=_required_checkpoint_labels(),
        checkpoint_event_sequences=result.checkpoint_event_sequences,
        settlement_event_sequence=result.settlement_event_sequence,
        recorded_at=recorded_at or settlement_time,
    )
    return result


def verify_approval_gated_funding_settlement(
    ledger: Ledger,
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    approval_granted: bool,
    observed_at: datetime,
    actual_risex_funding_usd: EstimatedValue,
    actual_hedge_funding_usd: EstimatedValue,
    actual_risex_notional_usd: EstimatedValue,
    actual_hedge_notional_usd: EstimatedValue,
    recorded_at: datetime | None = None,
) -> FundingSettlementVerificationResult:
    """Record approved observed settlement evidence and run canonical verification."""

    if not isinstance(capture, Capture):
        raise ValueError("capture must be a Capture")
    if not isinstance(route, RouteCandidate):
        raise ValueError("route must be a RouteCandidate")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")
    validate_timezone_aware_datetime(observed_at, "observed_at")
    if type(approval_granted) is not bool:
        raise ValueError("approval_granted must be a bool")
    if capture.capture_id != route.capture_id or capture.route_id != route.route_id:
        raise ValueError("capture and route identity must match")
    if capture.settlement_time != settlement_time:
        raise ValueError("capture settlement_time must match settlement_time")

    append_funding_settlement_evidence_event(
        ledger,
        capture_id=capture.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        observed_at=observed_at,
        approval_granted=approval_granted,
        actual_risex_funding_usd=actual_risex_funding_usd,
        actual_hedge_funding_usd=actual_hedge_funding_usd,
        actual_risex_notional_usd=actual_risex_notional_usd,
        actual_hedge_notional_usd=actual_hedge_notional_usd,
        recorded_at=recorded_at or observed_at,
    )
    return verify_funding_settlement(
        ledger,
        capture_id=capture.capture_id,
        settlement_time=settlement_time,
        recorded_at=recorded_at or settlement_time,
    )
