"""CLI entrypoints for deterministic research workflows."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation

from apps.paper_runner.lifecycle import PaperRunResult, run_paper_lifecycle
from apps.research_runner.real_data import (
    run_real_data_research_route,
    run_real_data_research_route_with_snapshot,
)
from apps.research_runner.fake_data import (
    build_fake_focused_refresh_observations,
    build_fake_route_candidates_and_observations,
)
from core.accounting.ledger import InMemoryLedger, LedgerEvent
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
        risex_adapter = RiseXObservationAdapter()
        hedge_adapter = HyperliquidObservationAdapter()
        decision, snapshot = run_real_data_research_route_with_snapshot(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=hedge_adapter,
            assembled_at=args.assembled_at,
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
