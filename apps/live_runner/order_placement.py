"""Approval-gated live order workflow wrapper."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from apps.live_runner.guarded import GuardedLiveRunnerResult
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    Capture,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import RejectReason
from core.execution.orders import (
    ApprovalGatedOrderPlacementResult,
    OrderPlacementApproval,
    run_approval_gated_order_boundary,
)
from core.execution.planning import NonSendingExecutionPlan


def run_approval_gated_live_order_placement(
    *,
    capture: Capture,
    route: RouteCandidate,
    settlement_time: datetime,
    guarded_live_runner_result: GuardedLiveRunnerResult | None,
    non_sending_plan: NonSendingExecutionPlan | None,
    approval: OrderPlacementApproval | None,
    requested_at: datetime,
    deterministic_order_boundary: (
        Callable[[OrderPlacementApproval, NonSendingExecutionPlan], bool] | None
    ),
    rules: ProductRules | None = None,
) -> ApprovalGatedOrderPlacementResult:
    """Require an exact no-order ready guarded result before order-boundary approval."""

    if type(guarded_live_runner_result) is not GuardedLiveRunnerResult:
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    if guarded_live_runner_result.no_order_ready is not True:
        return _blocked(
            guarded_live_runner_result.blocked_reason
            or RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    if (
        guarded_live_runner_result.capture_id != getattr(capture, "capture_id", None)
        or guarded_live_runner_result.route_id != getattr(route, "route_id", None)
        or guarded_live_runner_result.settlement_time != settlement_time
        or not _timezone_aware(guarded_live_runner_result.evaluated_at)
        or not _timezone_aware(requested_at)
        or guarded_live_runner_result.evaluated_at > requested_at
    ):
        return _blocked(
            RejectReason.REQUIRED_LIVE_DATA_MISSING,
            capture=capture,
            route=route,
            settlement_time=settlement_time,
            requested_at=requested_at,
            approval=approval,
        )

    return run_approval_gated_order_boundary(
        capture=capture,
        route=route,
        settlement_time=settlement_time,
        guarded_result_evaluated_at=guarded_live_runner_result.evaluated_at,
        non_sending_plan=non_sending_plan,
        approval=approval,
        requested_at=requested_at,
        deterministic_order_boundary=deterministic_order_boundary,
        rules=rules,
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


def _timezone_aware(value: object) -> bool:
    if not isinstance(value, datetime):
        return False
    try:
        validate_timezone_aware_datetime(value, "datetime")
    except ValueError:
        return False
    return True
