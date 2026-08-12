"""One-route real-data research runner."""

from __future__ import annotations

from datetime import datetime

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    DecisionResult,
    RouteCandidate,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.pipeline.evaluate import evaluate_route
from core.pipeline.snapshot import assemble_route_snapshot_from_adapters
from core.venues.base import VenueAdapter


def run_real_data_research_route(
    *,
    route: RouteCandidate,
    risex_adapter: VenueAdapter,
    hedge_adapter: VenueAdapter,
    assembled_at: datetime,
    mode: EvaluationMode,
    rules: ProductRules | None = None,
) -> DecisionResult:
    """Evaluate one explicit route from read-only adapter observations."""

    validate_timezone_aware_datetime(assembled_at, "assembled_at")

    try:
        snapshot = assemble_route_snapshot_from_adapters(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=hedge_adapter,
            assembled_at=assembled_at,
        )
    except Exception:
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.REJECTED,
            reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
            capture_plan=None,
            decided_at=assembled_at,
        )

    return evaluate_route(route, snapshot, mode, rules=rules)
