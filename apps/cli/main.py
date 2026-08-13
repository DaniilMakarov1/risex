"""CLI entrypoints for deterministic research workflows."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation

from apps.research_runner.real_data import run_real_data_research_route
from apps.research_runner.fake_data import (
    build_fake_focused_refresh_observations,
    build_fake_route_candidates_and_observations,
)
from core.domain.contracts import (
    DecisionResult,
    RouteCandidate,
    VALID_ORDER_SIDES,
    validate_timezone_aware_datetime,
)
from core.domain.enums import EvaluationMode
from core.pipeline.scan_refresh import run_broad_scan, run_focused_refresh
from core.venues.hyperliquid import HyperliquidObservationAdapter
from core.venues.risex import RiseXObservationAdapter


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
    real_data_route.set_defaults(handler=_run_real_data_route)

    return parser


def _decimal_or_none(value: Decimal | None) -> str:
    return "None" if value is None else str(value)


def _entry_ev_decimal_or_none(decision: DecisionResult, field_name: str) -> str:
    if decision.entry_ev is None:
        return "None"
    return _decimal_or_none(getattr(decision.entry_ev, field_name))


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


def _run_real_data_route(
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

    decision = run_real_data_research_route(
        route=route,
        risex_adapter=RiseXObservationAdapter(),
        hedge_adapter=HyperliquidObservationAdapter(),
        assembled_at=args.assembled_at,
        mode=EvaluationMode(args.mode),
    )
    _print_real_data_decision(decision)


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
