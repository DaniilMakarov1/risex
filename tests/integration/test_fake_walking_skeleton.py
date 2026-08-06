from dataclasses import replace
from decimal import Decimal

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.accounting.ledger import InMemoryLedger
from core.config.product_rules import ProductRules
from core.domain.contracts import EstimatedValue, FundingSnapshot, OrderBook, OrderBookLevel
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.liquidity import calculate_executable_quote
from core.pipeline.evaluate import evaluate_route


def test_fake_walking_skeleton_evaluates_without_exchange_api() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    ledger = InMemoryLedger()

    decision = evaluate_route(route, snapshot, EvaluationMode.DISCOVERY, ledger=ledger)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.capture_plan is None
    assert len(ledger.records()) == 1


def test_profitable_fake_route_is_paper_eligible_with_live_disabled() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=False),
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.net_profit_usd is not None
    assert decision.net_profit_usd >= Decimal("1")
    assert decision.capture_plan is None
    assert RejectReason.LIVE_TRADING_DISABLED in decision.reasons


def test_route_rejects_when_required_orderbook_leg_cannot_execute_minimum() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    shallow_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(),
        asks=(OrderBookLevel(price=Decimal("100"), size=Decimal("4")),),
    )
    bad_snapshot = replace(
        snapshot,
        risex_entry_quote=calculate_executable_quote(
            order_book=shallow_book,
            side="buy",
            target_notional_usd=Decimal("500"),
        ),
    )

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL,)
    assert decision.capture_plan is None


def test_route_rejects_when_net_profit_is_below_minimum() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_profit_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=Decimal("0.1"), source=ValueSource.OBSERVED),
            hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
        ),
    )

    decision = evaluate_route(route, low_profit_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.MIN_NET_PROFIT_NOT_MET,)
    assert decision.capture_plan is None


def test_missing_funding_data_does_not_produce_live_eligible() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    missing_funding_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
            hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        ),
    )

    decision = evaluate_route(
        route,
        missing_funding_snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert decision.status is RouteStatus.REJECTED
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decision.capture_plan is None
