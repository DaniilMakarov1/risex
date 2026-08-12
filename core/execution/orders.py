"""Approval-gated order boundary owned by execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    Capture,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import RejectReason
from core.execution.planning import NonSendingExecutionPlan


class OrderPlacementDisabled(RuntimeError):
    """Raised when code attempts to bypass the guarded boundary."""


@dataclass(frozen=True, slots=True)
class OrderPlacementApproval:
    """Caller-supplied approval for one exact guarded non-sending plan."""

    approval_id: str
    capture_id: str
    route_id: str
    settlement_time: datetime
    guarded_evaluated_at: datetime
    non_sending_plan_planned_at: datetime
    non_sending_plan_valid_until: datetime
    capture_plan_id: str
    capture_plan_version: str
    route_decision_event_sequence: int
    funding_verification_event_sequence: int
    ledger_reconciliation_event_sequence: int
    execution_capability_checked_at: datetime
    approval_granted: bool
    approved_at: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "approval_id",
            "capture_id",
            "route_id",
            "capture_plan_id",
            "capture_plan_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        for field_name in (
            "settlement_time",
            "guarded_evaluated_at",
            "non_sending_plan_planned_at",
            "non_sending_plan_valid_until",
            "execution_capability_checked_at",
            "approved_at",
            "valid_until",
        ):
            if not _timezone_aware(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.non_sending_plan_valid_until <= self.non_sending_plan_planned_at:
            raise ValueError("non_sending_plan_valid_until must be after planned_at")
        if self.valid_until <= self.approved_at:
            raise ValueError("valid_until must be after approved_at")
        if type(self.approval_granted) is not bool:
            raise ValueError("approval_granted must be a bool")
        for field_name in (
            "route_decision_event_sequence",
            "funding_verification_event_sequence",
            "ledger_reconciliation_event_sequence",
        ):
            if not _positive_sequence(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class ApprovalGatedOrderPlacementResult:
    """Deterministic result of the explicit approval boundary."""

    boundary_invoked: bool
    blocked_reason: RejectReason | None
    capture_id: str | None
    route_id: str | None
    settlement_time: datetime | None
    requested_at: datetime | None
    approval_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.boundary_invoked) is not bool:
            raise ValueError("boundary_invoked must be a bool")
        if self.boundary_invoked and self.blocked_reason is not None:
            raise ValueError("invoked results cannot carry a blocked reason")
        if self.boundary_invoked and (
            self.capture_id is None
            or self.route_id is None
            or self.settlement_time is None
            or self.requested_at is None
            or self.approval_id is None
        ):
            raise ValueError("invoked results require exact identity")
        if not self.boundary_invoked and not isinstance(self.blocked_reason, RejectReason):
            raise ValueError("blocked results require a RejectReason")
        for field_name in ("capture_id", "route_id", "approval_id"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be non-empty when provided")
        for field_name in ("settlement_time", "requested_at"):
            value = getattr(self, field_name)
            if value is not None:
                if not _timezone_aware(value):
                    raise ValueError(f"{field_name} must be timezone-aware")


def send_order(*args: object, **kwargs: object) -> None:
    """Refuse direct placement; callers must use the approval-gated boundary."""

    raise OrderPlacementDisabled("Direct order placement is disabled.")


def run_approval_gated_order_boundary(
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    guarded_result_evaluated_at: datetime,
    non_sending_plan: NonSendingExecutionPlan | None,
    approval: OrderPlacementApproval | None,
    requested_at: datetime,
    deterministic_order_boundary: (
        Callable[[OrderPlacementApproval, NonSendingExecutionPlan], bool] | None
    ),
    rules: ProductRules | None = None,
) -> ApprovalGatedOrderPlacementResult:
    """Invoke the injected boundary only after exact explicit approval passes."""

    if not isinstance(rules, ProductRules) or rules.live_trading_enabled is not True:
        return _blocked(
            RejectReason.LIVE_TRADING_DISABLED,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    if (
        type(capture) is not Capture
        or type(route) is not RouteCandidate
        or not _timezone_aware(settlement_time)
        or not _timezone_aware(guarded_result_evaluated_at)
        or not _timezone_aware(requested_at)
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )
    if (
        capture.capture_id != route.capture_id
        or capture.route_id != route.route_id
        or capture.settlement_time != settlement_time
        or guarded_result_evaluated_at > requested_at
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    plan_reason = _plan_blocked_reason(
        non_sending_plan,
        route=route,
        settlement_time=settlement_time,
        guarded_result_evaluated_at=guarded_result_evaluated_at,
        requested_at=requested_at,
    )
    if plan_reason is not None:
        return _blocked(
            plan_reason,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )
    assert non_sending_plan is not None

    approval_reason = _approval_blocked_reason(
        approval,
        route=route,
        settlement_time=settlement_time,
        guarded_result_evaluated_at=guarded_result_evaluated_at,
        non_sending_plan=non_sending_plan,
        requested_at=requested_at,
    )
    if approval_reason is not None:
        return _blocked(
            approval_reason,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )
    assert approval is not None

    if not callable(deterministic_order_boundary):
        return _blocked(
            RejectReason.TECHNICALLY_NOT_EXECUTABLE,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    try:
        boundary_accepted = deterministic_order_boundary(approval, non_sending_plan)
    except Exception:
        return _blocked(
            RejectReason.TECHNICALLY_NOT_EXECUTABLE,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    if boundary_accepted is not True:
        return _blocked(
            RejectReason.TECHNICALLY_NOT_EXECUTABLE,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    return ApprovalGatedOrderPlacementResult(
        boundary_invoked=True,
        blocked_reason=None,
        capture_id=capture.capture_id,
        route_id=route.route_id,
        settlement_time=settlement_time,
        requested_at=requested_at,
        approval_id=approval.approval_id,
    )


def _blocked(
    reason: RejectReason,
    *,
    capture: object,
    route: object,
    settlement_time: object,
    requested_at: object,
    approval: object,
) -> ApprovalGatedOrderPlacementResult:
    capture_id = capture.capture_id if type(capture) is Capture else None
    route_id = route.route_id if type(route) is RouteCandidate else None
    settlement = settlement_time if _timezone_aware(settlement_time) else None
    requested = requested_at if _timezone_aware(requested_at) else None
    approval_id = approval.approval_id if type(approval) is OrderPlacementApproval else None
    return ApprovalGatedOrderPlacementResult(
        boundary_invoked=False,
        blocked_reason=reason,
        capture_id=capture_id,
        route_id=route_id,
        settlement_time=settlement,
        requested_at=requested,
        approval_id=approval_id,
    )


def _plan_blocked_reason(
    plan: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    guarded_result_evaluated_at: datetime,
    requested_at: datetime,
) -> RejectReason | None:
    if type(plan) is not NonSendingExecutionPlan:
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    try:
        if (
            not _timezone_aware(plan.settlement_time)
            or not _timezone_aware(plan.planned_at)
            or not _timezone_aware(plan.valid_until)
            or not _timezone_aware(plan.execution_capability_checked_at)
        ):
            return RejectReason.REQUIRED_LIVE_DATA_MISSING
        if (
            plan.capture_id != route.capture_id
            or plan.route_id != route.route_id
            or plan.settlement_time != settlement_time
        ):
            return RejectReason.REQUIRED_LIVE_DATA_MISSING
        if plan.planned_at > requested_at or requested_at >= plan.valid_until:
            return RejectReason.CAPTURE_PLAN_NOT_FRESH
        if (
            guarded_result_evaluated_at < plan.planned_at
            or guarded_result_evaluated_at >= plan.valid_until
        ):
            return RejectReason.CAPTURE_PLAN_NOT_FRESH
        if (
            plan.risex_venue != route.risex_venue
            or plan.risex_symbol != route.risex_symbol
            or plan.risex_entry_side != route.risex_entry_side
            or plan.risex_unwind_side != _opposite_side(route.risex_entry_side)
            or plan.hedge_venue != route.hedge_venue
            or plan.hedge_symbol != route.hedge_symbol
            or plan.hedge_entry_side != route.hedge_entry_side
            or plan.hedge_unwind_side != _opposite_side(route.hedge_entry_side)
            or plan.target_notional_usd != route.target_notional_usd
        ):
            return RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if (
            not _positive_sequence(plan.route_decision_event_sequence)
            or not _positive_sequence(plan.funding_verification_event_sequence)
            or not _positive_sequence(plan.ledger_reconciliation_event_sequence)
        ):
            return RejectReason.REQUIRED_LIVE_DATA_MISSING
    except AttributeError:
        return RejectReason.REQUIRED_LIVE_DATA_MISSING
    return None


def _approval_blocked_reason(
    approval: object,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    guarded_result_evaluated_at: datetime,
    non_sending_plan: NonSendingExecutionPlan,
    requested_at: datetime,
) -> RejectReason | None:
    if type(approval) is not OrderPlacementApproval:
        return RejectReason.USER_RULE_VIOLATED
    if approval.approval_granted is not True:
        return RejectReason.USER_RULE_VIOLATED
    if (
        approval.capture_id != route.capture_id
        or approval.route_id != route.route_id
        or approval.settlement_time != settlement_time
        or approval.guarded_evaluated_at != guarded_result_evaluated_at
    ):
        return RejectReason.USER_RULE_VIOLATED
    if approval.approved_at < guarded_result_evaluated_at:
        return RejectReason.USER_RULE_VIOLATED
    if approval.approved_at > requested_at or requested_at >= approval.valid_until:
        return RejectReason.USER_RULE_VIOLATED
    if (
        approval.non_sending_plan_planned_at != non_sending_plan.planned_at
        or approval.non_sending_plan_valid_until != non_sending_plan.valid_until
        or approval.capture_plan_id != non_sending_plan.capture_plan_id
        or approval.capture_plan_version != non_sending_plan.capture_plan_version
        or approval.route_decision_event_sequence
        != non_sending_plan.route_decision_event_sequence
        or approval.funding_verification_event_sequence
        != non_sending_plan.funding_verification_event_sequence
        or approval.ledger_reconciliation_event_sequence
        != non_sending_plan.ledger_reconciliation_event_sequence
        or approval.execution_capability_checked_at
        != non_sending_plan.execution_capability_checked_at
    ):
        return RejectReason.USER_RULE_VIOLATED
    return None


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


def _opposite_side(side: str) -> str | None:
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    return None
