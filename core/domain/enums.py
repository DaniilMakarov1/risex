"""Shared domain enums for route evaluation."""

from __future__ import annotations

from enum import StrEnum


class RouteStatus(StrEnum):
    """Allowed route statuses.

    Keep this enum intentionally small. Do not add CANARY_ELIGIBLE.
    """

    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"
    LIVE_ELIGIBLE = "LIVE_ELIGIBLE"
    REJECTED = "REJECTED"


class EvaluationMode(StrEnum):
    """Evaluation mode used by the shared route decision pipeline."""

    DISCOVERY = "DISCOVERY"
    ENTRY = "ENTRY"
