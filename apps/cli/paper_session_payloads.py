"""Local paper session route payload parsing helpers."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from core.domain.contracts import RouteCandidate, validate_timezone_aware_datetime
from core.domain.enums import EvaluationMode
from core.venues.hyperliquid import HyperliquidObservationAdapter
from core.venues.risex import RiseXObservationAdapter

PAPER_SESSION_ROUTE_FIELD_NAMES = (
    "route_id",
    "capture_id",
    "risex_venue",
    "risex_symbol",
    "risex_side",
    "hedge_venue",
    "hedge_symbol",
    "hedge_side",
    "target_notional_usd",
    "mode",
    "assembled_at",
)
PAPER_SESSION_ROUTE_FIELDS = frozenset(PAPER_SESSION_ROUTE_FIELD_NAMES)
MAX_PAPER_SESSION_ROUTES = 25


def _non_empty(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise argparse.ArgumentTypeError("value must be non-empty")
    return cleaned


def _positive_finite_decimal(value: str) -> Decimal:
    try:
        notional = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(
            "target notional must be a positive finite Decimal"
        ) from exc
    if not notional.is_finite() or notional <= Decimal("0"):
        raise argparse.ArgumentTypeError(
            "target notional must be a positive finite Decimal"
        )
    return notional


def _timezone_aware_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "assembled-at must be an ISO 8601 timezone-aware timestamp"
        ) from exc
    try:
        validate_timezone_aware_datetime(parsed, "assembled_at")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return parsed


def _join_or_none(values: Sequence[str]) -> str:
    return ",".join(values) or "None"


def _route_string(
    payload: Mapping[str, object],
    field_name: str,
    route_index: int,
) -> str:
    value = payload[field_name]
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError(
            f"route {route_index} {field_name} must be a string"
        )
    try:
        return _non_empty(value)
    except argparse.ArgumentTypeError as exc:
        raise argparse.ArgumentTypeError(
            f"route {route_index} {field_name}: {exc}"
        ) from exc


def validate_paper_session_route_list(
    raw_routes: object,
    *,
    payload_name: str,
) -> tuple[tuple[RouteCandidate, datetime], ...]:
    if not isinstance(raw_routes, list):
        raise argparse.ArgumentTypeError(
            f"{payload_name} must contain a finite JSON array of explicit routes"
        )
    if not raw_routes:
        raise argparse.ArgumentTypeError(f"{payload_name} route array must be non-empty")
    if len(raw_routes) > MAX_PAPER_SESSION_ROUTES:
        raise argparse.ArgumentTypeError(
            f"{payload_name} route array must contain at most "
            f"{MAX_PAPER_SESSION_ROUTES} explicit routes"
        )

    route_inputs: list[tuple[RouteCandidate, datetime]] = []
    for route_index, raw_route in enumerate(raw_routes, start=1):
        if not isinstance(raw_route, Mapping):
            raise argparse.ArgumentTypeError(f"route {route_index} must be an object")

        field_names = set(raw_route)
        if field_names != PAPER_SESSION_ROUTE_FIELDS:
            missing = sorted(PAPER_SESSION_ROUTE_FIELDS - field_names)
            extra = sorted(field_names - PAPER_SESSION_ROUTE_FIELDS)
            raise argparse.ArgumentTypeError(
                f"route {route_index} must contain exactly explicit route fields; "
                f"missing={_join_or_none(tuple(missing))} "
                f"extra={_join_or_none(tuple(extra))}"
            )

        mode = _route_string(raw_route, "mode", route_index)
        if mode != EvaluationMode.ENTRY.value:
            raise argparse.ArgumentTypeError(
                f"route {route_index} mode must be {EvaluationMode.ENTRY.value}"
            )

        risex_venue = _route_string(raw_route, "risex_venue", route_index)
        if risex_venue != RiseXObservationAdapter.name:
            raise argparse.ArgumentTypeError(
                f"route {route_index} risex_venue must be {RiseXObservationAdapter.name}"
            )
        hedge_venue = _route_string(raw_route, "hedge_venue", route_index)
        if hedge_venue != HyperliquidObservationAdapter.name:
            raise argparse.ArgumentTypeError(
                "route "
                f"{route_index} hedge_venue must be {HyperliquidObservationAdapter.name}"
            )

        try:
            route = RouteCandidate(
                route_id=_route_string(raw_route, "route_id", route_index),
                capture_id=_route_string(raw_route, "capture_id", route_index),
                risex_venue=risex_venue,
                risex_symbol=_route_string(raw_route, "risex_symbol", route_index),
                risex_entry_side=_route_string(raw_route, "risex_side", route_index),
                hedge_venue=hedge_venue,
                hedge_symbol=_route_string(raw_route, "hedge_symbol", route_index),
                hedge_entry_side=_route_string(raw_route, "hedge_side", route_index),
                target_notional_usd=_positive_finite_decimal(
                    _route_string(raw_route, "target_notional_usd", route_index)
                ),
            )
            assembled_at = _timezone_aware_datetime(
                _route_string(raw_route, "assembled_at", route_index)
            )
        except (ValueError, argparse.ArgumentTypeError) as exc:
            raise argparse.ArgumentTypeError(f"route {route_index}: {exc}") from exc

        route_inputs.append((route, assembled_at))

    return tuple(route_inputs)


def paper_session_routes_from_json_path(
    routes_json_path: str,
) -> tuple[tuple[RouteCandidate, datetime], ...]:
    try:
        raw_routes = json.loads(Path(routes_json_path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise argparse.ArgumentTypeError(
            f"routes-json-path could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"routes-json-path must contain valid JSON: {exc.msg}"
        ) from exc

    return validate_paper_session_route_list(
        raw_routes,
        payload_name="routes-json-path",
    )


def _route_list_shape_from_inputs(
    route_inputs: Sequence[tuple[RouteCandidate, datetime]],
) -> list[dict[str, str]]:
    route_list: list[dict[str, str]] = []
    for route, assembled_at in route_inputs:
        route_list.append(
            {
                "route_id": route.route_id,
                "capture_id": route.capture_id,
                "risex_venue": route.risex_venue,
                "risex_symbol": route.risex_symbol,
                "risex_side": route.risex_entry_side,
                "hedge_venue": route.hedge_venue,
                "hedge_symbol": route.hedge_symbol,
                "hedge_side": route.hedge_entry_side,
                "target_notional_usd": str(route.target_notional_usd),
                "mode": EvaluationMode.ENTRY.value,
                "assembled_at": assembled_at.isoformat(),
            }
        )
    return route_list


def paper_session_route_list_from_command_payload(
    payload_text: str,
) -> list[dict[str, str]]:
    try:
        payload_source = _non_empty(payload_text)
    except argparse.ArgumentTypeError as exc:
        raise argparse.ArgumentTypeError(
            f"paper-session-command-payload: {exc}"
        ) from exc

    try:
        raw_payload = json.loads(payload_source)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(
            f"paper-session-command-payload must contain valid JSON: {exc.msg}"
        ) from exc

    if isinstance(raw_payload, Mapping):
        payload_fields = set(raw_payload)
        if payload_fields != {"routes"}:
            extra = sorted(payload_fields - {"routes"})
            missing = [] if "routes" in payload_fields else ["routes"]
            raise argparse.ArgumentTypeError(
                "paper-session-command-payload object must contain exactly routes; "
                f"missing={_join_or_none(tuple(missing))} "
                f"extra={_join_or_none(tuple(extra))}"
            )
        raw_routes = raw_payload["routes"]
    else:
        raw_routes = raw_payload

    route_inputs = validate_paper_session_route_list(
        raw_routes,
        payload_name="paper-session-command-payload",
    )
    return _route_list_shape_from_inputs(route_inputs)
