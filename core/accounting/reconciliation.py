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
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
    ExecutableQuote,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import CaptureState, EvaluationMode, RejectReason, RouteStatus, ValueSource


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
    CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION = "CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION"
    MISSING_LIVE_GATE_EVIDENCE_BUNDLE = "MISSING_LIVE_GATE_EVIDENCE_BUNDLE"
    DUPLICATED_LIVE_GATE_EVIDENCE_BUNDLE = "DUPLICATED_LIVE_GATE_EVIDENCE_BUNDLE"
    CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE = "CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE"


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


@dataclass(frozen=True, slots=True)
class LiveGateEvidenceBundleReplayResult:
    """Pure replay result for one recorded fake live-gate evidence bundle check."""

    capture_id: str
    route_id: str | None
    settlement_time: datetime
    evaluated_at: datetime | None
    replayed: bool
    bundle_check_passed: bool
    bundle_check_reason: RejectReason | None
    reasons: tuple[LedgerReconciliationReason, ...]
    live_gate_evidence_bundle_event_sequence: int | None
    route_decision_event_sequence: int | None
    funding_verification_event_sequence: int | None
    ledger_reconciliation_event_sequence: int | None


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
_LIVE_GATE_EVIDENCE_BUNDLE_EVENT_TYPE = (
    LedgerEventType.LIVE_GATE_EVIDENCE_BUNDLE_RECORDED.value
)
_KNOWN_EVENT_TYPES = frozenset(event_type.value for event_type in LedgerEventType)

_PAPER_LIFECYCLE_EVENT_ORDER = (
    _PAPER_OPENED_EVENT_TYPE,
    _PAPER_SETTLEMENT_EVENT_TYPE,
    _PAPER_CLOSED_EVENT_TYPE,
)
_PNL_EXPLANATION_FIELDS = (
    "expected_funding_usd",
    "total_fees_usd",
    "simulated_roundtrip_cost_usd",
    "net_profit_usd",
)
_STARTED_ATTRIBUTION = "entry_paper_eligible_decision"
_BLOCKED_ATTRIBUTION = "paper_start_blocked_by_decision"
_MODE_BLOCKER = "decision_mode_not_entry"
_STATUS_BLOCKER = "decision_status_not_paper_eligible"
_MISSING_PAYLOAD_VALUE = object()
_CAPTURE_SCOPED_EVENT_TYPES = frozenset(
    {
        _PAPER_OPENED_EVENT_TYPE,
        _PAPER_SETTLEMENT_EVENT_TYPE,
        _PAPER_CLOSED_EVENT_TYPE,
        _FUNDING_CHECKPOINT_EVENT_TYPE,
        _FUNDING_SETTLEMENT_EVIDENCE_EVENT_TYPE,
        _FUNDING_VERIFICATION_EVENT_TYPE,
        _LIVE_GATE_EVIDENCE_BUNDLE_EVENT_TYPE,
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


def _pnl_explanation_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    return all(
        field_name in payload and _optional_decimal_payload(payload, field_name)
        for field_name in _PNL_EXPLANATION_FIELDS
    )


def _paper_start_blockers_for_decision_payload(
    *,
    decision_mode: Any,
    decision_status: Any,
) -> tuple[str, ...] | None:
    try:
        mode = EvaluationMode(str(decision_mode))
        status = RouteStatus(str(decision_status))
    except ValueError:
        return None

    blockers: list[str] = []
    if mode is not EvaluationMode.ENTRY:
        blockers.append(_MODE_BLOCKER)
    if status is not RouteStatus.PAPER_ELIGIBLE:
        blockers.append(_STATUS_BLOCKER)
    return tuple(blockers)


def _paper_result_explanation_payload(
    payload: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    raw_explanation = payload.get("paper_result_explanation")
    return raw_explanation if isinstance(raw_explanation, Mapping) else None


def _paper_result_explanation_matches_expected_payload(
    raw_explanation: Mapping[str, Any],
    *,
    route_id: Any,
    decision_mode: Any,
    decision_status: Any,
    decision_reasons: Sequence[str],
    paper_started: bool,
    paper_start_attribution: str,
    paper_start_blockers: Sequence[str],
    net_profit_usd: Any = _MISSING_PAYLOAD_VALUE,
) -> bool:
    raw_pnl_explanation = raw_explanation.get("pnl_explanation")
    if not isinstance(raw_pnl_explanation, Mapping):
        return False

    return (
        raw_explanation.get("route_id") == route_id
        and raw_explanation.get("decision_mode") == decision_mode
        and raw_explanation.get("decision_status") == decision_status
        and _payload_str_sequence(raw_explanation, "decision_reasons")
        == tuple(decision_reasons)
        and raw_explanation.get("paper_started") is paper_started
        and raw_explanation.get("paper_start_attribution") == paper_start_attribution
        and _payload_str_sequence(raw_explanation, "paper_start_blockers")
        == tuple(paper_start_blockers)
        and (
            net_profit_usd is _MISSING_PAYLOAD_VALUE
            or raw_pnl_explanation.get("net_profit_usd") == net_profit_usd
        )
    )


def _optional_paper_result_explanation_is_well_formed(
    payload: Mapping[str, Any],
    *,
    expected_paper_started: bool,
) -> bool:
    raw_explanation = payload.get("paper_result_explanation")
    if raw_explanation is None:
        return True
    if not isinstance(raw_explanation, Mapping):
        return False
    route_id = _payload_str(payload, "route_id")
    explanation_route_id = _payload_str(raw_explanation, "route_id")
    if route_id is None or explanation_route_id != route_id:
        return False
    decision_reasons = _payload_str_sequence(raw_explanation, "decision_reasons")
    if decision_reasons is None:
        return False
    try:
        EvaluationMode(str(raw_explanation.get("decision_mode")))
        RouteStatus(str(raw_explanation.get("decision_status")))
        for reason in decision_reasons:
            RejectReason(reason)
    except ValueError:
        return False

    blockers = _payload_str_sequence(raw_explanation, "paper_start_blockers")
    raw_pnl_explanation = raw_explanation.get("pnl_explanation")
    paper_started = raw_explanation.get("paper_started")
    return (
        _payload_str(raw_explanation, "route_id") is not None
        and type(paper_started) is bool
        and paper_started is expected_paper_started
        and _payload_str(raw_explanation, "paper_start_attribution") is not None
        and blockers is not None
        and ((paper_started and not blockers) or (not paper_started and bool(blockers)))
        and isinstance(raw_pnl_explanation, Mapping)
        and _pnl_explanation_payload_is_well_formed(raw_pnl_explanation)
    )


def _paper_rejection_explanation_matches_event_payload(payload: Mapping[str, Any]) -> bool:
    raw_explanation = _paper_result_explanation_payload(payload)
    if raw_explanation is None:
        return True

    decision_reasons = _payload_str_sequence(payload, "reasons")
    blockers = _paper_start_blockers_for_decision_payload(
        decision_mode=payload.get("mode"),
        decision_status=payload.get("status"),
    )
    if decision_reasons is None or blockers is None:
        return True

    return _paper_result_explanation_matches_expected_payload(
        raw_explanation,
        route_id=payload.get("route_id"),
        decision_mode=payload.get("mode"),
        decision_status=payload.get("status"),
        decision_reasons=decision_reasons,
        paper_started=False,
        paper_start_attribution=_BLOCKED_ATTRIBUTION,
        paper_start_blockers=blockers,
    )


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
        and _optional_paper_result_explanation_is_well_formed(
            payload,
            expected_paper_started=True,
        )
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
        and _optional_paper_result_explanation_is_well_formed(
            payload,
            expected_paper_started=False,
        )
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


def _payload_mapping(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any] | None:
    value = payload.get(field_name)
    return value if isinstance(value, Mapping) else None


def _decimal_from_required_payload(payload: Mapping[str, Any], field_name: str) -> Decimal:
    value = _finite_decimal(payload.get(field_name))
    if value is None:
        raise ValueError(f"{field_name} must be a finite decimal")
    return value


def _decimal_from_optional_payload(payload: Mapping[str, Any], field_name: str) -> Decimal | None:
    raw_value = payload.get(field_name)
    if raw_value is None:
        return None
    value = _finite_decimal(raw_value)
    if value is None:
        raise ValueError(f"{field_name} must be a finite decimal or None")
    return value


def _datetime_from_required_payload(payload: Mapping[str, Any], field_name: str) -> datetime:
    value = _payload_datetime(payload, field_name)
    if value is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value


def _str_from_required_payload(payload: Mapping[str, Any], field_name: str) -> str:
    value = _payload_str(payload, field_name)
    if value is None:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _sequence_from_required_payload(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[Mapping[str, Any], ...]:
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, tuple | list):
        raise ValueError(f"{field_name} must be a sequence")
    parsed: list[Mapping[str, Any]] = []
    for item in raw_value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name} must contain mappings")
        parsed.append(item)
    return tuple(parsed)


def _route_from_payload(payload: Mapping[str, Any]) -> RouteCandidate:
    target_notional_usd = _decimal_from_required_payload(payload, "target_notional_usd")
    if target_notional_usd <= Decimal("0"):
        raise ValueError("target_notional_usd must be positive")
    return RouteCandidate(
        route_id=_str_from_required_payload(payload, "route_id"),
        capture_id=_str_from_required_payload(payload, "capture_id"),
        risex_venue=_str_from_required_payload(payload, "risex_venue"),
        risex_symbol=_str_from_required_payload(payload, "risex_symbol"),
        risex_entry_side=_str_from_required_payload(payload, "risex_entry_side"),
        hedge_venue=_str_from_required_payload(payload, "hedge_venue"),
        hedge_symbol=_str_from_required_payload(payload, "hedge_symbol"),
        hedge_entry_side=_str_from_required_payload(payload, "hedge_entry_side"),
        target_notional_usd=target_notional_usd,
    )


def _quote_from_payload(payload: Mapping[str, Any]) -> ExecutableQuote:
    consumed_levels = payload.get("consumed_levels")
    if type(consumed_levels) is not int or consumed_levels < 0:
        raise ValueError("consumed_levels must be a non-negative integer")
    executable = payload.get("executable")
    if type(executable) is not bool:
        raise ValueError("executable must be a bool")

    return ExecutableQuote(
        venue=_str_from_required_payload(payload, "venue"),
        symbol=_str_from_required_payload(payload, "symbol"),
        side=_str_from_required_payload(payload, "side"),
        target_notional_usd=_decimal_from_required_payload(payload, "target_notional_usd"),
        vwap_price=_decimal_from_optional_payload(payload, "vwap_price"),
        executable=executable,
        source=ValueSource(str(payload.get("source"))),
        consumed_base_quantity=_decimal_from_optional_payload(
            payload,
            "consumed_base_quantity",
        ),
        consumed_levels=consumed_levels,
        notional_filled_usd=_decimal_from_optional_payload(
            payload,
            "notional_filled_usd",
        ),
        best_price=_decimal_from_optional_payload(payload, "best_price"),
        worst_price=_decimal_from_optional_payload(payload, "worst_price"),
        price_impact_bps=_decimal_from_optional_payload(payload, "price_impact_bps"),
    )


def _capture_plan_evidence_from_payload(
    payload: Mapping[str, Any],
) -> CapturePlanFreshnessEvidence:
    ledger_reconciliation_event_sequence = _payload_optional_int(
        payload,
        "ledger_reconciliation_event_sequence",
    )
    if ledger_reconciliation_event_sequence == 0:
        raise ValueError("ledger_reconciliation_event_sequence must be positive or None")
    return CapturePlanFreshnessEvidence(
        plan_id=_str_from_required_payload(payload, "plan_id"),
        plan_version=_str_from_required_payload(payload, "plan_version"),
        capture_id=_str_from_required_payload(payload, "capture_id"),
        route_id=_str_from_required_payload(payload, "route_id"),
        settlement_time=_datetime_from_required_payload(payload, "settlement_time"),
        planned_at=_datetime_from_required_payload(payload, "planned_at"),
        valid_until=_datetime_from_required_payload(payload, "valid_until"),
        source=ValueSource(str(payload.get("source"))),
        ledger_reconciliation_event_sequence=ledger_reconciliation_event_sequence,
    )


def _execution_capability_evidence_from_payload(
    payload: Mapping[str, Any],
) -> ExecutionCapabilityEvidence:
    quote_payloads = {
        field_name: _payload_mapping(payload, field_name)
        for field_name in (
            "risex_entry_quote",
            "hedge_entry_quote",
            "risex_estimated_exit_quote",
            "hedge_estimated_exit_quote",
        )
    }
    if any(value is None for value in quote_payloads.values()):
        raise ValueError("execution capability evidence requires all quote payloads")

    return ExecutionCapabilityEvidence(
        capture_id=_str_from_required_payload(payload, "capture_id"),
        route_id=_str_from_required_payload(payload, "route_id"),
        settlement_time=_datetime_from_required_payload(payload, "settlement_time"),
        checked_at=_datetime_from_required_payload(payload, "checked_at"),
        valid_until=_datetime_from_required_payload(payload, "valid_until"),
        source=ValueSource(str(payload.get("source"))),
        risex_entry_quote=_quote_from_payload(quote_payloads["risex_entry_quote"]),
        hedge_entry_quote=_quote_from_payload(quote_payloads["hedge_entry_quote"]),
        risex_estimated_exit_quote=_quote_from_payload(
            quote_payloads["risex_estimated_exit_quote"]
        ),
        hedge_estimated_exit_quote=_quote_from_payload(
            quote_payloads["hedge_estimated_exit_quote"]
        ),
    )


def _live_gate_evidence_bundle_from_payload(
    payload: Mapping[str, Any],
) -> LiveGateEvidenceBundle:
    funding_settlement_verified = payload.get("funding_settlement_verified")
    ledger_explicitly_reconciled = payload.get("ledger_explicitly_reconciled")
    if type(funding_settlement_verified) is not bool:
        raise ValueError("funding_settlement_verified must be a bool")
    if type(ledger_explicitly_reconciled) is not bool:
        raise ValueError("ledger_explicitly_reconciled must be a bool")

    return LiveGateEvidenceBundle(
        capture_id=_str_from_required_payload(payload, "capture_id"),
        route_id=_str_from_required_payload(payload, "route_id"),
        settlement_time=_datetime_from_required_payload(payload, "settlement_time"),
        funding_settlement_verified=funding_settlement_verified,
        ledger_explicitly_reconciled=ledger_explicitly_reconciled,
        capture_plan_evidence=tuple(
            _capture_plan_evidence_from_payload(item)
            for item in _sequence_from_required_payload(payload, "capture_plan_evidence")
        ),
        execution_capability_evidence=tuple(
            _execution_capability_evidence_from_payload(item)
            for item in _sequence_from_required_payload(
                payload,
                "execution_capability_evidence",
            )
        ),
    )


def _bundle_check_reason_from_payload(
    payload: Mapping[str, Any],
) -> RejectReason | None:
    raw_reason = payload.get("bundle_check_reason")
    if raw_reason is None:
        return None
    if not isinstance(raw_reason, str):
        raise ValueError("bundle_check_reason must be a reject reason string or None")
    return RejectReason(raw_reason)


def _live_gate_bundle_payload_is_well_formed(payload: Mapping[str, Any]) -> bool:
    route_payload = _payload_mapping(payload, "route")
    bundle_payload = _payload_mapping(payload, "live_gate_evidence_bundle")
    if route_payload is None or bundle_payload is None:
        return False
    try:
        route = _route_from_payload(route_payload)
        _live_gate_evidence_bundle_from_payload(bundle_payload)
        _datetime_from_required_payload(payload, "settlement_time")
        _datetime_from_required_payload(payload, "evaluated_at")
        bundle_check_reason = _bundle_check_reason_from_payload(payload)
    except (ValueError, TypeError):
        return False

    bundle_check_passed = payload.get("bundle_check_passed")
    return (
        payload.get("capture_id") == route.capture_id
        and payload.get("route_id") == route.route_id
        and type(bundle_check_passed) is bool
        and (
            (bundle_check_passed and bundle_check_reason is None)
            or (not bundle_check_passed and bundle_check_reason is not None)
        )
        and _payload_int(payload, "route_decision_event_sequence") is not None
        and _payload_int(payload, "funding_verification_event_sequence") is not None
        and _payload_int(payload, "ledger_reconciliation_event_sequence") is not None
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
    if event.event_type == _LIVE_GATE_EVIDENCE_BUNDLE_EVENT_TYPE:
        return _live_gate_bundle_payload_is_well_formed(payload)
    return False


def _validate_well_formed_event_payload_semantics(
    event: LedgerEvent,
    reasons: list[LedgerReconciliationReason],
) -> None:
    if event.event_type == LedgerEventType.PAPER_REJECTION_RECORDED.value and (
        not _paper_rejection_explanation_matches_event_payload(event.payload)
    ):
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)


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
            continue
        _validate_well_formed_event_payload_semantics(event, reasons)
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


def _validate_opened_paper_result_explanation(
    *,
    opened_event: LedgerEvent,
    route_decision: LedgerEvent | None,
    reasons: list[LedgerReconciliationReason],
) -> None:
    if route_decision is None:
        return
    raw_explanation = _paper_result_explanation_payload(opened_event.payload)
    if raw_explanation is None:
        return

    decision_reasons = _payload_str_sequence(route_decision.payload, "reasons")
    if decision_reasons is None:
        return

    net_profit_usd = (
        route_decision.payload.get("net_profit_usd")
        if "net_profit_usd" in route_decision.payload
        else _MISSING_PAYLOAD_VALUE
    )
    if not _paper_result_explanation_matches_expected_payload(
        raw_explanation,
        route_id=route_decision.payload.get("route_id"),
        decision_mode=route_decision.payload.get("mode"),
        decision_status=route_decision.payload.get("status"),
        decision_reasons=decision_reasons,
        paper_started=True,
        paper_start_attribution=_STARTED_ATTRIBUTION,
        paper_start_blockers=(),
        net_profit_usd=net_profit_usd,
    ):
        _add_reason(reasons, LedgerReconciliationReason.CONTRADICTORY_LEDGER_EVIDENCE)


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
        opened_event = next(
            event for event in paper_events if event.event_type == _PAPER_OPENED_EVENT_TYPE
        )
        _validate_opened_paper_result_explanation(
            opened_event=opened_event,
            route_decision=route_decision,
            reasons=reasons,
        )
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


def _recorded_funding_reasons(payload: Mapping[str, Any]) -> tuple[str, ...]:
    reasons = _payload_str_sequence(payload, "reasons")
    return reasons if reasons is not None else ()


def _funding_verification_matches_canonical_replay(
    *,
    verification_event: LedgerEvent,
    events: Sequence[LedgerEvent],
    capture_id: str,
    settlement_time: datetime,
) -> bool:
    from core.monitoring.funding_settlement import (
        REQUIRED_FUNDING_CHECKPOINTS,
        replay_funding_settlement_verification,
    )

    replayed_result = replay_funding_settlement_verification(
        events,
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    canonical_required_checkpoints = tuple(
        requirement.checkpoint.value for requirement in REQUIRED_FUNDING_CHECKPOINTS
    )
    recorded_required_checkpoints = _payload_str_sequence(
        verification_event.payload,
        "required_checkpoints",
    )
    recorded_checkpoint_sequences = _payload_int_sequence(
        verification_event.payload,
        "checkpoint_event_sequences",
    )
    recorded_settlement_sequence = _payload_optional_int(
        verification_event.payload,
        "settlement_event_sequence",
    )
    recorded_settlement_sequence = None if recorded_settlement_sequence == 0 else recorded_settlement_sequence

    return (
        recorded_required_checkpoints == canonical_required_checkpoints
        and verification_event.payload.get("capture_id") == replayed_result.capture_id
        and verification_event.payload.get("route_id") == replayed_result.route_id
        and _payload_datetime(verification_event.payload, "settlement_time")
        == replayed_result.settlement_time
        and verification_event.payload.get("verified") == replayed_result.verified
        and _recorded_funding_reasons(verification_event.payload)
        == tuple(reason.value for reason in replayed_result.reasons)
        and recorded_checkpoint_sequences == replayed_result.checkpoint_event_sequences
        and recorded_settlement_sequence == replayed_result.settlement_event_sequence
    )


def _validate_funding_verification(
    *,
    events: Sequence[LedgerEvent],
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
    if not _funding_verification_matches_canonical_replay(
        verification_event=verification_event,
        events=events,
        capture_id=capture_id,
        settlement_time=settlement_time,
    ):
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_FUNDING_SETTLEMENT_VERIFICATION,
        )
    return verification_event


def _live_gate_bundle_events_for_capture(
    events: Sequence[LedgerEvent],
    capture_id: str,
) -> tuple[LedgerEvent, ...]:
    return tuple(
        event
        for event in events
        if event.event_type == _LIVE_GATE_EVIDENCE_BUNDLE_EVENT_TYPE
        and event.payload.get("capture_id") == capture_id
    )


def _live_gate_bundle_replay_result(
    *,
    capture_id: str,
    route_id: str | None,
    settlement_time: datetime,
    evaluated_at: datetime | None = None,
    replayed: bool = False,
    bundle_check_passed: bool = False,
    bundle_check_reason: RejectReason | None = None,
    reasons: Sequence[LedgerReconciliationReason],
    live_gate_evidence_bundle_event_sequence: int | None = None,
    route_decision_event_sequence: int | None = None,
    funding_verification_event_sequence: int | None = None,
    ledger_reconciliation_event_sequence: int | None = None,
) -> LiveGateEvidenceBundleReplayResult:
    return LiveGateEvidenceBundleReplayResult(
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
        replayed=replayed,
        bundle_check_passed=bundle_check_passed,
        bundle_check_reason=bundle_check_reason,
        reasons=tuple(reasons),
        live_gate_evidence_bundle_event_sequence=live_gate_evidence_bundle_event_sequence,
        route_decision_event_sequence=route_decision_event_sequence,
        funding_verification_event_sequence=funding_verification_event_sequence,
        ledger_reconciliation_event_sequence=ledger_reconciliation_event_sequence,
    )


def _validate_referenced_live_gate_bundle_history(
    *,
    bundle_event: LedgerEvent,
    event_by_sequence: Mapping[int, LedgerEvent],
    route: RouteCandidate,
    settlement_time: datetime,
    route_decision_event_sequence: int,
    funding_verification_event_sequence: int,
    ledger_reconciliation_event_sequence: int,
    reasons: list[LedgerReconciliationReason],
) -> None:
    route_decision_event = event_by_sequence.get(route_decision_event_sequence)
    funding_verification_event = event_by_sequence.get(funding_verification_event_sequence)
    ledger_reconciliation_event = event_by_sequence.get(ledger_reconciliation_event_sequence)

    if (
        route_decision_event is None
        or route_decision_event.event_type != _ROUTE_DECISION_EVENT_TYPE
        or route_decision_event.payload.get("route_id") != route.route_id
        or route_decision_event.payload.get("mode") != EvaluationMode.ENTRY.value
        or route_decision_event.payload.get("status") != RouteStatus.PAPER_ELIGIBLE.value
        or route_decision_event.payload.get("has_capture_plan") is not False
    ):
        _add_reason(reasons, LedgerReconciliationReason.MISSING_ROUTE_DECISION)
    elif route_decision_event.sequence >= bundle_event.sequence:
        _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)

    if (
        funding_verification_event is None
        or funding_verification_event.event_type != _FUNDING_VERIFICATION_EVENT_TYPE
        or funding_verification_event.payload.get("capture_id") != route.capture_id
        or funding_verification_event.payload.get("route_id") != route.route_id
        or _payload_datetime(funding_verification_event.payload, "settlement_time")
        != settlement_time
        or funding_verification_event.payload.get("verified") is not True
    ):
        _add_reason(
            reasons,
            LedgerReconciliationReason.MISSING_FUNDING_SETTLEMENT_VERIFICATION,
        )
    elif funding_verification_event.sequence >= bundle_event.sequence:
        _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)

    if (
        ledger_reconciliation_event is None
        or ledger_reconciliation_event.event_type != _LEDGER_RECONCILIATION_EVENT_TYPE
        or ledger_reconciliation_event.payload.get("capture_id") != route.capture_id
        or ledger_reconciliation_event.payload.get("route_id") != route.route_id
        or _payload_datetime(ledger_reconciliation_event.payload, "settlement_time")
        != settlement_time
        or ledger_reconciliation_event.payload.get("reconciled") is not True
        or ledger_reconciliation_event.payload.get("route_decision_event_sequence")
        != route_decision_event_sequence
        or ledger_reconciliation_event.payload.get("funding_verification_event_sequence")
        != funding_verification_event_sequence
    ):
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
        )
    else:
        if ledger_reconciliation_event.sequence >= bundle_event.sequence:
            _add_reason(reasons, LedgerReconciliationReason.OUT_OF_ORDER_LEDGER_EVIDENCE)
        if ledger_reconciliation_event.sequence != bundle_event.sequence - 1:
            _add_reason(
                reasons,
                LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
            )
        referenced_reconciliation_prefix = tuple(
            event
            for event in event_by_sequence.values()
            if event.sequence <= ledger_reconciliation_event.sequence
        )
        referenced_reconciliation_prefix = tuple(
            sorted(referenced_reconciliation_prefix, key=lambda event: event.sequence)
        )
        if not is_ledger_explicitly_reconciled(referenced_reconciliation_prefix):
            _add_reason(
                reasons,
                LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
            )


def _validate_live_gate_bundle_plan_references(
    *,
    bundle: LiveGateEvidenceBundle,
    ledger_reconciliation_event_sequence: int,
    reasons: list[LedgerReconciliationReason],
) -> None:
    if len(bundle.capture_plan_evidence) != 1:
        return
    plan_evidence = bundle.capture_plan_evidence[0]
    if plan_evidence.ledger_reconciliation_event_sequence != ledger_reconciliation_event_sequence:
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
        )


def replay_live_gate_evidence_bundle_recording(
    events: Sequence[LedgerEvent],
    *,
    capture_id: str,
    settlement_time: datetime,
) -> LiveGateEvidenceBundleReplayResult:
    """Replay one recorded fake live-gate evidence bundle check result."""

    if not capture_id.strip():
        raise ValueError("capture_id must be non-empty")
    validate_timezone_aware_datetime(settlement_time, "settlement_time")

    reasons: list[LedgerReconciliationReason] = []
    supplied_events = _validate_supplied_ledger_history(events, reasons)
    event_by_sequence = _event_by_sequence(supplied_events, reasons)
    bundle_events = _live_gate_bundle_events_for_capture(supplied_events, capture_id)
    if not bundle_events:
        _add_reason(reasons, LedgerReconciliationReason.MISSING_LIVE_GATE_EVIDENCE_BUNDLE)
        return _live_gate_bundle_replay_result(
            capture_id=capture_id,
            route_id=None,
            settlement_time=settlement_time,
            reasons=reasons,
        )
    if len(bundle_events) != 1:
        _add_reason(
            reasons,
            LedgerReconciliationReason.DUPLICATED_LIVE_GATE_EVIDENCE_BUNDLE,
        )
        return _live_gate_bundle_replay_result(
            capture_id=capture_id,
            route_id=None,
            settlement_time=settlement_time,
            reasons=reasons,
        )

    bundle_event = bundle_events[0]
    route_payload = _payload_mapping(bundle_event.payload, "route")
    bundle_payload = _payload_mapping(bundle_event.payload, "live_gate_evidence_bundle")
    if route_payload is None or bundle_payload is None:
        _add_reason(reasons, LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD)
        return _live_gate_bundle_replay_result(
            capture_id=capture_id,
            route_id=None,
            settlement_time=settlement_time,
            reasons=reasons,
            live_gate_evidence_bundle_event_sequence=bundle_event.sequence,
        )

    try:
        route = _route_from_payload(route_payload)
        bundle = _live_gate_evidence_bundle_from_payload(bundle_payload)
        event_settlement_time = _datetime_from_required_payload(
            bundle_event.payload,
            "settlement_time",
        )
        evaluated_at = _datetime_from_required_payload(bundle_event.payload, "evaluated_at")
        recorded_reason = _bundle_check_reason_from_payload(bundle_event.payload)
    except (ValueError, TypeError):
        _add_reason(reasons, LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD)
        return _live_gate_bundle_replay_result(
            capture_id=capture_id,
            route_id=None,
            settlement_time=settlement_time,
            reasons=reasons,
            live_gate_evidence_bundle_event_sequence=bundle_event.sequence,
        )

    recorded_passed = bundle_event.payload.get("bundle_check_passed")
    route_decision_event_sequence = _payload_int(
        bundle_event.payload,
        "route_decision_event_sequence",
    )
    funding_verification_event_sequence = _payload_int(
        bundle_event.payload,
        "funding_verification_event_sequence",
    )
    ledger_reconciliation_event_sequence = _payload_int(
        bundle_event.payload,
        "ledger_reconciliation_event_sequence",
    )

    if (
        event_settlement_time != settlement_time
        or bundle_event.payload.get("capture_id") != capture_id
        or bundle_event.payload.get("route_id") != route.route_id
        or route.capture_id != capture_id
    ):
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
        )
    if type(recorded_passed) is not bool:
        _add_reason(reasons, LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD)
        recorded_passed = False
    if (recorded_passed and recorded_reason is not None) or (
        not recorded_passed and recorded_reason is None
    ):
        _add_reason(reasons, LedgerReconciliationReason.MALFORMED_LEDGER_EVENT_PAYLOAD)
    if (
        route_decision_event_sequence is None
        or funding_verification_event_sequence is None
        or ledger_reconciliation_event_sequence is None
    ):
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
        )
    else:
        _validate_referenced_live_gate_bundle_history(
            bundle_event=bundle_event,
            event_by_sequence=event_by_sequence,
            route=route,
            settlement_time=event_settlement_time,
            route_decision_event_sequence=route_decision_event_sequence,
            funding_verification_event_sequence=funding_verification_event_sequence,
            ledger_reconciliation_event_sequence=ledger_reconciliation_event_sequence,
            reasons=reasons,
        )
        _validate_live_gate_bundle_plan_references(
            bundle=bundle,
            ledger_reconciliation_event_sequence=ledger_reconciliation_event_sequence,
            reasons=reasons,
        )

    from core.risk.gates import check_live_gate_evidence_bundle

    replayed_passed, replayed_reason = check_live_gate_evidence_bundle(
        route=route,
        settlement_time=event_settlement_time,
        evaluated_at=evaluated_at,
        live_gate_evidence_bundle=bundle,
    )
    if replayed_passed != recorded_passed or replayed_reason != recorded_reason:
        _add_reason(
            reasons,
            LedgerReconciliationReason.CONTRADICTORY_LIVE_GATE_EVIDENCE_BUNDLE,
        )

    return _live_gate_bundle_replay_result(
        capture_id=capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
        replayed=not reasons,
        bundle_check_passed=bool(recorded_passed),
        bundle_check_reason=recorded_reason,
        reasons=reasons,
        live_gate_evidence_bundle_event_sequence=bundle_event.sequence,
        route_decision_event_sequence=route_decision_event_sequence,
        funding_verification_event_sequence=funding_verification_event_sequence,
        ledger_reconciliation_event_sequence=ledger_reconciliation_event_sequence,
    )


def _validate_live_gate_bundle_recording_for_reconciliation(
    *,
    events: Sequence[LedgerEvent],
    capture_id: str,
    settlement_time: datetime,
    reasons: list[LedgerReconciliationReason],
) -> tuple[int, ...]:
    live_gate_bundle_events = _live_gate_bundle_events_for_capture(events, capture_id)
    if not live_gate_bundle_events:
        return ()

    replayed = replay_live_gate_evidence_bundle_recording(
        events,
        capture_id=capture_id,
        settlement_time=settlement_time,
    )
    if not replayed.replayed:
        for reason in replayed.reasons:
            _add_reason(reasons, reason)
    return tuple(event.sequence for event in live_gate_bundle_events)


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
        events=supplied_events,
        capture_events=capture_events,
        event_by_sequence=event_by_sequence,
        paper_event_sequences=paper_event_sequences,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement_time,
        reasons=reasons,
    )
    live_gate_bundle_event_sequences = _validate_live_gate_bundle_recording_for_reconciliation(
        events=supplied_events,
        capture_id=capture_id,
        settlement_time=settlement_time,
        reasons=reasons,
    )

    checked_event_sequences = set(paper_event_sequences)
    if route_decision is not None:
        checked_event_sequences.add(route_decision.sequence)
    checked_event_sequences.update(live_gate_bundle_event_sequences)
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
