"""Deterministic offline orchestration over normalized venue observations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    DecisionResult,
    RouteCandidate,
    VenueObservation,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus
from core.pipeline.evaluate import evaluate_route
from core.pipeline.snapshot import ObservationKey, SnapshotAssemblyInputError, assemble_route_snapshot


def _snapshot_assembly_failure_result(
    *,
    route: RouteCandidate,
    mode: EvaluationMode,
    decided_at: datetime,
) -> DecisionResult:
    return DecisionResult(
        route_id=route.route_id,
        mode=mode,
        status=RouteStatus.REJECTED,
        reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
        capture_plan=None,
        decided_at=decided_at,
    )


def evaluate_offline_candidates(
    *,
    routes: Sequence[RouteCandidate],
    observations: Mapping[ObservationKey, VenueObservation],
    assembled_at: datetime,
    mode: EvaluationMode,
    rules: ProductRules | None = None,
) -> tuple[DecisionResult, ...]:
    """Evaluate route candidates through snapshot assembly and the shared decision path."""

    validate_timezone_aware_datetime(assembled_at, "assembled_at")

    decisions: list[DecisionResult] = []
    for route in routes:
        try:
            snapshot = assemble_route_snapshot(
                route=route,
                observations=observations,
                assembled_at=assembled_at,
            )
        except SnapshotAssemblyInputError:
            decisions.append(
                _snapshot_assembly_failure_result(
                    route=route,
                    mode=mode,
                    decided_at=assembled_at,
                )
            )
            continue

        decisions.append(evaluate_route(route, snapshot, mode, rules=rules))

    return tuple(decisions)
