from decimal import Decimal

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.config.product_rules import ProductRules
from core.domain.enums import EvaluationMode, RouteStatus
from core.pipeline.evaluate import evaluate_route


def test_evaluate_route_does_not_create_live_capture_plan_when_live_disabled() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=False),
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.capture_plan is None
    assert "live_trading_disabled" in decision.reasons


def test_evaluate_route_rejects_when_net_profit_below_minimum() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_profit_snapshot = snapshot.__class__(
        captured_at=snapshot.captured_at,
        risex_entry_quote=snapshot.risex_entry_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
        hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
        expected_risex_funding_usd=Decimal("0.1"),
        expected_hedge_funding_usd=Decimal("0"),
        documented_fees_usd=Decimal("0"),
    )

    decision = evaluate_route(route, low_profit_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == ("min_net_profit_not_met",)


def test_evaluate_route_rejects_when_500_not_executable() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_quote = snapshot.risex_entry_quote.__class__(
        venue=snapshot.risex_entry_quote.venue,
        symbol=snapshot.risex_entry_quote.symbol,
        side=snapshot.risex_entry_quote.side,
        target_notional_usd=Decimal("499.99"),
        vwap_price=snapshot.risex_entry_quote.vwap_price,
        executable=True,
    )
    bad_snapshot = snapshot.__class__(
        captured_at=snapshot.captured_at,
        risex_entry_quote=bad_quote,
        hedge_entry_quote=snapshot.hedge_entry_quote,
        risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
        hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
        expected_risex_funding_usd=snapshot.expected_risex_funding_usd,
        expected_hedge_funding_usd=snapshot.expected_hedge_funding_usd,
        documented_fees_usd=snapshot.documented_fees_usd,
    )

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons[0].startswith("not_executable_for_min_notional")
