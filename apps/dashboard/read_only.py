"""Read-only dashboard rendering for already-derived Capture evidence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from core.accounting.reconciliation import LedgerReconciliationResult
from core.domain.contracts import (
    Capture,
    CapturePlanFreshnessEvidence,
    DecisionResult,
    ExecutionCapabilityEvidence,
    LiveGateEvidenceBundle,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode, RouteStatus
from core.monitoring.funding_settlement import FundingSettlementVerificationResult

_AVAILABLE = "available"
_BLOCKED = "blocked"
_MISSING = "missing"


def render_capture_monitor_view(
    *,
    capture: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
    decision: object | None = None,
    funding_verification: object | None = None,
    ledger_reconciliation: object | None = None,
    live_gate_evidence_bundle: object | None = None,
    non_sending_plan: object | None = None,
    guarded_readiness: object | None = None,
    approval: object | None = None,
    approval_boundary_result: object | None = None,
) -> dict[str, object]:
    """Render one read-only Capture/route monitor view from supplied evidence."""

    identity = _identity_section(
        capture=capture,
        route=route,
        settlement_time=settlement_time,
        viewed_at=viewed_at,
    )
    if identity["display_state"] == _AVAILABLE:
        assert isinstance(capture, Capture)
        assert isinstance(route, RouteCandidate)
        assert isinstance(settlement_time, datetime)
        assert isinstance(viewed_at, datetime)

    sections = {
        "identity": identity,
        "decision": _decision_section(decision=decision, route=route),
        "funding_verification": _funding_verification_section(
            funding_verification=funding_verification,
            route=route,
            settlement_time=settlement_time,
        ),
        "ledger_reconciliation": _ledger_reconciliation_section(
            ledger_reconciliation=ledger_reconciliation,
            route=route,
            settlement_time=settlement_time,
        ),
        "live_gate_evidence_bundle": _live_gate_bundle_section(
            live_gate_evidence_bundle=live_gate_evidence_bundle,
            route=route,
            settlement_time=settlement_time,
            viewed_at=viewed_at,
        ),
        "non_sending_plan": _non_sending_plan_section(
            non_sending_plan=non_sending_plan,
            route=route,
            settlement_time=settlement_time,
            viewed_at=viewed_at,
            ledger_reconciliation=ledger_reconciliation,
            live_gate_evidence_bundle=live_gate_evidence_bundle,
        ),
        "guarded_readiness": _guarded_readiness_section(
            guarded_readiness=guarded_readiness,
            route=route,
            settlement_time=settlement_time,
            viewed_at=viewed_at,
            non_sending_plan=non_sending_plan,
        ),
        "approval": _approval_section(
            approval=approval,
            route=route,
            settlement_time=settlement_time,
            viewed_at=viewed_at,
            guarded_readiness=guarded_readiness,
            non_sending_plan=non_sending_plan,
        ),
        "approval_boundary_result": _approval_boundary_section(
            approval_boundary_result=approval_boundary_result,
            route=route,
            settlement_time=settlement_time,
            viewed_at=viewed_at,
            approval=approval,
        ),
    }
    unavailable_sections = tuple(
        name for name, section in sections.items() if section["display_state"] != _AVAILABLE
    )
    return {
        "display_state": _AVAILABLE if not unavailable_sections else _BLOCKED,
        "unavailable_sections": unavailable_sections,
        "sections": sections,
    }


def _identity_section(
    *,
    capture: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
) -> dict[str, object]:
    if type(capture) is not Capture:
        return _missing_section("capture_missing_or_malformed")
    if type(route) is not RouteCandidate:
        return _missing_section("route_missing_or_malformed")
    if not _timezone_aware(settlement_time):
        return _missing_section("settlement_time_missing_or_malformed")
    if not _timezone_aware(viewed_at):
        return _missing_section("viewed_at_missing_or_malformed")
    assert isinstance(settlement_time, datetime)
    assert isinstance(viewed_at, datetime)

    target_notional_usd = _decimal_maybe_text(route.target_notional_usd)
    payload = {
        "capture_id": capture.capture_id,
        "route_id": route.route_id,
        "settlement_time": _iso(settlement_time),
        "viewed_at": _iso(viewed_at),
        "capture_state": _enum_value(capture.state),
        "risex": {
            "venue": route.risex_venue,
            "symbol": route.risex_symbol,
            "entry_side": route.risex_entry_side,
        },
        "hedge": {
            "venue": route.hedge_venue,
            "symbol": route.hedge_symbol,
            "entry_side": route.hedge_entry_side,
        },
        "target_notional_usd": target_notional_usd,
    }
    if target_notional_usd is None:
        return _blocked_section("route_notional_missing_or_malformed", **payload)
    if (
        capture.capture_id != route.capture_id
        or capture.route_id != route.route_id
        or capture.settlement_time != settlement_time
    ):
        return _blocked_section("cross_identity_or_settlement", **payload)
    return _available_section(**payload)


def _decision_section(*, decision: object, route: object) -> dict[str, object]:
    if type(decision) is not DecisionResult:
        return _missing_section("decision_missing_or_malformed")
    payload = {
        "route_id": decision.route_id,
        "mode": _enum_value(decision.mode),
        "status": _enum_value(decision.status),
        "reasons": _enum_values(decision.reasons),
        "decided_at": _iso(decision.decided_at) if _timezone_aware(decision.decided_at) else None,
        "economics": _decision_economics(decision),
    }
    if type(route) is not RouteCandidate or decision.route_id != route.route_id:
        return _blocked_section("cross_route_decision", **payload)
    if not _timezone_aware(decision.decided_at):
        return _blocked_section("decision_time_missing_or_malformed", **payload)
    if decision.mode is not EvaluationMode.ENTRY or decision.status is not RouteStatus.PAPER_ELIGIBLE:
        return _blocked_section("decision_not_entry_paper_eligible", **payload)
    return _available_section(**payload)


def _funding_verification_section(
    *,
    funding_verification: object,
    route: object,
    settlement_time: object,
) -> dict[str, object]:
    if type(funding_verification) is not FundingSettlementVerificationResult:
        return _missing_section("funding_verification_missing_or_malformed")
    payload = {
        "capture_id": funding_verification.capture_id,
        "route_id": funding_verification.route_id,
        "settlement_time": _maybe_iso(funding_verification.settlement_time),
        "verified": funding_verification.verified,
        "reasons": _enum_values(funding_verification.reasons),
        "checkpoint_event_sequences": funding_verification.checkpoint_event_sequences,
        "settlement_event_sequence": funding_verification.settlement_event_sequence,
    }
    if (
        type(route) is not RouteCandidate
        or not _timezone_aware(settlement_time)
        or funding_verification.capture_id != route.capture_id
        or funding_verification.route_id != route.route_id
        or funding_verification.settlement_time != settlement_time
    ):
        return _blocked_section("cross_identity_funding_verification", **payload)
    if funding_verification.verified is not True:
        return _blocked_section("funding_not_verified", **payload)
    if not _positive_sequence_values(funding_verification.checkpoint_event_sequences):
        return _blocked_section("funding_checkpoint_sequences_missing", **payload)
    if not _positive_sequence(funding_verification.settlement_event_sequence):
        return _blocked_section("funding_settlement_sequence_missing", **payload)
    return _available_section(**payload)


def _ledger_reconciliation_section(
    *,
    ledger_reconciliation: object,
    route: object,
    settlement_time: object,
) -> dict[str, object]:
    if type(ledger_reconciliation) is not LedgerReconciliationResult:
        return _missing_section("ledger_reconciliation_missing_or_malformed")
    payload = {
        "capture_id": ledger_reconciliation.capture_id,
        "route_id": ledger_reconciliation.route_id,
        "settlement_time": _maybe_iso(ledger_reconciliation.settlement_time),
        "reconciled": ledger_reconciliation.reconciled,
        "reasons": _enum_values(ledger_reconciliation.reasons),
        "route_decision_event_sequence": ledger_reconciliation.route_decision_event_sequence,
        "funding_verification_event_sequence": (
            ledger_reconciliation.funding_verification_event_sequence
        ),
        "checked_event_sequences": ledger_reconciliation.checked_event_sequences,
    }
    if (
        type(route) is not RouteCandidate
        or not _timezone_aware(settlement_time)
        or ledger_reconciliation.capture_id != route.capture_id
        or ledger_reconciliation.route_id != route.route_id
        or ledger_reconciliation.settlement_time != settlement_time
    ):
        return _blocked_section("cross_identity_ledger_reconciliation", **payload)
    if ledger_reconciliation.reconciled is not True:
        return _blocked_section("ledger_not_reconciled", **payload)
    if not _positive_sequence_values(ledger_reconciliation.checked_event_sequences):
        return _blocked_section("ledger_checked_sequences_missing", **payload)
    if not _positive_sequence(ledger_reconciliation.route_decision_event_sequence):
        return _blocked_section("ledger_route_decision_sequence_missing", **payload)
    if not _positive_sequence(ledger_reconciliation.funding_verification_event_sequence):
        return _blocked_section("ledger_funding_sequence_missing", **payload)
    if (
        ledger_reconciliation.route_decision_event_sequence
        not in ledger_reconciliation.checked_event_sequences
        or ledger_reconciliation.funding_verification_event_sequence
        not in ledger_reconciliation.checked_event_sequences
    ):
        return _blocked_section("ledger_prerequisite_sequences_not_checked", **payload)
    return _available_section(**payload)


def _live_gate_bundle_section(
    *,
    live_gate_evidence_bundle: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
) -> dict[str, object]:
    if type(live_gate_evidence_bundle) is not LiveGateEvidenceBundle:
        return _missing_section("live_gate_bundle_missing_or_malformed")
    capture_plan_evidence = live_gate_evidence_bundle.capture_plan_evidence
    execution_capability_evidence = live_gate_evidence_bundle.execution_capability_evidence
    payload = {
        "capture_id": live_gate_evidence_bundle.capture_id,
        "route_id": live_gate_evidence_bundle.route_id,
        "settlement_time": _maybe_iso(live_gate_evidence_bundle.settlement_time),
        "funding_settlement_verified": live_gate_evidence_bundle.funding_settlement_verified,
        "ledger_explicitly_reconciled": (
            live_gate_evidence_bundle.ledger_explicitly_reconciled
        ),
        "capture_plan_evidence_count": _tuple_count(capture_plan_evidence),
        "execution_capability_evidence_count": _tuple_count(execution_capability_evidence),
    }
    if not isinstance(capture_plan_evidence, tuple) or not isinstance(
        execution_capability_evidence,
        tuple,
    ):
        return _blocked_section("live_gate_bundle_evidence_malformed", **payload)
    if (
        type(route) is not RouteCandidate
        or not _timezone_aware(settlement_time)
        or live_gate_evidence_bundle.capture_id != route.capture_id
        or live_gate_evidence_bundle.route_id != route.route_id
        or live_gate_evidence_bundle.settlement_time != settlement_time
    ):
        return _blocked_section("cross_identity_live_gate_bundle", **payload)
    if live_gate_evidence_bundle.funding_settlement_verified is not True:
        return _blocked_section("bundle_funding_not_verified", **payload)
    if live_gate_evidence_bundle.ledger_explicitly_reconciled is not True:
        return _blocked_section("bundle_ledger_not_reconciled", **payload)
    if len(capture_plan_evidence) != 1:
        return _blocked_section("bundle_capture_plan_evidence_missing", **payload)
    if len(execution_capability_evidence) != 1:
        return _blocked_section("bundle_execution_evidence_missing", **payload)

    plan_evidence = capture_plan_evidence[0]
    execution_evidence = execution_capability_evidence[0]
    plan_reason = _capture_plan_evidence_blocker(
        plan_evidence,
        route=route,
        settlement_time=settlement_time,
        viewed_at=viewed_at,
    )
    if plan_reason is not None:
        return _blocked_section(plan_reason, **payload)
    execution_reason = _execution_evidence_blocker(
        execution_evidence,
        route=route,
        settlement_time=settlement_time,
        viewed_at=viewed_at,
    )
    if execution_reason is not None:
        return _blocked_section(execution_reason, **payload)
    return _available_section(**payload)


def _non_sending_plan_section(
    *,
    non_sending_plan: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
    ledger_reconciliation: object,
    live_gate_evidence_bundle: object,
) -> dict[str, object]:
    if not _is_contract(non_sending_plan, "core.execution.planning", "NonSendingExecutionPlan"):
        return _missing_section("non_sending_plan_missing_or_malformed")
    payload = {
        "capture_id": getattr(non_sending_plan, "capture_id", None),
        "route_id": getattr(non_sending_plan, "route_id", None),
        "settlement_time": _maybe_iso(getattr(non_sending_plan, "settlement_time", None)),
        "planned_at": _maybe_iso(getattr(non_sending_plan, "planned_at", None)),
        "valid_until": _maybe_iso(getattr(non_sending_plan, "valid_until", None)),
        "capture_plan_id": getattr(non_sending_plan, "capture_plan_id", None),
        "capture_plan_version": getattr(non_sending_plan, "capture_plan_version", None),
        "route_decision_event_sequence": getattr(
            non_sending_plan,
            "route_decision_event_sequence",
            None,
        ),
        "funding_verification_event_sequence": getattr(
            non_sending_plan,
            "funding_verification_event_sequence",
            None,
        ),
        "ledger_reconciliation_event_sequence": getattr(
            non_sending_plan,
            "ledger_reconciliation_event_sequence",
            None,
        ),
        "execution_capability_checked_at": _maybe_iso(
            getattr(non_sending_plan, "execution_capability_checked_at", None)
        ),
    }
    if type(route) is not RouteCandidate or not _timezone_aware(settlement_time):
        return _blocked_section("route_identity_missing_for_plan_display", **payload)
    if not _timezone_aware(viewed_at):
        return _blocked_section("viewed_at_missing_for_plan_display", **payload)
    if not _timezone_aware(getattr(non_sending_plan, "planned_at", None)) or not _timezone_aware(
        getattr(non_sending_plan, "valid_until", None)
    ):
        return _blocked_section("non_sending_plan_time_missing_or_malformed", **payload)
    if _plan_identity_blocker(non_sending_plan, route=route, settlement_time=settlement_time):
        return _blocked_section("cross_identity_non_sending_plan", **payload)
    if getattr(non_sending_plan, "planned_at") > viewed_at or viewed_at >= getattr(
        non_sending_plan,
        "valid_until",
    ):
        return _blocked_section("non_sending_plan_stale", **payload)
    if not (
        _positive_sequence(getattr(non_sending_plan, "route_decision_event_sequence"))
        and _positive_sequence(getattr(non_sending_plan, "funding_verification_event_sequence"))
        and _positive_sequence(getattr(non_sending_plan, "ledger_reconciliation_event_sequence"))
    ):
        return _blocked_section("non_sending_plan_prerequisite_sequences_missing", **payload)
    if type(ledger_reconciliation) is LedgerReconciliationResult and (
        non_sending_plan.route_decision_event_sequence
        != ledger_reconciliation.route_decision_event_sequence
        or non_sending_plan.funding_verification_event_sequence
        != ledger_reconciliation.funding_verification_event_sequence
    ):
        return _blocked_section("non_sending_plan_ledger_prerequisites_stale", **payload)
    if type(live_gate_evidence_bundle) is LiveGateEvidenceBundle:
        prerequisite_reason = _plan_bundle_prerequisite_blocker(
            non_sending_plan,
            live_gate_evidence_bundle=live_gate_evidence_bundle,
        )
        if prerequisite_reason is not None:
            return _blocked_section(prerequisite_reason, **payload)
    return _available_section(**payload)


def _guarded_readiness_section(
    *,
    guarded_readiness: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
    non_sending_plan: object,
) -> dict[str, object]:
    if not _is_contract(guarded_readiness, "apps.live_runner.guarded", "GuardedLiveRunnerResult"):
        return _missing_section("guarded_readiness_missing_or_malformed")
    payload = {
        "no_order_ready": getattr(guarded_readiness, "no_order_ready", None),
        "blocked_reason": _enum_value(getattr(guarded_readiness, "blocked_reason", None)),
        "capture_id": getattr(guarded_readiness, "capture_id", None),
        "route_id": getattr(guarded_readiness, "route_id", None),
        "settlement_time": _maybe_iso(getattr(guarded_readiness, "settlement_time", None)),
        "evaluated_at": _maybe_iso(getattr(guarded_readiness, "evaluated_at", None)),
    }
    if getattr(guarded_readiness, "no_order_ready") is not True:
        return _blocked_section("guarded_readiness_blocked", **payload)
    if type(route) is not RouteCandidate or not _timezone_aware(settlement_time):
        return _blocked_section("route_identity_missing_for_guarded_display", **payload)
    if (
        guarded_readiness.capture_id != route.capture_id
        or guarded_readiness.route_id != route.route_id
        or guarded_readiness.settlement_time != settlement_time
        or not _timezone_aware(guarded_readiness.evaluated_at)
    ):
        return _blocked_section("cross_identity_guarded_readiness", **payload)
    if not _timezone_aware(viewed_at) or guarded_readiness.evaluated_at > viewed_at:
        return _blocked_section("guarded_readiness_time_missing_or_future", **payload)
    if _is_contract(non_sending_plan, "core.execution.planning", "NonSendingExecutionPlan"):
        if not _timezone_aware(getattr(non_sending_plan, "planned_at", None)) or not _timezone_aware(
            getattr(non_sending_plan, "valid_until", None)
        ):
            return _blocked_section("guarded_plan_time_missing_or_malformed", **payload)
        if (
            guarded_readiness.evaluated_at < non_sending_plan.planned_at
            or guarded_readiness.evaluated_at >= non_sending_plan.valid_until
        ):
            return _blocked_section("guarded_readiness_stale_for_plan", **payload)
    return _available_section(**payload)


def _approval_section(
    *,
    approval: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
    guarded_readiness: object,
    non_sending_plan: object,
) -> dict[str, object]:
    if not _is_contract(approval, "core.execution.orders", "OrderPlacementApproval"):
        return _missing_section("approval_missing_or_malformed")
    payload = {
        "approval_id": getattr(approval, "approval_id", None),
        "capture_id": getattr(approval, "capture_id", None),
        "route_id": getattr(approval, "route_id", None),
        "settlement_time": _maybe_iso(getattr(approval, "settlement_time", None)),
        "approval_granted": getattr(approval, "approval_granted", None),
        "approved_at": _maybe_iso(getattr(approval, "approved_at", None)),
        "valid_until": _maybe_iso(getattr(approval, "valid_until", None)),
    }
    if getattr(approval, "approval_granted") is not True:
        return _blocked_section("approval_not_granted", **payload)
    if type(route) is not RouteCandidate or not _timezone_aware(settlement_time):
        return _blocked_section("route_identity_missing_for_approval_display", **payload)
    if (
        approval.capture_id != route.capture_id
        or approval.route_id != route.route_id
        or approval.settlement_time != settlement_time
    ):
        return _blocked_section("cross_identity_approval", **payload)
    if not _timezone_aware(approval.approved_at) or not _timezone_aware(approval.valid_until):
        return _blocked_section("approval_time_missing_or_malformed", **payload)
    if not _timezone_aware(viewed_at) or approval.approved_at > viewed_at or viewed_at >= approval.valid_until:
        return _blocked_section("approval_stale_or_future", **payload)
    if _is_contract(guarded_readiness, "apps.live_runner.guarded", "GuardedLiveRunnerResult"):
        if (
            approval.guarded_evaluated_at != guarded_readiness.evaluated_at
            or approval.approved_at < guarded_readiness.evaluated_at
        ):
            return _blocked_section("approval_guarded_reference_mismatch", **payload)
    if _is_contract(non_sending_plan, "core.execution.planning", "NonSendingExecutionPlan"):
        prerequisite_reason = _approval_plan_prerequisite_blocker(
            approval,
            non_sending_plan=non_sending_plan,
        )
        if prerequisite_reason is not None:
            return _blocked_section(prerequisite_reason, **payload)
    return _available_section(**payload)


def _approval_boundary_section(
    *,
    approval_boundary_result: object,
    route: object,
    settlement_time: object,
    viewed_at: object,
    approval: object,
) -> dict[str, object]:
    if not _is_contract(
        approval_boundary_result,
        "core.execution.orders",
        "ApprovalGatedOrderPlacementResult",
    ):
        return _missing_section("approval_boundary_result_missing_or_malformed")
    payload = {
        "boundary_invoked": getattr(approval_boundary_result, "boundary_invoked", None),
        "blocked_reason": _enum_value(getattr(approval_boundary_result, "blocked_reason", None)),
        "capture_id": getattr(approval_boundary_result, "capture_id", None),
        "route_id": getattr(approval_boundary_result, "route_id", None),
        "settlement_time": _maybe_iso(getattr(approval_boundary_result, "settlement_time", None)),
        "requested_at": _maybe_iso(getattr(approval_boundary_result, "requested_at", None)),
        "approval_id": getattr(approval_boundary_result, "approval_id", None),
    }
    if getattr(approval_boundary_result, "boundary_invoked") is not True:
        return _blocked_section("approval_boundary_blocked", **payload)
    if type(route) is not RouteCandidate or not _timezone_aware(settlement_time):
        return _blocked_section("route_identity_missing_for_boundary_display", **payload)
    if (
        approval_boundary_result.capture_id != route.capture_id
        or approval_boundary_result.route_id != route.route_id
        or approval_boundary_result.settlement_time != settlement_time
        or not _timezone_aware(approval_boundary_result.requested_at)
    ):
        return _blocked_section("cross_identity_approval_boundary", **payload)
    if not _timezone_aware(viewed_at) or approval_boundary_result.requested_at > viewed_at:
        return _blocked_section("approval_boundary_request_future_or_malformed", **payload)
    if _is_contract(approval, "core.execution.orders", "OrderPlacementApproval"):
        if approval_boundary_result.approval_id != approval.approval_id:
            return _blocked_section("approval_boundary_approval_mismatch", **payload)
    return _available_section(**payload)


def _decision_economics(decision: DecisionResult) -> dict[str, object]:
    entry_ev = decision.entry_ev
    return {
        "net_profit_usd": _decimal_display(decision.net_profit_usd),
        "entry_ev": {
            "expected_funding_usd": _decimal_display(
                getattr(entry_ev, "expected_funding_usd", None)
            ),
            "total_fees_usd": _decimal_display(getattr(entry_ev, "total_fees_usd", None)),
            "simulated_roundtrip_cost_usd": _decimal_display(
                getattr(entry_ev, "simulated_roundtrip_cost_usd", None)
            ),
            "net_profit_usd": _decimal_display(getattr(entry_ev, "net_profit_usd", None)),
        },
    }


def _capture_plan_evidence_blocker(
    evidence: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    viewed_at: object,
) -> str | None:
    if type(evidence) is not CapturePlanFreshnessEvidence:
        return "bundle_capture_plan_evidence_malformed"
    if (
        getattr(evidence, "capture_id", None) != route.capture_id
        or getattr(evidence, "route_id", None) != route.route_id
        or getattr(evidence, "settlement_time", None) != settlement_time
    ):
        return "bundle_capture_plan_evidence_cross_identity"
    if not _timezone_aware(viewed_at):
        return "viewed_at_missing_for_bundle_display"
    if not _timezone_aware(evidence.planned_at) or not _timezone_aware(evidence.valid_until):
        return "bundle_capture_plan_evidence_time_malformed"
    if getattr(evidence, "planned_at", viewed_at) > viewed_at or viewed_at >= getattr(
        evidence,
        "valid_until",
        viewed_at,
    ):
        return "bundle_capture_plan_evidence_stale"
    return None


def _execution_evidence_blocker(
    evidence: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    viewed_at: object,
) -> str | None:
    if type(evidence) is not ExecutionCapabilityEvidence:
        return "bundle_execution_evidence_malformed"
    if (
        evidence.capture_id != route.capture_id
        or evidence.route_id != route.route_id
        or evidence.settlement_time != settlement_time
    ):
        return "bundle_execution_evidence_cross_identity"
    if not _timezone_aware(viewed_at):
        return "viewed_at_missing_for_bundle_display"
    if not _timezone_aware(evidence.checked_at) or not _timezone_aware(evidence.valid_until):
        return "bundle_execution_evidence_time_malformed"
    if evidence.checked_at > viewed_at or viewed_at >= evidence.valid_until:
        return "bundle_execution_evidence_stale"
    return None


def _plan_identity_blocker(
    plan: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
) -> bool:
    return (
        getattr(plan, "capture_id", None) != route.capture_id
        or getattr(plan, "route_id", None) != route.route_id
        or getattr(plan, "settlement_time", None) != settlement_time
        or getattr(plan, "risex_venue", None) != route.risex_venue
        or getattr(plan, "risex_symbol", None) != route.risex_symbol
        or getattr(plan, "risex_entry_side", None) != route.risex_entry_side
        or getattr(plan, "hedge_venue", None) != route.hedge_venue
        or getattr(plan, "hedge_symbol", None) != route.hedge_symbol
        or getattr(plan, "hedge_entry_side", None) != route.hedge_entry_side
        or getattr(plan, "target_notional_usd", None) != route.target_notional_usd
    )


def _plan_bundle_prerequisite_blocker(
    plan: object,
    *,
    live_gate_evidence_bundle: LiveGateEvidenceBundle,
) -> str | None:
    if len(live_gate_evidence_bundle.capture_plan_evidence) != 1:
        return "non_sending_plan_bundle_plan_reference_missing"
    if len(live_gate_evidence_bundle.execution_capability_evidence) != 1:
        return "non_sending_plan_bundle_execution_reference_missing"
    plan_evidence = live_gate_evidence_bundle.capture_plan_evidence[0]
    execution_evidence = live_gate_evidence_bundle.execution_capability_evidence[0]
    if (
        type(plan_evidence) is not CapturePlanFreshnessEvidence
        or type(execution_evidence) is not ExecutionCapabilityEvidence
    ):
        return "non_sending_plan_bundle_reference_malformed"
    if (
        getattr(plan, "capture_plan_id", None) != plan_evidence.plan_id
        or getattr(plan, "capture_plan_version", None) != plan_evidence.plan_version
        or getattr(plan, "planned_at", None) != plan_evidence.planned_at
        or getattr(plan, "ledger_reconciliation_event_sequence", None)
        != plan_evidence.ledger_reconciliation_event_sequence
    ):
        return "non_sending_plan_capture_plan_reference_mismatch"
    if getattr(plan, "execution_capability_checked_at", None) != execution_evidence.checked_at:
        return "non_sending_plan_execution_reference_mismatch"
    if not _timezone_aware(plan_evidence.valid_until) or not _timezone_aware(
        execution_evidence.valid_until
    ):
        return "non_sending_plan_bundle_validity_malformed"
    expected_valid_until = min(plan_evidence.valid_until, execution_evidence.valid_until)
    if getattr(plan, "valid_until", None) != expected_valid_until:
        return "non_sending_plan_validity_mismatch"
    return None


def _approval_plan_prerequisite_blocker(
    approval: object,
    *,
    non_sending_plan: object,
) -> str | None:
    checks = (
        ("non_sending_plan_planned_at", "planned_at"),
        ("non_sending_plan_valid_until", "valid_until"),
        ("capture_plan_id", "capture_plan_id"),
        ("capture_plan_version", "capture_plan_version"),
        ("route_decision_event_sequence", "route_decision_event_sequence"),
        ("funding_verification_event_sequence", "funding_verification_event_sequence"),
        ("ledger_reconciliation_event_sequence", "ledger_reconciliation_event_sequence"),
        ("execution_capability_checked_at", "execution_capability_checked_at"),
    )
    for approval_field, plan_field in checks:
        if getattr(approval, approval_field, None) != getattr(non_sending_plan, plan_field, None):
            return "approval_plan_reference_mismatch"
    return None


def _available_section(**payload: object) -> dict[str, object]:
    return {"display_state": _AVAILABLE, **payload}


def _blocked_section(reason: str, **payload: object) -> dict[str, object]:
    return {"display_state": _BLOCKED, "display_reason": reason, **payload}


def _missing_section(reason: str, **payload: object) -> dict[str, object]:
    return {"display_state": _MISSING, "display_reason": reason, **payload}


def _timezone_aware(value: object) -> bool:
    if not isinstance(value, datetime):
        return False
    try:
        validate_timezone_aware_datetime(value, "datetime")
    except ValueError:
        return False
    return True


def _positive_sequence(value: object) -> bool:
    return type(value) is int and value > 0


def _positive_sequence_values(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) > 0
        and all(_positive_sequence(item) for item in value)
    )


def _tuple_count(value: object) -> int | None:
    return len(value) if isinstance(value, tuple) else None


def _is_contract(value: object, module: str, qualname: str) -> bool:
    value_type = type(value)
    return value_type.__module__ == module and value_type.__qualname__ == qualname


def _decimal_display(value: object) -> dict[str, object]:
    if isinstance(value, Decimal):
        return {"display_state": _AVAILABLE, "value": _decimal_text(value)}
    return {"display_state": _MISSING, "value": None}


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _decimal_maybe_text(value: object) -> str | None:
    return _decimal_text(value) if isinstance(value, Decimal) else None


def _iso(value: datetime) -> str:
    return value.isoformat()


def _maybe_iso(value: object) -> str | None:
    return _iso(value) if _timezone_aware(value) else None


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _enum_values(value: object) -> tuple[str | None, ...]:
    if not isinstance(value, tuple):
        return ()
    return tuple(_enum_value(item) for item in value)
