from __future__ import annotations

import importlib
import sys
from dataclasses import replace
from decimal import Decimal

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.config.product_rules import ProductRules
from core.domain.contracts import EstimatedValue, FeeComponent, FeeModel, FundingSnapshot
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.pipeline.evaluate import evaluate_route


def _replace_snapshot_quote(snapshot, quote_name: str, **changes):
    return replace(snapshot, **{quote_name: replace(getattr(snapshot, quote_name), **changes)})


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
    assert RejectReason.LIVE_TRADING_DISABLED in decision.reasons


def test_evaluate_route_rejects_when_net_profit_below_minimum() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_profit_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=Decimal("0.1"), source=snapshot.funding.risex_funding_usd.source),
            hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=snapshot.funding.hedge_funding_usd.source),
        ),
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="zero_fees",
                    amount_usd=EstimatedValue(value=Decimal("0"), source=snapshot.fees.components[0].amount_usd.source),
                ),
            )
        ),
    )

    decision = evaluate_route(route, low_profit_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.MIN_NET_PROFIT_NOT_MET,)


def test_evaluate_route_rejects_when_500_not_executable() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_quote = snapshot.risex_entry_quote.__class__(
        venue=snapshot.risex_entry_quote.venue,
        symbol=snapshot.risex_entry_quote.symbol,
        side=snapshot.risex_entry_quote.side,
        target_notional_usd=route.target_notional_usd,
        vwap_price=None,
        executable=False,
    )
    bad_snapshot = replace(snapshot, risex_entry_quote=bad_quote)

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL,)


def test_evaluate_route_rejects_when_route_notional_is_below_minimum() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    low_notional_route = replace(route, target_notional_usd=Decimal("499.99"))

    decision = evaluate_route(low_notional_route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.MIN_LEG_NOTIONAL_NOT_MET,)


def test_evaluate_route_rejects_route_notional_mismatched_with_quote_notional() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    larger_route = replace(route, target_notional_usd=Decimal("10000"))

    decision = evaluate_route(larger_route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)
    assert decision.capture_plan is None


def test_evaluate_route_rejects_wrong_risex_quote_symbol() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_snapshot = _replace_snapshot_quote(
        snapshot,
        "risex_entry_quote",
        symbol="ETH-PERP",
    )

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


@pytest.mark.parametrize(
    ("quote_name", "changes"),
    (
        ("hedge_entry_quote", {"venue": "OtherVenue"}),
        ("hedge_estimated_exit_quote", {"symbol": "ETH"}),
    ),
)
def test_evaluate_route_rejects_wrong_hedge_quote_venue_or_symbol(
    quote_name: str,
    changes: dict[str, str],
) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_snapshot = _replace_snapshot_quote(snapshot, quote_name, **changes)

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_evaluate_route_rejects_entry_quote_side_that_does_not_match_route() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_snapshot = _replace_snapshot_quote(snapshot, "risex_entry_quote", side="sell")

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_evaluate_route_rejects_non_opposing_route_entry_sides() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_route = replace(route, hedge_entry_side=route.risex_entry_side)

    decision = evaluate_route(bad_route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_evaluate_route_rejects_quote_not_sourced_from_orderbook() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bad_snapshot = _replace_snapshot_quote(
        snapshot,
        "risex_entry_quote",
        source=ValueSource.OBSERVED,
    )

    decision = evaluate_route(route, bad_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_evaluate_route_keeps_live_gates_closed_even_when_live_switch_is_enabled() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_GATES_NOT_IMPLEMENTED,)


def test_evaluate_route_rejects_missing_funding_economics_data() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    missing_funding_snapshot = replace(
        snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
            hedge_funding_usd=snapshot.funding.hedge_funding_usd,
        ),
    )

    decision = evaluate_route(route, missing_funding_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decision.capture_plan is None


def test_evaluate_route_rejects_missing_fee_economics_data() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    missing_fee_snapshot = replace(
        snapshot,
        fees=FeeModel(
            components=(
                FeeComponent(
                    name="unknown_fee",
                    amount_usd=EstimatedValue(value=None, source=ValueSource.UNKNOWN),
                ),
            )
        ),
    )

    decision = evaluate_route(route, missing_fee_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decision.capture_plan is None


def test_evaluate_route_does_not_mask_unexpected_programming_value_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    route, snapshot = build_fake_route_and_snapshot()
    evaluate_module = importlib.import_module("core.pipeline.evaluate")

    def fail_with_programming_error(_snapshot):
        raise ValueError("programming defect")

    monkeypatch.setattr(evaluate_module, "calculate_entry_ev", fail_with_programming_error)

    with pytest.raises(ValueError, match="programming defect"):
        evaluate_module.evaluate_route(route, snapshot, EvaluationMode.ENTRY)


def test_poor_executable_price_impact_changes_pnl_without_technical_rejection() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    baseline_decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)
    poor_snapshot = _replace_snapshot_quote(
        snapshot,
        "risex_estimated_exit_quote",
        vwap_price=Decimal("90"),
        best_price=Decimal("90"),
        worst_price=Decimal("90"),
        price_impact_bps=Decimal("1000"),
    )
    funded_snapshot = replace(
        poor_snapshot,
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=Decimal("100"), source=ValueSource.OBSERVED),
            hedge_funding_usd=poor_snapshot.funding.hedge_funding_usd,
        ),
    )

    decision = evaluate_route(route, funded_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.entry_ev is not None
    assert baseline_decision.entry_ev is not None
    assert decision.entry_ev.simulated_roundtrip_cost_usd > baseline_decision.entry_ev.simulated_roundtrip_cost_usd
    assert RejectReason.TECHNICALLY_NOT_EXECUTABLE not in decision.reasons
    assert RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL not in decision.reasons


def test_evaluate_route_does_not_import_execution_order_placement() -> None:
    for module_name in list(sys.modules):
        if module_name == "core.execution" or module_name.startswith("core.execution."):
            del sys.modules[module_name]

    evaluate_module = importlib.import_module("core.pipeline.evaluate")
    evaluate_module = importlib.reload(evaluate_module)
    route, snapshot = build_fake_route_and_snapshot()

    decision = evaluate_module.evaluate_route(route, snapshot, EvaluationMode.DISCOVERY)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
