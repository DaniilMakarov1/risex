from __future__ import annotations

import importlib
import sys
from dataclasses import fields, replace
from datetime import timedelta
from decimal import Decimal

import pytest

from apps.research_runner.fake_data import build_fake_route_and_snapshot
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    CapturePlanFreshnessEvidence,
    EstimatedValue,
    ExecutionCapabilityEvidence,
    ExecutableQuote,
    FeeComponent,
    FeeModel,
    FundingSnapshot,
    LiveGateEvidenceBundle,
    OrderBook,
    OrderBookLevel,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.economics.liquidity import calculate_executable_quote
from core.pipeline.evaluate import evaluate_route


def _replace_snapshot_quote(snapshot, quote_name: str, **changes):
    return replace(snapshot, **{quote_name: replace(getattr(snapshot, quote_name), **changes)})


def _forge_quote(quote: ExecutableQuote, **changes) -> ExecutableQuote:
    values = {field.name: getattr(quote, field.name) for field in fields(ExecutableQuote)}
    values.update(changes)
    forged = object.__new__(ExecutableQuote)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _live_gate_evidence_bundle(route, snapshot, **changes) -> LiveGateEvidenceBundle:
    values = {
        "capture_id": route.capture_id,
        "route_id": route.route_id,
        "settlement_time": snapshot.risex_funding_settlement_at,
        "funding_settlement_verified": True,
        "ledger_explicitly_reconciled": True,
        "capture_plan_evidence": (
            CapturePlanFreshnessEvidence(
                plan_id="fake-plan-001",
                plan_version="fake-v1",
                capture_id=route.capture_id,
                route_id=route.route_id,
                settlement_time=snapshot.risex_funding_settlement_at,
                planned_at=snapshot.captured_at,
                valid_until=snapshot.captured_at + timedelta(minutes=5),
                source=ValueSource.OBSERVED,
                ledger_reconciliation_event_sequence=11,
            ),
        ),
        "execution_capability_evidence": (
            ExecutionCapabilityEvidence(
                capture_id=route.capture_id,
                route_id=route.route_id,
                settlement_time=snapshot.risex_funding_settlement_at,
                checked_at=snapshot.captured_at,
                valid_until=snapshot.captured_at + timedelta(minutes=1),
                source=ValueSource.ESTIMATED_FROM_ORDERBOOK,
                risex_entry_quote=snapshot.risex_entry_quote,
                hedge_entry_quote=snapshot.hedge_entry_quote,
                risex_estimated_exit_quote=snapshot.risex_estimated_exit_quote,
                hedge_estimated_exit_quote=snapshot.hedge_estimated_exit_quote,
            ),
        ),
    }
    values.update(changes)
    return LiveGateEvidenceBundle(**values)


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


def test_evaluate_route_preserves_paper_eligible_behavior_for_matching_settlement_timestamps() -> None:
    route, snapshot = build_fake_route_and_snapshot()

    assert snapshot.risex_funding_settlement_at == snapshot.hedge_funding_settlement_at

    decision = evaluate_route(route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.entry_ev is not None
    assert decision.capture_plan is None


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


def test_evaluate_route_rejects_mismatched_funding_settlement_timestamps() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    mismatched_snapshot = replace(
        snapshot,
        hedge_funding_settlement_at=snapshot.risex_funding_settlement_at + timedelta(seconds=1),
    )

    decision = evaluate_route(route, mismatched_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)
    assert decision.entry_ev is None
    assert decision.capture_plan is None


def test_evaluate_route_rejects_large_route_when_quotes_only_partially_fill_target() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    large_route = replace(route, target_notional_usd=Decimal("10000"))
    partial_snapshot = replace(
        snapshot,
        risex_entry_quote=_forge_quote(
            snapshot.risex_entry_quote,
            target_notional_usd=Decimal("10000"),
            executable=True,
            notional_filled_usd=Decimal("500"),
            consumed_base_quantity=Decimal("5"),
        ),
        hedge_entry_quote=_forge_quote(
            snapshot.hedge_entry_quote,
            target_notional_usd=Decimal("10000"),
            executable=True,
            notional_filled_usd=Decimal("500"),
            consumed_base_quantity=Decimal("5"),
        ),
        risex_estimated_exit_quote=_forge_quote(
            snapshot.risex_estimated_exit_quote,
            target_notional_usd=Decimal("10000"),
            executable=True,
            notional_filled_usd=Decimal("500"),
            consumed_base_quantity=Decimal("5"),
        ),
        hedge_estimated_exit_quote=_forge_quote(
            snapshot.hedge_estimated_exit_quote,
            target_notional_usd=Decimal("10000"),
            executable=True,
            notional_filled_usd=Decimal("500"),
            consumed_base_quantity=Decimal("5"),
        ),
    )

    decision = evaluate_route(large_route, partial_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.status is not RouteStatus.PAPER_ELIGIBLE
    assert decision.reasons == (RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL,)
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
    bad_route = object.__new__(route.__class__)
    for field in fields(route):
        object.__setattr__(bad_route, field.name, getattr(route, field.name))
    object.__setattr__(bad_route, "hedge_entry_side", route.risex_entry_side)

    decision = evaluate_route(bad_route, snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.TECHNICALLY_NOT_EXECUTABLE,)


def test_route_candidate_rejects_invalid_entry_side_string() -> None:
    route, _ = build_fake_route_and_snapshot()

    with pytest.raises(ValueError, match="order side"):
        replace(route, risex_entry_side="hold")


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
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LEDGER_NOT_RECONCILED,)


def test_evaluate_route_uses_live_gate_evidence_bundle_without_returning_live_eligible() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(route, snapshot)

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_GATES_NOT_IMPLEMENTED,)


def test_evaluate_route_live_gate_evidence_bundle_does_not_bypass_live_disabled() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(route, snapshot)

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=False),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.LIVE_TRADING_DISABLED,)


def test_evaluate_route_live_gate_evidence_bundle_requires_verified_funding_settlement() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    bundle = _live_gate_evidence_bundle(
        route,
        snapshot,
        funding_settlement_verified=False,
    )

    decision = evaluate_route(
        route,
        snapshot,
        EvaluationMode.ENTRY,
        rules=ProductRules(live_trading_enabled=True),
        live_gate_evidence_bundle=bundle,
    )

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.status is not RouteStatus.LIVE_ELIGIBLE
    assert decision.capture_plan is None
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)


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


def test_poor_prices_for_fully_filled_large_target_affect_pnl_without_liquidity_rejection() -> None:
    route, snapshot = build_fake_route_and_snapshot()
    large_route = replace(route, target_notional_usd=Decimal("10000"))
    risex_book = OrderBook(
        venue="RiseX",
        symbol="BTC-PERP",
        bids=(OrderBookLevel(price=Decimal("80"), size=Decimal("200")),),
        asks=(
            OrderBookLevel(price=Decimal("100"), size=Decimal("50")),
            OrderBookLevel(price=Decimal("120"), size=Decimal("100")),
        ),
    )
    hedge_book = OrderBook(
        venue="Hyperliquid",
        symbol="BTC",
        bids=(OrderBookLevel(price=Decimal("100"), size=Decimal("200")),),
        asks=(OrderBookLevel(price=Decimal("130"), size=Decimal("200")),),
    )
    large_snapshot = replace(
        snapshot,
        risex_entry_quote=calculate_executable_quote(
            order_book=risex_book,
            side=large_route.risex_entry_side,
            target_notional_usd=large_route.target_notional_usd,
        ),
        hedge_entry_quote=calculate_executable_quote(
            order_book=hedge_book,
            side=large_route.hedge_entry_side,
            target_notional_usd=large_route.target_notional_usd,
        ),
        risex_estimated_exit_quote=calculate_executable_quote(
            order_book=risex_book,
            side="sell",
            target_notional_usd=large_route.target_notional_usd,
        ),
        hedge_estimated_exit_quote=calculate_executable_quote(
            order_book=hedge_book,
            side="buy",
            target_notional_usd=large_route.target_notional_usd,
        ),
        funding=FundingSnapshot(
            risex_funding_usd=EstimatedValue(value=Decimal("6000"), source=ValueSource.OBSERVED),
            hedge_funding_usd=EstimatedValue(value=Decimal("0"), source=ValueSource.OBSERVED),
        ),
    )

    decision = evaluate_route(large_route, large_snapshot, EvaluationMode.ENTRY)

    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.entry_ev is not None
    assert decision.entry_ev.simulated_roundtrip_cost_usd > Decimal("0")
    assert all(quote.notional_filled_usd == large_route.target_notional_usd for quote in large_snapshot.executable_quotes())
    assert RejectReason.ORDERBOOK_NOT_EXECUTABLE_FOR_MIN_NOTIONAL not in decision.reasons
    assert RejectReason.TECHNICALLY_NOT_EXECUTABLE not in decision.reasons


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
