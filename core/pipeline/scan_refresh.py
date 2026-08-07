"""Two-stage fake scan orchestration over the shared offline evaluation path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    DecisionResult,
    RouteCandidate,
    VenueObservation,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode
from core.pipeline.offline_scan import evaluate_offline_candidates
from core.pipeline.snapshot import ObservationKey


@dataclass(frozen=True, slots=True)
class BroadScanResult:
    """Deterministic broad scan output plus route candidates for refresh."""

    scanned_at: datetime
    decisions: tuple[DecisionResult, ...]
    refresh_candidates: tuple[RouteCandidate, ...]

    def __post_init__(self) -> None:
        validate_timezone_aware_datetime(self.scanned_at, "scanned_at")
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "refresh_candidates", tuple(self.refresh_candidates))
        if tuple(decision.route_id for decision in self.decisions) != tuple(
            route.route_id for route in self.refresh_candidates
        ):
            raise ValueError("broad scan decisions must align with refresh candidates")


@dataclass(frozen=True, slots=True)
class FocusedRefreshResult:
    """Deterministic focused refresh output sourced from one broad scan."""

    source_scanned_at: datetime
    refreshed_at: datetime
    decisions: tuple[DecisionResult, ...]

    def __post_init__(self) -> None:
        validate_timezone_aware_datetime(self.source_scanned_at, "source_scanned_at")
        validate_timezone_aware_datetime(self.refreshed_at, "refreshed_at")
        object.__setattr__(self, "decisions", tuple(self.decisions))


def run_broad_scan(
    *,
    routes: Sequence[RouteCandidate],
    observations: Mapping[ObservationKey, VenueObservation],
    scanned_at: datetime,
    rules: ProductRules | None = None,
) -> BroadScanResult:
    """Evaluate discovered fake candidates in discovery mode."""

    decisions = evaluate_offline_candidates(
        routes=routes,
        observations=observations,
        assembled_at=scanned_at,
        mode=EvaluationMode.DISCOVERY,
        rules=rules,
    )
    return BroadScanResult(
        scanned_at=scanned_at,
        decisions=decisions,
        refresh_candidates=tuple(routes),
    )


def run_focused_refresh(
    *,
    broad_scan: BroadScanResult,
    observations: Mapping[ObservationKey, VenueObservation],
    refreshed_at: datetime,
    rules: ProductRules | None = None,
) -> FocusedRefreshResult:
    """Refresh only candidates handed off by broad scan in entry mode."""

    decisions = evaluate_offline_candidates(
        routes=broad_scan.refresh_candidates,
        observations=observations,
        assembled_at=refreshed_at,
        mode=EvaluationMode.ENTRY,
        rules=rules,
    )
    return FocusedRefreshResult(
        source_scanned_at=broad_scan.scanned_at,
        refreshed_at=refreshed_at,
        decisions=decisions,
    )
