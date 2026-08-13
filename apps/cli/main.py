"""CLI entrypoints for deterministic research workflows."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from apps.cli.paper_session_payloads import (
    MAX_PAPER_SESSION_ROUTES as _MAX_PAPER_SESSION_ROUTES,
    paper_session_display_command_payload_from_command_text as _paper_session_display_command_payload_from_command_text,
    paper_session_package_command_paths_from_run_command_text as _paper_session_package_command_paths_from_run_command_text,
    paper_session_report_path_from_display_command_payload as _paper_session_report_path_from_display_command_payload,
    paper_session_route_list_from_command_payload as _paper_session_route_list_from_command_payload,
    paper_session_routes_from_json_path as _paper_session_routes_from_json_path,
)
from apps.paper_runner.lifecycle import PaperRunResult, run_paper_lifecycle
from apps.research_runner.real_data import (
    run_real_data_research_route,
    run_real_data_research_route_with_snapshot,
)
from apps.research_runner.fake_data import (
    build_fake_focused_refresh_observations,
    build_fake_route_candidates_and_observations,
)
from core.accounting.ledger import (
    InMemoryLedger,
    Ledger,
    LedgerEvent,
    ledger_payload_to_jsonable,
)
from core.domain.contracts import (
    DecisionResult,
    EstimatedValue,
    RouteCandidate,
    VALID_ORDER_SIDES,
    VenueSnapshot,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode, RouteStatus, ValueSource
from core.pipeline.scan_refresh import run_broad_scan, run_focused_refresh
from core.venues.hyperliquid import HyperliquidObservationAdapter
from core.venues.risex import RiseXObservationAdapter
from storage.sqlite.ledger import SQLiteLedger


def _print_decisions(label: str, decisions: tuple[DecisionResult, ...]) -> None:
    print(label)
    for decision in decisions:
        print(f"{decision.route_id}: {decision.status.value} net_profit_usd={decision.net_profit_usd}")


def _run_fake_scan_refresh() -> None:
    routes, observations, assembled_at = build_fake_route_candidates_and_observations()
    broad_scan = run_broad_scan(
        routes=routes,
        observations=observations,
        scanned_at=assembled_at,
    )
    refreshed_observations, refreshed_at = build_fake_focused_refresh_observations()
    focused_refresh = run_focused_refresh(
        broad_scan=broad_scan,
        observations=refreshed_observations,
        refreshed_at=refreshed_at,
    )

    _print_decisions("Broad Scan", broad_scan.decisions)
    _print_decisions("Focused Refresh", focused_refresh.decisions)


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m apps.cli.main",
        description="Run RiseX Points Farmer research commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    real_data_route = subparsers.add_parser(
        "real-data-route",
        help="Evaluate one explicit RiseX plus Hyperliquid route from read-only public data.",
    )
    real_data_route.add_argument("--route-id", required=True, type=_non_empty)
    real_data_route.add_argument("--capture-id", required=True, type=_non_empty)
    real_data_route.add_argument(
        "--risex-venue",
        required=True,
        choices=(RiseXObservationAdapter.name,),
    )
    real_data_route.add_argument("--risex-symbol", required=True, type=_non_empty)
    real_data_route.add_argument(
        "--risex-side",
        required=True,
        choices=tuple(sorted(VALID_ORDER_SIDES)),
    )
    real_data_route.add_argument(
        "--hedge-venue",
        required=True,
        choices=(HyperliquidObservationAdapter.name,),
    )
    real_data_route.add_argument("--hedge-symbol", required=True, type=_non_empty)
    real_data_route.add_argument(
        "--hedge-side",
        required=True,
        choices=tuple(sorted(VALID_ORDER_SIDES)),
    )
    real_data_route.add_argument(
        "--target-notional-usd",
        required=True,
        type=_positive_finite_decimal,
    )
    real_data_route.add_argument(
        "--mode",
        required=True,
        choices=tuple(mode.value for mode in EvaluationMode),
    )
    real_data_route.add_argument(
        "--assembled-at",
        required=True,
        type=_timezone_aware_datetime,
    )
    real_data_route.add_argument(
        "--public-readiness-report",
        action="store_true",
        help="Print one route's public fee, funding, and readiness evidence.",
    )
    real_data_route.add_argument(
        "--public-readiness-report-format",
        choices=("text", "json"),
        default=None,
        help="Select stdout format for --public-readiness-report.",
    )
    real_data_route.set_defaults(handler=_run_real_data_route)

    paper_trade_route = subparsers.add_parser(
        "paper-trade-route",
        help=(
            "Evaluate one explicit public ENTRY route and run the fake paper "
            "lifecycle."
        ),
    )
    paper_trade_route.add_argument("--route-id", required=True, type=_non_empty)
    paper_trade_route.add_argument("--capture-id", required=True, type=_non_empty)
    paper_trade_route.add_argument(
        "--risex-venue",
        required=True,
        choices=(RiseXObservationAdapter.name,),
    )
    paper_trade_route.add_argument("--risex-symbol", required=True, type=_non_empty)
    paper_trade_route.add_argument(
        "--risex-side",
        required=True,
        choices=tuple(sorted(VALID_ORDER_SIDES)),
    )
    paper_trade_route.add_argument(
        "--hedge-venue",
        required=True,
        choices=(HyperliquidObservationAdapter.name,),
    )
    paper_trade_route.add_argument("--hedge-symbol", required=True, type=_non_empty)
    paper_trade_route.add_argument(
        "--hedge-side",
        required=True,
        choices=tuple(sorted(VALID_ORDER_SIDES)),
    )
    paper_trade_route.add_argument(
        "--target-notional-usd",
        required=True,
        type=_positive_finite_decimal,
    )
    paper_trade_route.add_argument(
        "--mode",
        required=True,
        choices=(EvaluationMode.ENTRY.value,),
    )
    paper_trade_route.add_argument(
        "--assembled-at",
        required=True,
        type=_timezone_aware_datetime,
    )
    paper_trade_route.add_argument(
        "--ledger-sqlite-path",
        default=None,
        type=_non_empty,
        help="Optional explicit local SQLite ledger path for fake paper events.",
    )
    paper_trade_route.set_defaults(handler=_run_paper_trade_route)

    paper_trade_session = subparsers.add_parser(
        "paper-trade-session",
        help=(
            "Evaluate a finite explicit route-list file serially and run fake "
            "paper lifecycle attempts."
        ),
    )
    paper_trade_session.add_argument(
        "--routes-json-path",
        required=True,
        type=_non_empty,
        help="Local JSON file containing a finite explicit route array.",
    )
    paper_trade_session.add_argument(
        "--ledger-sqlite-path",
        default=None,
        type=_non_empty,
        help="Optional explicit local SQLite ledger path for fake paper events.",
    )
    paper_trade_session.add_argument(
        "--session-report-json-path",
        default=None,
        type=_non_empty,
        help="Optional explicit local JSON path for the paper session report/history export.",
    )
    paper_trade_session.set_defaults(handler=_run_paper_trade_session)

    build_paper_session_package = subparsers.add_parser(
        "build-paper-session-package",
        help=(
            "Build local route-list and preview artifacts for a manual paper "
            "trade session."
        ),
    )
    build_paper_session_package.add_argument(
        "--paper-session-command-payload-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON command payload fixture path.",
    )
    build_paper_session_package.add_argument(
        "--routes-json-output-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON route-list artifact path to write.",
    )
    build_paper_session_package.add_argument(
        "--preview-json-output-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON preview/manifest artifact path to write.",
    )
    build_paper_session_package.add_argument(
        "--session-report-json-path",
        required=True,
        type=_non_empty,
        help="Intended explicit local JSON report path for the manual session run.",
    )
    build_paper_session_package.set_defaults(handler=_run_build_paper_session_package)

    build_paper_session_run_command_text_preview = subparsers.add_parser(
        "build-paper-session-run-command-text-preview",
        help=(
            "Build a local preview artifact for a manual paper session run "
            "command text package-builder plan."
        ),
    )
    build_paper_session_run_command_text_preview.add_argument(
        "--paper-session-run-command-text-path",
        required=True,
        type=_non_empty,
        help="Explicit local paper session run command text fixture path.",
    )
    build_paper_session_run_command_text_preview.add_argument(
        "--preview-json-output-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON run-command-text preview artifact path to write.",
    )
    build_paper_session_run_command_text_preview.set_defaults(
        handler=_run_build_paper_session_run_command_text_preview
    )

    parse_paper_session_run_command_text = subparsers.add_parser(
        "parse-paper-session-run-command-text",
        help=(
            "Parse local paper session run command text into package artifacts."
        ),
    )
    parse_paper_session_run_command_text.add_argument(
        "--paper-session-run-command-text-path",
        required=True,
        type=_non_empty,
        help="Explicit local paper session run command text fixture path.",
    )
    parse_paper_session_run_command_text.set_defaults(
        handler=_run_parse_paper_session_run_command_text
    )

    build_paper_session_display_payload = subparsers.add_parser(
        "build-paper-session-display-payload",
        help=(
            "Build a local display command payload fixture for an existing "
            "paper session report."
        ),
    )
    build_paper_session_display_payload.add_argument(
        "--session-report-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local RX-057 paper session report JSON path to validate.",
    )
    build_paper_session_display_payload.add_argument(
        "--display-payload-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON display payload fixture path to write.",
    )
    build_paper_session_display_payload.set_defaults(
        handler=_run_build_paper_session_display_payload
    )

    build_paper_session_display_command_preview = subparsers.add_parser(
        "build-paper-session-display-command-preview",
        help=(
            "Build a local preview artifact for a manual paper session report "
            "display command."
        ),
    )
    build_paper_session_display_command_preview.add_argument(
        "--paper-session-display-command-payload-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON display command payload fixture path.",
    )
    build_paper_session_display_command_preview.add_argument(
        "--preview-json-output-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON preview/manifest artifact path to write.",
    )
    build_paper_session_display_command_preview.set_defaults(
        handler=_run_build_paper_session_display_command_preview
    )

    parse_paper_session_display_command_text = subparsers.add_parser(
        "parse-paper-session-display-command-text",
        help=(
            "Parse local paper session report display command text into a "
            "display payload fixture."
        ),
    )
    parse_paper_session_display_command_text.add_argument(
        "--paper-session-display-command-text-path",
        required=True,
        type=_non_empty,
        help="Explicit local display command text fixture path.",
    )
    parse_paper_session_display_command_text.add_argument(
        "--display-payload-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON display payload fixture path to write.",
    )
    parse_paper_session_display_command_text.set_defaults(
        handler=_run_parse_paper_session_display_command_text
    )

    build_paper_session_display_command_text_preview = subparsers.add_parser(
        "build-paper-session-display-command-text-preview",
        help=(
            "Build a local preview artifact for a manual paper session report "
            "display command text parser command."
        ),
    )
    build_paper_session_display_command_text_preview.add_argument(
        "--paper-session-display-command-text-path",
        required=True,
        type=_non_empty,
        help="Explicit local display command text fixture path.",
    )
    build_paper_session_display_command_text_preview.add_argument(
        "--display-payload-json-path",
        required=True,
        type=_non_empty,
        help="Intended explicit local JSON display payload fixture path.",
    )
    build_paper_session_display_command_text_preview.add_argument(
        "--preview-json-output-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON preview/manifest artifact path to write.",
    )
    build_paper_session_display_command_text_preview.set_defaults(
        handler=_run_build_paper_session_display_command_text_preview
    )

    render_paper_session_report = subparsers.add_parser(
        "render-paper-session-report",
        help="Render an already-written local paper session report JSON to stdout.",
    )
    render_paper_session_report.add_argument(
        "--session-report-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local RX-057 paper session report JSON path to render.",
    )
    render_paper_session_report.set_defaults(
        handler=_run_render_paper_session_report
    )

    render_paper_session_report_from_payload = subparsers.add_parser(
        "render-paper-session-report-from-payload",
        help=(
            "Render an already-written local paper session report selected by "
            "a local display command payload fixture."
        ),
    )
    render_paper_session_report_from_payload.add_argument(
        "--paper-session-display-command-payload-json-path",
        required=True,
        type=_non_empty,
        help="Explicit local JSON display command payload fixture path.",
    )
    render_paper_session_report_from_payload.set_defaults(
        handler=_run_render_paper_session_report_from_payload
    )

    return parser


def _decimal_or_none(value: Decimal | None) -> str:
    return "None" if value is None else str(value)


def _decimal_json_or_none(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _entry_ev_decimal_or_none(decision: DecisionResult, field_name: str) -> str:
    if decision.entry_ev is None:
        return "None"
    return _decimal_or_none(getattr(decision.entry_ev, field_name))


def _entry_ev_json_or_none(
    decision: DecisionResult,
    field_name: str,
) -> str | None:
    if decision.entry_ev is None:
        return None
    return _decimal_json_or_none(getattr(decision.entry_ev, field_name))


def _print_real_data_decision(decision: DecisionResult) -> None:
    reasons = ",".join(reason.value for reason in decision.reasons) or "None"
    print("Real Data Route")
    print(f"route_id={decision.route_id}")
    print(f"mode={decision.mode.value}")
    print(f"status={decision.status.value}")
    print(f"reasons={reasons}")
    print(f"net_profit_usd={_decimal_or_none(decision.net_profit_usd)}")
    print(
        "expected_funding_usd="
        f"{_entry_ev_decimal_or_none(decision, 'expected_funding_usd')}"
    )
    print(f"total_fees_usd={_entry_ev_decimal_or_none(decision, 'total_fees_usd')}")
    print(
        "simulated_roundtrip_cost_usd="
        f"{_entry_ev_decimal_or_none(decision, 'simulated_roundtrip_cost_usd')}"
    )


def _metadata_or_none(metadata: Mapping[str, str]) -> str:
    if not metadata:
        return "None"
    return ";".join(f"{key}={metadata[key]}" for key in sorted(metadata))


def _metadata_json(metadata: Mapping[str, str]) -> dict[str, str]:
    return {key: metadata[key] for key in sorted(metadata)}


def _print_estimated_value(prefix: str, value: EstimatedValue) -> None:
    print(f"{prefix}.value_usd={_decimal_or_none(value.value)}")
    print(f"{prefix}.source={value.source.value}")
    print(f"{prefix}.description={value.description or 'None'}")
    print(f"{prefix}.metadata={_metadata_or_none(value.metadata)}")


def _estimated_value_json(value: EstimatedValue) -> dict[str, object]:
    return {
        "value_usd": _decimal_json_or_none(value.value),
        "source": value.source.value,
        "description": value.description,
        "metadata": _metadata_json(value.metadata),
    }


def _unknown_evidence_components(snapshot: VenueSnapshot | None) -> tuple[str, ...]:
    if snapshot is None:
        return ("snapshot",)

    unknowns: list[str] = []
    if snapshot.funding.risex_funding_usd.source is ValueSource.UNKNOWN:
        unknowns.append("funding.risex")
    if snapshot.funding.hedge_funding_usd.source is ValueSource.UNKNOWN:
        unknowns.append("funding.hedge")
    for index, component in enumerate(snapshot.fees.components, start=1):
        if component.amount_usd.source is ValueSource.UNKNOWN:
            unknowns.append(f"fee.{index}.{component.name}")
    return tuple(unknowns)


def _join_or_none(values: Sequence[str]) -> str:
    return ",".join(values) or "None"


def _public_readiness_blockers(
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
    unknowns: Sequence[str],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if snapshot is None:
        blockers.append("public snapshot evidence unavailable")
    if decision.mode is not EvaluationMode.ENTRY:
        blockers.append(f"evaluation mode is {decision.mode.value}, not ENTRY")
    if decision.status is not RouteStatus.PAPER_ELIGIBLE:
        blockers.append(f"decision status is {decision.status.value}")
    if decision.entry_ev is None:
        blockers.append("Entry EV fields are unavailable")
    if unknowns:
        blockers.append(f"UNKNOWN evidence remains: {_join_or_none(unknowns)}")
    return tuple(blockers)


def _public_readiness_ready_reason() -> str:
    return (
        "public evidence complete for one ENTRY route; live/order/private/account "
        "stages remain outside this report"
    )


def _print_public_readiness_report(
    route: RouteCandidate,
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
) -> None:
    reasons = tuple(reason.value for reason in decision.reasons)
    unknowns = _unknown_evidence_components(snapshot)
    blockers = _public_readiness_blockers(decision, snapshot, unknowns)

    print("Public Readiness Report")
    print(f"route_id={route.route_id}")
    print(f"capture_id={route.capture_id}")
    print(f"risex_venue={route.risex_venue}")
    print(f"risex_symbol={route.risex_symbol}")
    print(f"risex_side={route.risex_entry_side}")
    print(f"hedge_venue={route.hedge_venue}")
    print(f"hedge_symbol={route.hedge_symbol}")
    print(f"hedge_side={route.hedge_entry_side}")
    print(f"target_notional_usd={route.target_notional_usd}")
    print(f"mode={decision.mode.value}")
    print(f"status={decision.status.value}")
    print(f"reasons={_join_or_none(reasons)}")
    print(f"net_profit_usd={_decimal_or_none(decision.net_profit_usd)}")
    print(
        "expected_funding_usd="
        f"{_entry_ev_decimal_or_none(decision, 'expected_funding_usd')}"
    )
    print(f"total_fees_usd={_entry_ev_decimal_or_none(decision, 'total_fees_usd')}")
    print(
        "simulated_roundtrip_cost_usd="
        f"{_entry_ev_decimal_or_none(decision, 'simulated_roundtrip_cost_usd')}"
    )
    print(
        "entry_ev_net_profit_usd="
        f"{_entry_ev_decimal_or_none(decision, 'net_profit_usd')}"
    )

    if snapshot is None:
        print("snapshot=UNKNOWN")
    else:
        print("snapshot=AVAILABLE")
        print(f"snapshot.captured_at={snapshot.captured_at.isoformat()}")
        print(f"snapshot.risex_observed_at={snapshot.risex_observed_at.isoformat()}")
        print(f"snapshot.hedge_observed_at={snapshot.hedge_observed_at.isoformat()}")
        print(
            "snapshot.risex_funding_settlement_at="
            f"{snapshot.risex_funding_settlement_at.isoformat()}"
        )
        print(
            "snapshot.hedge_funding_settlement_at="
            f"{snapshot.hedge_funding_settlement_at.isoformat()}"
        )
        _print_estimated_value("funding.risex", snapshot.funding.risex_funding_usd)
        _print_estimated_value("funding.hedge", snapshot.funding.hedge_funding_usd)
        print(f"fee.count={len(snapshot.fees.components)}")
        for index, component in enumerate(snapshot.fees.components, start=1):
            prefix = f"fee.{index}"
            print(f"{prefix}.name={component.name}")
            print(f"{prefix}.is_default={component.is_default}")
            _print_estimated_value(prefix, component.amount_usd)

    print(f"unknown_components={_join_or_none(unknowns)}")
    if blockers:
        print("public_readiness=NOT_READY")
        print(f"public_readiness_reasons={'; '.join(blockers)}")
    else:
        print("public_readiness=READY_FOR_LATER_FAIL_CLOSED_STAGES")
        print(f"public_readiness_reasons={_public_readiness_ready_reason()}")
    print(f"later_fail_closed_blockers={_join_or_none(reasons)}")


def _public_readiness_report_json(
    route: RouteCandidate,
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
) -> dict[str, object]:
    reasons = tuple(reason.value for reason in decision.reasons)
    unknowns = _unknown_evidence_components(snapshot)
    blockers = _public_readiness_blockers(decision, snapshot, unknowns)
    readiness_status = (
        "NOT_READY" if blockers else "READY_FOR_LATER_FAIL_CLOSED_STAGES"
    )
    readiness_reasons = (
        list(blockers) if blockers else [_public_readiness_ready_reason()]
    )

    snapshot_json: dict[str, object]
    if snapshot is None:
        snapshot_json = {
            "state": "UNKNOWN",
            "captured_at": None,
            "risex_observed_at": None,
            "hedge_observed_at": None,
            "risex_funding_settlement_at": None,
            "hedge_funding_settlement_at": None,
            "funding": None,
            "fees": None,
        }
    else:
        snapshot_json = {
            "state": "AVAILABLE",
            "captured_at": snapshot.captured_at.isoformat(),
            "risex_observed_at": snapshot.risex_observed_at.isoformat(),
            "hedge_observed_at": snapshot.hedge_observed_at.isoformat(),
            "risex_funding_settlement_at": (
                snapshot.risex_funding_settlement_at.isoformat()
            ),
            "hedge_funding_settlement_at": (
                snapshot.hedge_funding_settlement_at.isoformat()
            ),
            "funding": {
                "risex": _estimated_value_json(snapshot.funding.risex_funding_usd),
                "hedge": _estimated_value_json(snapshot.funding.hedge_funding_usd),
            },
            "fees": {
                "count": len(snapshot.fees.components),
                "components": [
                    {
                        "name": component.name,
                        "is_default": component.is_default,
                        "amount_usd": _estimated_value_json(component.amount_usd),
                    }
                    for component in snapshot.fees.components
                ],
            },
        }

    return {
        "report": "Public Readiness Report",
        "route": {
            "route_id": route.route_id,
            "capture_id": route.capture_id,
            "risex_venue": route.risex_venue,
            "risex_symbol": route.risex_symbol,
            "risex_side": route.risex_entry_side,
            "hedge_venue": route.hedge_venue,
            "hedge_symbol": route.hedge_symbol,
            "hedge_side": route.hedge_entry_side,
            "target_notional_usd": str(route.target_notional_usd),
        },
        "decision": {
            "mode": decision.mode.value,
            "status": decision.status.value,
            "reasons": list(reasons),
            "net_profit_usd": _decimal_json_or_none(decision.net_profit_usd),
            "entry_ev": {
                "expected_funding_usd": _entry_ev_json_or_none(
                    decision,
                    "expected_funding_usd",
                ),
                "total_fees_usd": _entry_ev_json_or_none(
                    decision,
                    "total_fees_usd",
                ),
                "simulated_roundtrip_cost_usd": _entry_ev_json_or_none(
                    decision,
                    "simulated_roundtrip_cost_usd",
                ),
                "net_profit_usd": _entry_ev_json_or_none(
                    decision,
                    "net_profit_usd",
                ),
            },
        },
        "snapshot": snapshot_json,
        "unknown_components": list(unknowns),
        "public_readiness": {
            "status": readiness_status,
            "reasons": readiness_reasons,
            "display_only": True,
        },
        "later_fail_closed_blockers": list(reasons),
    }


def _print_public_readiness_report_json(
    route: RouteCandidate,
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
) -> None:
    print(
        json.dumps(
            _public_readiness_report_json(route, decision, snapshot),
            indent=2,
        )
    )


def _print_paper_trade_summary(
    *,
    route: RouteCandidate,
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
    paper_result: PaperRunResult | None,
    ledger_events: Sequence[LedgerEvent],
    ledger_path: str | None,
) -> None:
    reasons = tuple(reason.value for reason in decision.reasons)
    if paper_result is None:
        paper_started = False
        paper_start_attribution = "None"
        paper_start_blockers = ("public_snapshot_unavailable",)
        expected_funding_usd = None
        total_fees_usd = None
        simulated_roundtrip_cost_usd = None
        paper_net_profit_usd = None
    else:
        explanation = paper_result.explanation
        paper_started = paper_result.started
        paper_start_attribution = explanation.paper_start_attribution
        paper_start_blockers = explanation.paper_start_blockers
        expected_funding_usd = explanation.expected_funding_usd
        total_fees_usd = explanation.total_fees_usd
        simulated_roundtrip_cost_usd = explanation.simulated_roundtrip_cost_usd
        paper_net_profit_usd = explanation.net_profit_usd

    print("Paper Trade Route")
    print(f"route_id={route.route_id}")
    print(f"capture_id={route.capture_id}")
    print(f"mode={decision.mode.value}")
    print(f"status={decision.status.value}")
    print(f"reasons={_join_or_none(reasons)}")
    print(f"decision.net_profit_usd={_decimal_or_none(decision.net_profit_usd)}")
    if snapshot is None:
        print("snapshot=UNKNOWN")
        print("funding_settlement_at=None")
    else:
        print("snapshot=AVAILABLE")
        print(
            "funding_settlement_at="
            f"{snapshot.risex_funding_settlement_at.isoformat()}"
        )
    print(f"paper_started={paper_started}")
    print(f"paper_start_attribution={paper_start_attribution}")
    print(f"paper_start_blockers={_join_or_none(paper_start_blockers)}")
    print(f"ledger_event_count={len(ledger_events)}")
    print(
        "ledger_event_sequences="
        f"{_join_or_none(tuple(str(event.sequence) for event in ledger_events))}"
    )
    print(
        "ledger_event_types="
        f"{_join_or_none(tuple(event.event_type for event in ledger_events))}"
    )
    print(f"paper.expected_funding_usd={_decimal_or_none(expected_funding_usd)}")
    print(f"paper.total_fees_usd={_decimal_or_none(total_fees_usd)}")
    print(
        "paper.simulated_roundtrip_cost_usd="
        f"{_decimal_or_none(simulated_roundtrip_cost_usd)}"
    )
    print(f"paper.net_profit_usd={_decimal_or_none(paper_net_profit_usd)}")
    print(f"ledger_path={ledger_path or 'None'}")


def _run_one_paper_trade_route(
    *,
    route: RouteCandidate,
    assembled_at: datetime,
    ledger: Ledger,
) -> tuple[DecisionResult, VenueSnapshot | None, PaperRunResult | None, tuple[LedgerEvent, ...]]:
    start_event_count = len(ledger.records())
    risex_adapter = RiseXObservationAdapter()
    hedge_adapter = HyperliquidObservationAdapter()
    decision, snapshot = run_real_data_research_route_with_snapshot(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=hedge_adapter,
        assembled_at=assembled_at,
        mode=EvaluationMode.ENTRY,
    )
    paper_result = (
        None
        if snapshot is None
        else run_paper_lifecycle(
            route=route,
            decision=decision,
            funding_settlement_at=snapshot.risex_funding_settlement_at,
            ledger=ledger,
        )
    )
    return decision, snapshot, paper_result, ledger.records()[start_event_count:]


def _paper_session_summary_fields(
    *,
    route_count: int,
    decisions: Sequence[DecisionResult],
    snapshots: Sequence[VenueSnapshot | None],
    paper_results: Sequence[PaperRunResult | None],
    session_ledger_events: Sequence[LedgerEvent],
    ledger_path: str | None,
) -> dict[str, object]:
    status_counts = {
        status.value: sum(1 for decision in decisions if decision.status is status)
        for status in RouteStatus
    }
    decision_net_profit_known = sum(
        1 for decision in decisions if decision.net_profit_usd is not None
    )
    entry_ev_known = sum(1 for decision in decisions if decision.entry_ev is not None)
    paper_expected_funding_known = sum(
        1
        for paper_result in paper_results
        if (
            paper_result is not None
            and paper_result.explanation.expected_funding_usd is not None
        )
    )
    paper_total_fees_known = sum(
        1
        for paper_result in paper_results
        if paper_result is not None and paper_result.explanation.total_fees_usd is not None
    )
    paper_net_profit_known = sum(
        1
        for paper_result in paper_results
        if paper_result is not None and paper_result.explanation.net_profit_usd is not None
    )
    paper_started = sum(
        1 for paper_result in paper_results if paper_result is not None and paper_result.started
    )

    return {
        "routes_total": route_count,
        "routes_with_snapshot": sum(1 for snapshot in snapshots if snapshot is not None),
        "routes_without_snapshot": sum(1 for snapshot in snapshots if snapshot is None),
        "paper_started": paper_started,
        "paper_not_started": route_count - paper_started,
        "decision_status": status_counts,
        "entry_ev_known": entry_ev_known,
        "entry_ev_unknown": route_count - entry_ev_known,
        "paper_expected_funding_known": paper_expected_funding_known,
        "paper_expected_funding_unknown": route_count - paper_expected_funding_known,
        "paper_total_fees_known": paper_total_fees_known,
        "paper_total_fees_unknown": route_count - paper_total_fees_known,
        "decision_net_profit_known": decision_net_profit_known,
        "decision_net_profit_unknown": route_count - decision_net_profit_known,
        "paper_net_profit_known": paper_net_profit_known,
        "paper_net_profit_unknown": route_count - paper_net_profit_known,
        "ledger_event_count": len(session_ledger_events),
        "ledger_event_sequences": [event.sequence for event in session_ledger_events],
        "ledger_event_types": [event.event_type for event in session_ledger_events],
        "aggregate_paper_net_profit_usd": None,
        "ledger_path": ledger_path,
    }


def _print_paper_session_summary(
    *,
    route_count: int,
    decisions: Sequence[DecisionResult],
    snapshots: Sequence[VenueSnapshot | None],
    paper_results: Sequence[PaperRunResult | None],
    session_ledger_events: Sequence[LedgerEvent],
    ledger_path: str | None,
) -> None:
    summary = _paper_session_summary_fields(
        route_count=route_count,
        decisions=decisions,
        snapshots=snapshots,
        paper_results=paper_results,
        session_ledger_events=session_ledger_events,
        ledger_path=ledger_path,
    )
    status_counts = summary["decision_status"]
    assert isinstance(status_counts, dict)

    print("Paper Trade Session Summary")
    print(f"routes_total={summary['routes_total']}")
    print(f"routes_with_snapshot={summary['routes_with_snapshot']}")
    print(f"routes_without_snapshot={summary['routes_without_snapshot']}")
    print(f"paper_started={summary['paper_started']}")
    print(f"paper_not_started={summary['paper_not_started']}")
    for status in RouteStatus:
        print(f"decision_status.{status.value}={status_counts[status.value]}")
    print(f"entry_ev_known={summary['entry_ev_known']}")
    print(f"entry_ev_unknown={summary['entry_ev_unknown']}")
    print(f"paper_expected_funding_known={summary['paper_expected_funding_known']}")
    print(f"paper_expected_funding_unknown={summary['paper_expected_funding_unknown']}")
    print(f"paper_total_fees_known={summary['paper_total_fees_known']}")
    print(f"paper_total_fees_unknown={summary['paper_total_fees_unknown']}")
    print(f"decision_net_profit_known={summary['decision_net_profit_known']}")
    print(f"decision_net_profit_unknown={summary['decision_net_profit_unknown']}")
    print(f"paper_net_profit_known={summary['paper_net_profit_known']}")
    print(f"paper_net_profit_unknown={summary['paper_net_profit_unknown']}")
    print(f"ledger_event_count={summary['ledger_event_count']}")
    print(
        "ledger_event_sequences="
        f"{_join_or_none(tuple(str(sequence) for sequence in summary['ledger_event_sequences']))}"
    )
    print(
        "ledger_event_types="
        f"{_join_or_none(tuple(str(event_type) for event_type in summary['ledger_event_types']))}"
    )
    print("aggregate_paper_net_profit_usd=None")
    print(f"ledger_path={ledger_path or 'None'}")


def _ledger_event_json(event: LedgerEvent) -> dict[str, object]:
    return {
        "sequence": event.sequence,
        "event_type": event.event_type,
        "recorded_at": event.recorded_at.isoformat(),
        "payload": ledger_payload_to_jsonable(event.payload),
    }


def _paper_session_route_report_json(
    *,
    route_index: int,
    route: RouteCandidate,
    assembled_at: datetime,
    decision: DecisionResult,
    snapshot: VenueSnapshot | None,
    paper_result: PaperRunResult | None,
    route_events: Sequence[LedgerEvent],
) -> dict[str, object]:
    if paper_result is None:
        paper_json = {
            "started": False,
            "start_attribution": None,
            "start_blockers": ["public_snapshot_unavailable"],
            "expected_funding_usd": None,
            "total_fees_usd": None,
            "simulated_roundtrip_cost_usd": None,
            "net_profit_usd": None,
        }
    else:
        explanation = paper_result.explanation
        paper_json = {
            "started": paper_result.started,
            "start_attribution": explanation.paper_start_attribution,
            "start_blockers": list(explanation.paper_start_blockers),
            "expected_funding_usd": _decimal_json_or_none(
                explanation.expected_funding_usd
            ),
            "total_fees_usd": _decimal_json_or_none(explanation.total_fees_usd),
            "simulated_roundtrip_cost_usd": _decimal_json_or_none(
                explanation.simulated_roundtrip_cost_usd
            ),
            "net_profit_usd": _decimal_json_or_none(explanation.net_profit_usd),
        }

    return {
        "route_index": route_index,
        "route": {
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
        },
        "decision": {
            "mode": decision.mode.value,
            "status": decision.status.value,
            "reasons": [reason.value for reason in decision.reasons],
            "net_profit_usd": _decimal_json_or_none(decision.net_profit_usd),
            "entry_ev": {
                "expected_funding_usd": _entry_ev_json_or_none(
                    decision,
                    "expected_funding_usd",
                ),
                "total_fees_usd": _entry_ev_json_or_none(
                    decision,
                    "total_fees_usd",
                ),
                "simulated_roundtrip_cost_usd": _entry_ev_json_or_none(
                    decision,
                    "simulated_roundtrip_cost_usd",
                ),
                "net_profit_usd": _entry_ev_json_or_none(
                    decision,
                    "net_profit_usd",
                ),
            },
        },
        "snapshot": {
            "state": "UNKNOWN" if snapshot is None else "AVAILABLE",
            "funding_settlement_at": (
                None if snapshot is None else snapshot.risex_funding_settlement_at.isoformat()
            ),
        },
        "paper": paper_json,
        "ledger_events": [_ledger_event_json(event) for event in route_events],
    }


def _paper_session_report_json(
    *,
    route_inputs: Sequence[tuple[RouteCandidate, datetime]],
    decisions: Sequence[DecisionResult],
    snapshots: Sequence[VenueSnapshot | None],
    paper_results: Sequence[PaperRunResult | None],
    route_event_batches: Sequence[Sequence[LedgerEvent]],
    session_ledger_events: Sequence[LedgerEvent],
    ledger_path: str | None,
) -> dict[str, object]:
    route_reports: list[dict[str, object]] = []
    route_report_inputs = zip(
        route_inputs,
        decisions,
        snapshots,
        paper_results,
        route_event_batches,
        strict=True,
    )
    for route_index, (
        (route, assembled_at),
        decision,
        snapshot,
        paper_result,
        route_events,
    ) in enumerate(route_report_inputs, start=1):
        route_reports.append(
            _paper_session_route_report_json(
                route_index=route_index,
                route=route,
                assembled_at=assembled_at,
                decision=decision,
                snapshot=snapshot,
                paper_result=paper_result,
                route_events=route_events,
            )
        )

    return {
        "report": "Paper Trade Session Report",
        "schema_version": 1,
        "session": {
            "route_count": len(route_inputs),
            "ledger_path": ledger_path,
        },
        "routes": route_reports,
        "summary": _paper_session_summary_fields(
            route_count=len(route_inputs),
            decisions=decisions,
            snapshots=snapshots,
            paper_results=paper_results,
            session_ledger_events=session_ledger_events,
            ledger_path=ledger_path,
        ),
        "ledger_events": [_ledger_event_json(event) for event in session_ledger_events],
    }


def _write_paper_session_report_json(
    *,
    report_json_path: str,
    route_inputs: Sequence[tuple[RouteCandidate, datetime]],
    decisions: Sequence[DecisionResult],
    snapshots: Sequence[VenueSnapshot | None],
    paper_results: Sequence[PaperRunResult | None],
    route_event_batches: Sequence[Sequence[LedgerEvent]],
    session_ledger_events: Sequence[LedgerEvent],
    ledger_path: str | None,
) -> None:
    payload = _paper_session_report_json(
        route_inputs=route_inputs,
        decisions=decisions,
        snapshots=snapshots,
        paper_results=paper_results,
        route_event_batches=route_event_batches,
        session_ledger_events=session_ledger_events,
        ledger_path=ledger_path,
    )
    Path(report_json_path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_json_artifact(path: str, payload: object) -> None:
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _normalized_local_output_path(path: str) -> Path:
    try:
        return Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise argparse.ArgumentTypeError(
            f"local output path could not be normalized: {exc}"
        ) from exc


def _paper_session_package_preview_json(
    *,
    route_list: Sequence[Mapping[str, str]],
    routes_json_output_path: str,
    session_report_json_path: str,
) -> dict[str, object]:
    command_args = [
        "python3",
        "-m",
        "apps.cli.main",
        "paper-trade-session",
        "--routes-json-path",
        routes_json_output_path,
        "--session-report-json-path",
        session_report_json_path,
    ]
    return {
        "preview": "Paper Trade Session Operator Package",
        "schema_version": 1,
        "route_count": len(route_list),
        "route_ids": [route["route_id"] for route in route_list],
        "routes_json_path": routes_json_output_path,
        "session_report_json_path": session_report_json_path,
        "manual_command": {
            "argv": command_args,
            "text": shlex.join(command_args),
        },
    }


def _paper_session_display_command_preview_json(
    *,
    display_payload_json_path: str,
) -> dict[str, object]:
    command_args = [
        "python3",
        "-m",
        "apps.cli.main",
        "render-paper-session-report-from-payload",
        "--paper-session-display-command-payload-json-path",
        display_payload_json_path,
    ]
    return {
        "preview": "Paper Session Display Command Preview",
        "schema_version": 1,
        "display_payload_json_path": display_payload_json_path,
        "manual_command": {
            "argv": command_args,
            "text": shlex.join(command_args),
        },
    }


def _paper_session_display_command_text_preview_json(
    *,
    command_text_path: str,
    display_payload_json_path: str,
    session_report_json_path: str,
) -> dict[str, object]:
    command_args = [
        "python3",
        "-m",
        "apps.cli.main",
        "parse-paper-session-display-command-text",
        "--paper-session-display-command-text-path",
        command_text_path,
        "--display-payload-json-path",
        display_payload_json_path,
    ]
    return {
        "schema_version": 1,
        "command_text_fixture_path": command_text_path,
        "intended_display_payload_json_path": display_payload_json_path,
        "normalized_session_report_json_path": session_report_json_path,
        "manual_command": {
            "argv": command_args,
            "text": shlex.join(command_args),
        },
    }


def _paper_session_run_command_text_preview_json(
    *,
    command_text_path: str,
    command_paths: Mapping[str, str],
    route_list: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    command_args = [
        "python3",
        "-m",
        "apps.cli.main",
        "build-paper-session-package",
        "--paper-session-command-payload-json-path",
        command_paths["paper_session_command_payload_json_path"],
        "--routes-json-output-path",
        command_paths["routes_json_output_path"],
        "--preview-json-output-path",
        command_paths["preview_json_output_path"],
        "--session-report-json-path",
        command_paths["session_report_json_path"],
    ]
    return {
        "schema_version": 1,
        "command_text_fixture_path": command_text_path,
        "paper_session_command_payload_fixture_path": command_paths[
            "paper_session_command_payload_json_path"
        ],
        "intended_routes_json_output_path": command_paths["routes_json_output_path"],
        "intended_package_preview_json_output_path": command_paths[
            "preview_json_output_path"
        ],
        "intended_session_report_json_path": command_paths["session_report_json_path"],
        "route_count": len(route_list),
        "route_ids": [route["route_id"] for route in route_list],
        "manual_command": {
            "argv": command_args,
            "text": shlex.join(command_args),
        },
    }


def _paper_report_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise argparse.ArgumentTypeError(f"{field_name} must be an object")
    return value


def _paper_report_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise argparse.ArgumentTypeError(f"{field_name} must be an array")
    return value


def _paper_report_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise argparse.ArgumentTypeError(f"{field_name} must be an integer")
    return value


def _paper_report_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise argparse.ArgumentTypeError(f"{field_name} must be a non-empty string")
    return value


def _paper_report_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise argparse.ArgumentTypeError(f"{field_name} must be a boolean")
    return value


def _paper_report_economics_value(value: object, field_name: str) -> str:
    if value is None:
        return "null"
    if not isinstance(value, str):
        raise argparse.ArgumentTypeError(f"{field_name} must be a string or null")
    return value


def _paper_report_economics_field(
    mapping: Mapping[str, object],
    key: str,
    field_name: str,
) -> str:
    if key not in mapping:
        raise argparse.ArgumentTypeError(
            f"{field_name} must be present as a string or null"
        )
    return _paper_report_economics_value(mapping[key], field_name)


def _paper_report_bool_display(value: bool) -> str:
    return "true" if value else "false"


def _validated_paper_session_report_display_values(
    report: Mapping[str, object],
) -> dict[str, object]:
    if report.get("report") != "Paper Trade Session Report":
        raise argparse.ArgumentTypeError("report must be Paper Trade Session Report")
    if report.get("schema_version") != 1:
        raise argparse.ArgumentTypeError("schema_version must be 1")

    session = _paper_report_mapping(report.get("session"), "session")
    route_count = _paper_report_int(session.get("route_count"), "session.route_count")
    if route_count < 1 or route_count > _MAX_PAPER_SESSION_ROUTES:
        raise argparse.ArgumentTypeError(
            "session.route_count must be between 1 and "
            f"{_MAX_PAPER_SESSION_ROUTES}"
        )
    routes = _paper_report_list(report.get("routes"), "routes")
    if len(routes) != route_count:
        raise argparse.ArgumentTypeError(
            "routes length must match session.route_count"
        )

    route_displays: list[dict[str, object]] = []
    for index, route_item in enumerate(routes, start=1):
        route_report = _paper_report_mapping(route_item, f"routes[{index}]")
        route = _paper_report_mapping(
            route_report.get("route"),
            f"routes[{index}].route",
        )
        decision = _paper_report_mapping(
            route_report.get("decision"),
            f"routes[{index}].decision",
        )
        entry_ev = _paper_report_mapping(
            decision.get("entry_ev"),
            f"routes[{index}].decision.entry_ev",
        )
        paper = _paper_report_mapping(
            route_report.get("paper"),
            f"routes[{index}].paper",
        )

        route_displays.append(
            {
                "route_id": _paper_report_string(
                    route.get("route_id"),
                    f"routes[{index}].route.route_id",
                ),
                "decision_status": _paper_report_string(
                    decision.get("status"),
                    f"routes[{index}].decision.status",
                ),
                "paper_started": _paper_report_bool(
                    paper.get("started"),
                    f"routes[{index}].paper.started",
                ),
                "decision_net_profit_usd": _paper_report_economics_field(
                    decision,
                    "net_profit_usd",
                    f"routes[{index}].decision.net_profit_usd",
                ),
                "decision_entry_ev_expected_funding_usd": (
                    _paper_report_economics_field(
                        entry_ev,
                        "expected_funding_usd",
                        f"routes[{index}].decision.entry_ev.expected_funding_usd",
                    )
                ),
                "decision_entry_ev_total_fees_usd": (
                    _paper_report_economics_field(
                        entry_ev,
                        "total_fees_usd",
                        f"routes[{index}].decision.entry_ev.total_fees_usd",
                    )
                ),
                "decision_entry_ev_simulated_roundtrip_cost_usd": (
                    _paper_report_economics_field(
                        entry_ev,
                        "simulated_roundtrip_cost_usd",
                        "routes"
                        f"[{index}].decision.entry_ev.simulated_roundtrip_cost_usd",
                    )
                ),
                "decision_entry_ev_net_profit_usd": (
                    _paper_report_economics_field(
                        entry_ev,
                        "net_profit_usd",
                        f"routes[{index}].decision.entry_ev.net_profit_usd",
                    )
                ),
                "paper_expected_funding_usd": _paper_report_economics_field(
                    paper,
                    "expected_funding_usd",
                    f"routes[{index}].paper.expected_funding_usd",
                ),
                "paper_total_fees_usd": _paper_report_economics_field(
                    paper,
                    "total_fees_usd",
                    f"routes[{index}].paper.total_fees_usd",
                ),
                "paper_simulated_roundtrip_cost_usd": (
                    _paper_report_economics_field(
                        paper,
                        "simulated_roundtrip_cost_usd",
                        f"routes[{index}].paper.simulated_roundtrip_cost_usd",
                    )
                ),
                "paper_net_profit_usd": _paper_report_economics_field(
                    paper,
                    "net_profit_usd",
                    f"routes[{index}].paper.net_profit_usd",
                ),
            }
        )

    summary = _paper_report_mapping(report.get("summary"), "summary")
    summary_count_fields = (
        "entry_ev_known",
        "entry_ev_unknown",
        "paper_expected_funding_known",
        "paper_expected_funding_unknown",
        "paper_total_fees_known",
        "paper_total_fees_unknown",
        "decision_net_profit_known",
        "decision_net_profit_unknown",
        "paper_net_profit_known",
        "paper_net_profit_unknown",
    )
    summary_counts = {
        field_name: _paper_report_int(summary.get(field_name), f"summary.{field_name}")
        for field_name in summary_count_fields
    }
    if "aggregate_paper_net_profit_usd" not in summary:
        raise argparse.ArgumentTypeError(
            "summary.aggregate_paper_net_profit_usd must be present and null"
        )
    if summary["aggregate_paper_net_profit_usd"] is not None:
        raise argparse.ArgumentTypeError(
            "summary.aggregate_paper_net_profit_usd must be null"
        )

    return {
        "route_count": route_count,
        "route_displays": route_displays,
        "summary_counts": summary_counts,
        "aggregate_paper_net_profit_usd": "null",
    }


def _paper_session_report_display_lines(
    report: Mapping[str, object],
) -> tuple[str, ...]:
    display = _validated_paper_session_report_display_values(report)
    route_displays = display["route_displays"]
    assert isinstance(route_displays, list)
    summary_counts = display["summary_counts"]
    assert isinstance(summary_counts, dict)

    route_ids = tuple(str(route["route_id"]) for route in route_displays)
    lines = [
        "Paper Session Report Display",
        f"route_count={display['route_count']}",
        f"route_ids={_join_or_none(route_ids)}",
    ]
    route_field_names = (
        "route_id",
        "decision_status",
        "paper_started",
        "decision_net_profit_usd",
        "decision_entry_ev_expected_funding_usd",
        "decision_entry_ev_total_fees_usd",
        "decision_entry_ev_simulated_roundtrip_cost_usd",
        "decision_entry_ev_net_profit_usd",
        "paper_expected_funding_usd",
        "paper_total_fees_usd",
        "paper_simulated_roundtrip_cost_usd",
        "paper_net_profit_usd",
    )
    for index, route_display in enumerate(route_displays, start=1):
        for field_name in route_field_names:
            value = route_display[field_name]
            if isinstance(value, bool):
                rendered_value = _paper_report_bool_display(value)
            else:
                rendered_value = str(value)
            lines.append(f"route.{index}.{field_name}={rendered_value}")

    for field_name in sorted(summary_counts):
        lines.append(f"summary.{field_name}={summary_counts[field_name]}")
    lines.append(
        "summary.aggregate_paper_net_profit_usd="
        f"{display['aggregate_paper_net_profit_usd']}"
    )
    return tuple(lines)


def _run_render_paper_session_report(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        report_text = Path(args.session_report_json_path).read_text(encoding="utf-8")
        parsed_report = json.loads(report_text)
        report = _paper_report_mapping(parsed_report, "report")
        lines = _paper_session_report_display_lines(report)
    except OSError as exc:
        parser.error(f"session-report-json-path could not be read: {exc}")
    except json.JSONDecodeError as exc:
        parser.error(f"session-report-json-path must contain valid JSON: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    for line in lines:
        print(line)


def _run_render_paper_session_report_from_payload(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        payload_text = Path(
            args.paper_session_display_command_payload_json_path
        ).read_text(encoding="utf-8")
        session_report_json_path = (
            _paper_session_report_path_from_display_command_payload(payload_text)
        )
    except OSError as exc:
        parser.error(
            "paper-session-display-command-payload-json-path could not be read: "
            f"{exc}"
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    _run_render_paper_session_report(
        argparse.Namespace(session_report_json_path=session_report_json_path),
        parser,
    )


def _run_real_data_route(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    if (
        args.public_readiness_report_format is not None
        and not args.public_readiness_report
    ):
        parser.error("--public-readiness-report-format requires --public-readiness-report")

    try:
        route = RouteCandidate(
            route_id=args.route_id,
            capture_id=args.capture_id,
            risex_venue=args.risex_venue,
            risex_symbol=args.risex_symbol,
            risex_entry_side=args.risex_side,
            hedge_venue=args.hedge_venue,
            hedge_symbol=args.hedge_symbol,
            hedge_entry_side=args.hedge_side,
            target_notional_usd=args.target_notional_usd,
        )
    except ValueError as exc:
        parser.error(str(exc))

    risex_adapter = RiseXObservationAdapter()
    hedge_adapter = HyperliquidObservationAdapter()
    mode = EvaluationMode(args.mode)
    if args.public_readiness_report:
        decision, snapshot = run_real_data_research_route_with_snapshot(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=hedge_adapter,
            assembled_at=args.assembled_at,
            mode=mode,
        )
        if args.public_readiness_report_format == "json":
            _print_public_readiness_report_json(route, decision, snapshot)
        else:
            _print_public_readiness_report(route, decision, snapshot)
        return

    decision = run_real_data_research_route(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=hedge_adapter,
        assembled_at=args.assembled_at,
        mode=mode,
    )
    _print_real_data_decision(decision)


def _run_build_paper_session_package(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        payload_text = Path(args.paper_session_command_payload_json_path).read_text(
            encoding="utf-8"
        )
        route_list = _paper_session_route_list_from_command_payload(payload_text)
    except OSError as exc:
        parser.error(f"paper-session-command-payload-json-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    preview = _paper_session_package_preview_json(
        route_list=route_list,
        routes_json_output_path=args.routes_json_output_path,
        session_report_json_path=args.session_report_json_path,
    )
    _write_json_artifact(args.routes_json_output_path, route_list)
    _write_json_artifact(args.preview_json_output_path, preview)

    print("Paper Session Operator Package")
    print(f"route_count={len(route_list)}")
    print(
        "route_ids="
        f"{_join_or_none(tuple(str(route['route_id']) for route in route_list))}"
    )
    print(f"routes_json_path={args.routes_json_output_path}")
    print(f"preview_json_path={args.preview_json_output_path}")
    print(f"session_report_json_path={args.session_report_json_path}")


def _run_build_paper_session_run_command_text_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        command_text_fixture_path = _normalized_local_output_path(
            args.paper_session_run_command_text_path
        )
        run_preview_output_path = _normalized_local_output_path(
            args.preview_json_output_path
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    try:
        command_text = Path(args.paper_session_run_command_text_path).read_text(
            encoding="utf-8"
        )
        command_paths = _paper_session_package_command_paths_from_run_command_text(
            command_text
        )
    except OSError as exc:
        parser.error(f"paper-session-run-command-text-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    try:
        normalized_local_paths = {
            "paper-session-run-command-text-path": command_text_fixture_path,
            "paper-session-command-payload-json-path": _normalized_local_output_path(
                command_paths["paper_session_command_payload_json_path"]
            ),
            "preview-json-output-path": run_preview_output_path,
            "routes-json-output-path": _normalized_local_output_path(
                command_paths["routes_json_output_path"]
            ),
            "package-preview-json-output-path": _normalized_local_output_path(
                command_paths["preview_json_output_path"]
            ),
            "session-report-json-path": _normalized_local_output_path(
                command_paths["session_report_json_path"]
            ),
        }
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    seen_local_paths: dict[Path, str] = {}
    for path_name, normalized_path in normalized_local_paths.items():
        existing_name = seen_local_paths.get(normalized_path)
        if existing_name is not None:
            parser.error(
                f"{existing_name} and {path_name} must not resolve to the same "
                "local path"
            )
        seen_local_paths[normalized_path] = path_name

    try:
        payload_text = Path(
            command_paths["paper_session_command_payload_json_path"]
        ).read_text(encoding="utf-8")
        route_list = _paper_session_route_list_from_command_payload(payload_text)
    except OSError as exc:
        parser.error(f"paper-session-command-payload-json-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    preview = _paper_session_run_command_text_preview_json(
        command_text_path=args.paper_session_run_command_text_path,
        command_paths=command_paths,
        route_list=route_list,
    )
    _write_json_artifact(args.preview_json_output_path, preview)

    print("Paper Session Run Command Text Preview")
    print(f"command_text_path={args.paper_session_run_command_text_path}")
    print(
        "paper_session_command_payload_json_path="
        f"{command_paths['paper_session_command_payload_json_path']}"
    )
    print(f"routes_json_output_path={command_paths['routes_json_output_path']}")
    print(f"package_preview_json_output_path={command_paths['preview_json_output_path']}")
    print(f"session_report_json_path={command_paths['session_report_json_path']}")
    print(f"preview_json_path={args.preview_json_output_path}")
    print(f"route_count={len(route_list)}")


def _run_parse_paper_session_run_command_text(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        command_text_fixture_path = _normalized_local_output_path(
            args.paper_session_run_command_text_path
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    try:
        command_text = Path(args.paper_session_run_command_text_path).read_text(
            encoding="utf-8"
        )
        command_paths = _paper_session_package_command_paths_from_run_command_text(
            command_text
        )
    except OSError as exc:
        parser.error(f"paper-session-run-command-text-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    try:
        normalized_local_paths = {
            "paper-session-run-command-text-path": command_text_fixture_path,
            "paper-session-command-payload-json-path": _normalized_local_output_path(
                command_paths["paper_session_command_payload_json_path"]
            ),
            "routes-json-output-path": _normalized_local_output_path(
                command_paths["routes_json_output_path"]
            ),
            "package-preview-json-output-path": _normalized_local_output_path(
                command_paths["preview_json_output_path"]
            ),
            "session-report-json-path": _normalized_local_output_path(
                command_paths["session_report_json_path"]
            ),
        }
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    seen_local_paths: dict[Path, str] = {}
    for path_name, normalized_path in normalized_local_paths.items():
        existing_name = seen_local_paths.get(normalized_path)
        if existing_name is not None:
            parser.error(
                f"{existing_name} and {path_name} must not resolve to the same "
                "local path"
            )
        seen_local_paths[normalized_path] = path_name

    try:
        payload_text = Path(
            command_paths["paper_session_command_payload_json_path"]
        ).read_text(encoding="utf-8")
        route_list = _paper_session_route_list_from_command_payload(payload_text)
    except OSError as exc:
        parser.error(f"paper-session-command-payload-json-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    preview = _paper_session_package_preview_json(
        route_list=route_list,
        routes_json_output_path=command_paths["routes_json_output_path"],
        session_report_json_path=command_paths["session_report_json_path"],
    )
    _write_json_artifact(command_paths["routes_json_output_path"], route_list)
    _write_json_artifact(command_paths["preview_json_output_path"], preview)

    print("Paper Session Run Command Text Parser")
    print(f"command_text_path={args.paper_session_run_command_text_path}")
    print(
        "paper_session_command_payload_json_path="
        f"{command_paths['paper_session_command_payload_json_path']}"
    )
    print(f"route_count={len(route_list)}")
    print(
        "route_ids="
        f"{_join_or_none(tuple(str(route['route_id']) for route in route_list))}"
    )
    print(f"routes_json_path={command_paths['routes_json_output_path']}")
    print(f"preview_json_path={command_paths['preview_json_output_path']}")
    print(f"session_report_json_path={command_paths['session_report_json_path']}")


def _run_build_paper_session_display_payload(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        report_text = Path(args.session_report_json_path).read_text(encoding="utf-8")
        parsed_report = json.loads(report_text)
        report = _paper_report_mapping(parsed_report, "report")
        _validated_paper_session_report_display_values(report)
        payload = {
            "schema_version": 1,
            "session_report_json_path": args.session_report_json_path,
        }
        parsed_payload_report_path = (
            _paper_session_report_path_from_display_command_payload(
                json.dumps(payload, sort_keys=True)
            )
        )
        if parsed_payload_report_path != args.session_report_json_path:
            raise argparse.ArgumentTypeError(
                "display payload session_report_json_path did not round-trip"
            )
    except OSError as exc:
        parser.error(f"session-report-json-path could not be read: {exc}")
    except json.JSONDecodeError as exc:
        parser.error(f"session-report-json-path must contain valid JSON: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    _write_json_artifact(args.display_payload_json_path, payload)

    print(f"display_payload_json_path={args.display_payload_json_path}")
    print(f"session_report_json_path={args.session_report_json_path}")


def _run_build_paper_session_display_command_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        payload_text = Path(
            args.paper_session_display_command_payload_json_path
        ).read_text(encoding="utf-8")
        _paper_session_report_path_from_display_command_payload(payload_text)
    except OSError as exc:
        parser.error(
            "paper-session-display-command-payload-json-path could not be read: "
            f"{exc}"
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    preview = _paper_session_display_command_preview_json(
        display_payload_json_path=args.paper_session_display_command_payload_json_path
    )
    _write_json_artifact(args.preview_json_output_path, preview)

    print("Paper Session Display Command Preview")
    print(
        "display_payload_json_path="
        f"{args.paper_session_display_command_payload_json_path}"
    )
    print(f"preview_json_path={args.preview_json_output_path}")


def _run_parse_paper_session_display_command_text(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        command_text = Path(
            args.paper_session_display_command_text_path
        ).read_text(encoding="utf-8")
        payload = _paper_session_display_command_payload_from_command_text(
            command_text
        )
        session_report_json_path = _paper_session_report_path_from_display_command_payload(
            json.dumps(payload, sort_keys=True)
        )
    except OSError as exc:
        parser.error(f"paper-session-display-command-text-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    if payload["session_report_json_path"] != session_report_json_path:
        parser.error(
            "display payload session_report_json_path did not round-trip"
        )

    _write_json_artifact(args.display_payload_json_path, payload)

    print("Paper Session Display Command Text Parser")
    print(f"command_text_path={args.paper_session_display_command_text_path}")
    print(f"display_payload_json_path={args.display_payload_json_path}")
    print(f"session_report_json_path={session_report_json_path}")


def _run_build_paper_session_display_command_text_preview(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        display_payload_output_path = _normalized_local_output_path(
            args.display_payload_json_path
        )
        preview_output_path = _normalized_local_output_path(args.preview_json_output_path)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    if display_payload_output_path == preview_output_path:
        parser.error(
            "display-payload-json-path and preview-json-output-path must not "
            "resolve to the same local path"
        )

    try:
        command_text = Path(
            args.paper_session_display_command_text_path
        ).read_text(encoding="utf-8")
        payload = _paper_session_display_command_payload_from_command_text(
            command_text
        )
        session_report_json_path = _paper_session_report_path_from_display_command_payload(
            json.dumps(payload, sort_keys=True)
        )
    except OSError as exc:
        parser.error(f"paper-session-display-command-text-path could not be read: {exc}")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    if payload["session_report_json_path"] != session_report_json_path:
        parser.error("display payload session_report_json_path did not round-trip")

    preview = _paper_session_display_command_text_preview_json(
        command_text_path=args.paper_session_display_command_text_path,
        display_payload_json_path=args.display_payload_json_path,
        session_report_json_path=session_report_json_path,
    )
    _write_json_artifact(args.preview_json_output_path, preview)

    print("Paper Session Display Command Text Preview")
    print(f"command_text_path={args.paper_session_display_command_text_path}")
    print(f"intended_display_payload_json_path={args.display_payload_json_path}")
    print(f"preview_json_path={args.preview_json_output_path}")
    print(f"session_report_json_path={session_report_json_path}")


def _run_paper_trade_route(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        route = RouteCandidate(
            route_id=args.route_id,
            capture_id=args.capture_id,
            risex_venue=args.risex_venue,
            risex_symbol=args.risex_symbol,
            risex_entry_side=args.risex_side,
            hedge_venue=args.hedge_venue,
            hedge_symbol=args.hedge_symbol,
            hedge_entry_side=args.hedge_side,
            target_notional_usd=args.target_notional_usd,
        )
    except ValueError as exc:
        parser.error(str(exc))

    ledger = (
        SQLiteLedger(args.ledger_sqlite_path)
        if args.ledger_sqlite_path is not None
        else InMemoryLedger()
    )
    try:
        decision, snapshot, paper_result, _route_events = _run_one_paper_trade_route(
            route=route,
            assembled_at=args.assembled_at,
            ledger=ledger,
        )
        ledger_events = ledger.records()
        _print_paper_trade_summary(
            route=route,
            decision=decision,
            snapshot=snapshot,
            paper_result=paper_result,
            ledger_events=ledger_events,
            ledger_path=args.ledger_sqlite_path,
        )
    finally:
        close = getattr(ledger, "close", None)
        if close is not None:
            close()


def _run_paper_trade_session(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        route_inputs = _paper_session_routes_from_json_path(args.routes_json_path)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    ledger = (
        SQLiteLedger(args.ledger_sqlite_path)
        if args.ledger_sqlite_path is not None
        else InMemoryLedger()
    )
    try:
        session_start_event_count = len(ledger.records())
        decisions: list[DecisionResult] = []
        snapshots: list[VenueSnapshot | None] = []
        paper_results: list[PaperRunResult | None] = []
        route_event_batches: list[tuple[LedgerEvent, ...]] = []

        print("Paper Trade Session")
        print(f"route_count={len(route_inputs)}")
        print(f"ledger_path={args.ledger_sqlite_path or 'None'}")
        for route_index, (route, assembled_at) in enumerate(route_inputs, start=1):
            decision, snapshot, paper_result, route_events = _run_one_paper_trade_route(
                route=route,
                assembled_at=assembled_at,
                ledger=ledger,
            )
            decisions.append(decision)
            snapshots.append(snapshot)
            paper_results.append(paper_result)
            route_event_batches.append(tuple(route_events))

            print(f"session_route_index={route_index}")
            _print_paper_trade_summary(
                route=route,
                decision=decision,
                snapshot=snapshot,
                paper_result=paper_result,
                ledger_events=route_events,
                ledger_path=args.ledger_sqlite_path,
            )

        session_ledger_events = ledger.records()[session_start_event_count:]
        _print_paper_session_summary(
            route_count=len(route_inputs),
            decisions=decisions,
            snapshots=snapshots,
            paper_results=paper_results,
            session_ledger_events=session_ledger_events,
            ledger_path=args.ledger_sqlite_path,
        )
        if args.session_report_json_path is not None:
            _write_paper_session_report_json(
                report_json_path=args.session_report_json_path,
                route_inputs=route_inputs,
                decisions=decisions,
                snapshots=snapshots,
                paper_results=paper_results,
                route_event_batches=route_event_batches,
                session_ledger_events=session_ledger_events,
                ledger_path=args.ledger_sqlite_path,
            )
    finally:
        close = getattr(ledger, "close", None)
        if close is not None:
            close()


def main(argv: Sequence[str] | None = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if not args:
        _run_fake_scan_refresh()
        return 0

    parser = _build_parser()
    parsed = parser.parse_args(args)
    parsed.handler(parsed, parser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
