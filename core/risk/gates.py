"""Risk gates live here only."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from core.config.product_rules import ProductRules
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
    ExecutionCapabilityEvidence,
    ExecutableQuote,
    OrderSide,
    RouteCandidate,
    VALID_ORDER_SIDES,
    VenueSnapshot,
)
from core.domain.enums import RejectReason, ValueSource
from core.economics.liquidity import quote_is_executable_for_notional


REQUIRED_ORDERBOOK_QUOTE_SOURCE = ValueSource.ESTIMATED_FROM_ORDERBOOK


def _side_is_valid(side: str) -> bool:
    return side in VALID_ORDER_SIDES


def _datetime_is_timezone_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def _opposite_side(side: OrderSide) -> OrderSide | None:
    if side == "buy":
        return "sell"
    if side == "sell":
        return "buy"
    return None


def _quote_matches_leg(quote: ExecutableQuote, *, venue: str, symbol: str) -> bool:
    return quote.venue == venue and quote.symbol == symbol


def check_min_leg_notional(route: RouteCandidate, rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """Reject only if the route cannot meet the configured minimum notional."""

    if route.target_notional_usd < rules.min_leg_notional_usd:
        return False, RejectReason.MIN_LEG_NOTIONAL_NOT_MET
    return True, None


def check_route_snapshot_alignment(
    route: RouteCandidate,
    snapshot: VenueSnapshot,
) -> tuple[bool, RejectReason | None]:
    """Reject snapshots that do not represent the authoritative route contract."""

    if not _side_is_valid(route.risex_entry_side) or not _side_is_valid(route.hedge_entry_side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if route.risex_entry_side == route.hedge_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    risex_entry = snapshot.risex_entry_quote
    risex_exit = snapshot.risex_estimated_exit_quote
    hedge_entry = snapshot.hedge_entry_quote
    hedge_exit = snapshot.hedge_estimated_exit_quote

    if not _quote_matches_leg(risex_entry, venue=route.risex_venue, symbol=route.risex_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(risex_exit, venue=route.risex_venue, symbol=route.risex_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_entry, venue=route.hedge_venue, symbol=route.hedge_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_exit, venue=route.hedge_venue, symbol=route.hedge_symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    if risex_entry.side != route.risex_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if hedge_entry.side != route.hedge_entry_side:
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if risex_exit.side != _opposite_side(risex_entry.side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if hedge_exit.side != _opposite_side(hedge_entry.side):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    for quote in snapshot.executable_quotes():
        if quote.target_notional_usd != route.target_notional_usd:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if quote.source is not REQUIRED_ORDERBOOK_QUOTE_SOURCE:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    if not _quote_matches_leg(risex_entry, venue=risex_exit.venue, symbol=risex_exit.symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    if not _quote_matches_leg(hedge_entry, venue=hedge_exit.venue, symbol=hedge_exit.symbol):
        return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE

    return True, None


def check_snapshot_executability(
    snapshot: VenueSnapshot,
    rules: ProductRules,
) -> tuple[bool, RejectReason | None]:
    """Reject only when the provided VWAP quotes cannot execute the required notional."""

    for quote in snapshot.executable_quotes():
        if not quote_is_executable_for_notional(
            quote,
            min_leg_notional_usd=rules.min_leg_notional_usd,
        ):
            return False, RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL
    return True, None


def check_min_net_profit(net_profit_usd: Decimal, rules: ProductRules) -> tuple[bool, RejectReason | None]:
    """Reject only when explicit EV is below the configured minimum net profit."""

    if net_profit_usd < rules.min_net_profit_usd:
        return False, RejectReason.MIN_NET_PROFIT_NOT_MET
    return True, None


def check_ledger_reconciliation_gate(
    ledger_explicitly_reconciled: bool,
) -> tuple[bool, RejectReason | None]:
    """Future live paths require is_ledger_explicitly_reconciled(...) output."""

    if ledger_explicitly_reconciled is not True:
        return False, RejectReason.LEDGER_NOT_RECONCILED
    return True, None


def check_capture_plan_freshness_gate(
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    evaluated_at: datetime,
    plan_evidence: Sequence[CapturePlanFreshnessEvidence] | None,
) -> tuple[bool, RejectReason | None]:
    """Future live paths require exactly one fresh fake plan evidence record."""

    if not _datetime_is_timezone_aware(settlement_time) or not _datetime_is_timezone_aware(
        evaluated_at
    ):
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if plan_evidence is None or len(plan_evidence) != 1:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH

    evidence = plan_evidence[0]
    if not isinstance(evidence, CapturePlanFreshnessEvidence):
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if (
        not _datetime_is_timezone_aware(evidence.settlement_time)
        or not _datetime_is_timezone_aware(evidence.planned_at)
        or not _datetime_is_timezone_aware(evidence.valid_until)
    ):
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if not isinstance(evidence.source, ValueSource) or evidence.source is ValueSource.UNKNOWN:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if evidence.capture_id != route.capture_id:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if evidence.route_id != route.route_id:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if evidence.settlement_time != settlement_time:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if evidence.planned_at > evaluated_at:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    if evaluated_at >= evidence.valid_until:
        return False, RejectReason.CAPTURE_PLAN_NOT_FRESH
    return True, None


def check_execution_capability_gate(
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    evaluated_at: datetime,
    execution_evidence: Sequence[ExecutionCapabilityEvidence] | None,
) -> tuple[bool, RejectReason | None]:
    """Future live paths require fresh full-target order-book quote evidence."""

    if not _datetime_is_timezone_aware(settlement_time) or not _datetime_is_timezone_aware(
        evaluated_at
    ):
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if execution_evidence is None or len(execution_evidence) != 1:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING

    evidence = execution_evidence[0]
    if not isinstance(evidence, ExecutionCapabilityEvidence):
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if (
        not _datetime_is_timezone_aware(evidence.settlement_time)
        or not _datetime_is_timezone_aware(evidence.checked_at)
        or not _datetime_is_timezone_aware(evidence.valid_until)
    ):
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evidence.source is not REQUIRED_ORDERBOOK_QUOTE_SOURCE:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evidence.capture_id != route.capture_id:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evidence.route_id != route.route_id:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evidence.settlement_time != settlement_time:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evidence.checked_at > evaluated_at:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
    if evaluated_at >= evidence.valid_until:
        return False, RejectReason.REQUIRED_LIVE_DATA_MISSING

    quote_requirements = (
        (
            evidence.risex_entry_quote,
            route.risex_venue,
            route.risex_symbol,
            route.risex_entry_side,
        ),
        (
            evidence.hedge_entry_quote,
            route.hedge_venue,
            route.hedge_symbol,
            route.hedge_entry_side,
        ),
        (
            evidence.risex_estimated_exit_quote,
            route.risex_venue,
            route.risex_symbol,
            _opposite_side(route.risex_entry_side),
        ),
        (
            evidence.hedge_estimated_exit_quote,
            route.hedge_venue,
            route.hedge_symbol,
            _opposite_side(route.hedge_entry_side),
        ),
    )
    for quote, venue, symbol, side in quote_requirements:
        if not isinstance(quote, ExecutableQuote):
            return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
        if quote.source is not REQUIRED_ORDERBOOK_QUOTE_SOURCE:
            return False, RejectReason.REQUIRED_LIVE_DATA_MISSING
        if side is None or quote.side != side:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if not _quote_matches_leg(quote, venue=venue, symbol=symbol):
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if quote.target_notional_usd != route.target_notional_usd:
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
        if not quote_is_executable_for_notional(
            quote,
            min_leg_notional_usd=route.target_notional_usd,
        ):
            return False, RejectReason.TECHNICALLY_NOT_EXECUTABLE
    return True, None


def check_live_capture_allowed(
    rules: ProductRules,
    *,
    route: RouteCandidate,
    settlement_time: datetime,
    evaluated_at: datetime,
    ledger_explicitly_reconciled: bool = False,
    capture_plan_evidence: Sequence[CapturePlanFreshnessEvidence] | None = None,
    execution_capability_evidence: Sequence[ExecutionCapabilityEvidence] | None = None,
) -> tuple[bool, RejectReason | None]:
    """Live capture plans remain blocked until future live gates are implemented."""

    if not rules.live_trading_enabled:
        return False, RejectReason.LIVE_TRADING_DISABLED
    ok, reason = check_ledger_reconciliation_gate(ledger_explicitly_reconciled)
    if not ok:
        return False, reason
    ok, reason = check_capture_plan_freshness_gate(
        route=route,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
        plan_evidence=capture_plan_evidence,
    )
    if not ok:
        return False, reason
    ok, reason = check_execution_capability_gate(
        route=route,
        settlement_time=settlement_time,
        evaluated_at=evaluated_at,
        execution_evidence=execution_capability_evidence,
    )
    if not ok:
        return False, reason
    return False, RejectReason.LIVE_GATES_NOT_IMPLEMENTED
