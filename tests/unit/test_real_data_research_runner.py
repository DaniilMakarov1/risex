from __future__ import annotations

import importlib
import inspect
import sys
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import apps.research_runner.real_data as real_data
from core.config.product_rules import ProductRules
from core.domain.contracts import (
    DecisionResult,
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    RouteCandidate,
    VenueObservation,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from core.pipeline.snapshot import assemble_route_snapshot


RISEX_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
HEDGE_OBSERVED_AT = datetime(2026, 1, 1, 12, 0, 1, tzinfo=UTC)
SETTLEMENT_AT = datetime(2026, 1, 1, 16, 0, tzinfo=UTC)
ASSEMBLED_AT = datetime(2026, 1, 1, 12, 0, 5, tzinfo=UTC)


class RecordingObservationAdapter:
    name = "recording"

    def __init__(self, observation: VenueObservation) -> None:
        self.observation = observation
        self.requested_symbols: list[str] = []

    def fetch_observation(self, symbol: str) -> VenueObservation:
        self.requested_symbols.append(symbol)
        return self.observation


class FailingObservationAdapter:
    name = "failing"

    def __init__(self) -> None:
        self.requested_symbols: list[str] = []

    def fetch_observation(self, symbol: str) -> VenueObservation:
        self.requested_symbols.append(symbol)
        raise ValueError("adapter observation unavailable")


def _route() -> RouteCandidate:
    return RouteCandidate(
        route_id="real-data-route-001",
        capture_id="capture-001",
        risex_venue="RiseX",
        risex_symbol="BTC-PERP",
        risex_entry_side="buy",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        hedge_entry_side="sell",
        target_notional_usd=Decimal("500"),
    )


def _book(
    *,
    venue: str,
    symbol: str,
    bid_price: str = "99.95",
    ask_price: str = "100",
    size: str = "10",
) -> OrderBook:
    return OrderBook(
        venue=venue,
        symbol=symbol,
        bids=(OrderBookLevel(price=Decimal(bid_price), size=Decimal(size)),),
        asks=(OrderBookLevel(price=Decimal(ask_price), size=Decimal(size)),),
    )


def _fees(name: str, amount: str = "0.25") -> FeeModel:
    return FeeModel(
        components=(
            FeeComponent(
                name=name,
                amount_usd=EstimatedValue(
                    value=Decimal(amount),
                    source=ValueSource.DOCUMENTED,
                ),
            ),
        )
    )


def _observation(
    *,
    venue: str,
    symbol: str,
    observed_at: datetime,
    funding: str,
    fees: FeeModel,
    order_book: OrderBook | None = None,
) -> VenueObservation:
    return VenueObservation(
        venue=venue,
        symbol=symbol,
        observed_at=observed_at,
        order_book=order_book or _book(venue=venue, symbol=symbol),
        expected_funding_usd=EstimatedValue(
            value=Decimal(funding),
            source=ValueSource.OBSERVED,
        ),
        funding_settlement_at=SETTLEMENT_AT,
        fees=fees,
    )


def _observations() -> tuple[VenueObservation, VenueObservation]:
    return (
        _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=RISEX_OBSERVED_AT,
            funding="3",
            fees=_fees("risex_fees"),
        ),
        _observation(
            venue="Hyperliquid",
            symbol="BTC",
            observed_at=HEDGE_OBSERVED_AT,
            funding="-0.5",
            fees=_fees("hedge_fees"),
        ),
    )


def test_real_data_runner_evaluates_one_explicit_route_from_adapter_observations() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    risex_adapter = RecordingObservationAdapter(risex_observation)
    hedge_adapter = RecordingObservationAdapter(hedge_observation)

    decision = real_data.run_real_data_research_route(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=hedge_adapter,
        assembled_at=ASSEMBLED_AT,
        mode=EvaluationMode.ENTRY,
    )

    assert risex_adapter.requested_symbols == [route.risex_symbol]
    assert hedge_adapter.requested_symbols == [route.hedge_symbol]
    assert decision.route_id == route.route_id
    assert decision.mode is EvaluationMode.ENTRY
    assert decision.status is RouteStatus.PAPER_ELIGIBLE
    assert decision.capture_plan is None


def test_real_data_runner_uses_adapter_handoff_and_shared_decision_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    snapshot = assemble_route_snapshot(
        route=route,
        observations={
            (route.risex_venue, route.risex_symbol): risex_observation,
            (route.hedge_venue, route.hedge_symbol): hedge_observation,
        },
        assembled_at=ASSEMBLED_AT,
    )
    expected_rules = ProductRules()
    captured: dict[str, object] = {}

    def fake_handoff(*, route, risex_adapter, hedge_adapter, assembled_at):
        captured["handoff"] = (route, risex_adapter, hedge_adapter, assembled_at)
        return snapshot

    def fake_evaluate(route, snapshot, mode, *, rules=None, **kwargs):
        captured["evaluate"] = (route, snapshot, mode, rules, kwargs)
        return DecisionResult(
            route_id=route.route_id,
            mode=mode,
            status=RouteStatus.RESEARCH_ONLY,
            reasons=(),
            capture_plan=None,
            decided_at=ASSEMBLED_AT,
        )

    risex_adapter = RecordingObservationAdapter(risex_observation)
    hedge_adapter = RecordingObservationAdapter(hedge_observation)
    monkeypatch.setattr(real_data, "assemble_route_snapshot_from_adapters", fake_handoff)
    monkeypatch.setattr(real_data, "evaluate_route", fake_evaluate)

    decision = real_data.run_real_data_research_route(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=hedge_adapter,
        assembled_at=ASSEMBLED_AT,
        mode=EvaluationMode.DISCOVERY,
        rules=expected_rules,
    )

    assert captured["handoff"] == (route, risex_adapter, hedge_adapter, ASSEMBLED_AT)
    assert captured["evaluate"] == (
        route,
        snapshot,
        EvaluationMode.DISCOVERY,
        expected_rules,
        {},
    )
    assert decision.status is RouteStatus.RESEARCH_ONLY


def test_real_data_runner_adapter_failure_fails_closed_before_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _route()
    _, hedge_observation = _observations()
    risex_adapter = FailingObservationAdapter()

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("evaluate_route must not run after adapter failure")

    monkeypatch.setattr(real_data, "evaluate_route", fail_if_evaluated)

    decision = real_data.run_real_data_research_route(
        route=route,
        risex_adapter=risex_adapter,
        hedge_adapter=RecordingObservationAdapter(hedge_observation),
        assembled_at=ASSEMBLED_AT,
        mode=EvaluationMode.ENTRY,
    )

    assert risex_adapter.requested_symbols == [route.risex_symbol]
    assert decision.route_id == route.route_id
    assert decision.mode is EvaluationMode.ENTRY
    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decision.net_profit_usd is None
    assert decision.entry_ev is None
    assert decision.capture_plan is None
    assert decision.decided_at == ASSEMBLED_AT


def test_real_data_runner_snapshot_handoff_failure_fails_closed_before_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _route()
    risex_observation, _ = _observations()
    wrong_hedge_observation = _observation(
        venue="Hyperliquid",
        symbol="ETH",
        observed_at=HEDGE_OBSERVED_AT,
        funding="-0.5",
        fees=_fees("wrong_hedge_fees"),
        order_book=_book(venue="Hyperliquid", symbol="ETH"),
    )

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("evaluate_route must not run after snapshot handoff failure")

    monkeypatch.setattr(real_data, "evaluate_route", fail_if_evaluated)

    decision = real_data.run_real_data_research_route(
        route=route,
        risex_adapter=RecordingObservationAdapter(risex_observation),
        hedge_adapter=RecordingObservationAdapter(wrong_hedge_observation),
        assembled_at=ASSEMBLED_AT,
        mode=EvaluationMode.ENTRY,
    )

    assert decision.status is RouteStatus.REJECTED
    assert decision.reasons == (RejectReason.REQUIRED_LIVE_DATA_MISSING,)
    assert decision.decided_at == ASSEMBLED_AT


def test_real_data_runner_rejects_naive_assembly_timestamp_before_adapter_calls() -> None:
    route = _route()
    risex_observation, hedge_observation = _observations()
    risex_adapter = RecordingObservationAdapter(risex_observation)
    hedge_adapter = RecordingObservationAdapter(hedge_observation)

    with pytest.raises(ValueError, match="assembled_at"):
        real_data.run_real_data_research_route(
            route=route,
            risex_adapter=risex_adapter,
            hedge_adapter=hedge_adapter,
            assembled_at=datetime(2026, 1, 1, 12, 0),
            mode=EvaluationMode.ENTRY,
        )

    assert risex_adapter.requested_symbols == []
    assert hedge_adapter.requested_symbols == []


def test_real_data_runner_has_no_ledger_parameter() -> None:
    signature = inspect.signature(real_data.run_real_data_research_route)

    assert "ledger" not in signature.parameters


def test_real_data_runner_does_not_import_paper_live_or_execution_modules() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "core.execution"
            or module_name.startswith("core.execution.")
            or module_name.startswith("apps.paper_runner")
            or module_name.startswith("apps.live_runner")
        ):
            del sys.modules[module_name]

    module = importlib.reload(importlib.import_module("apps.research_runner.real_data"))
    route = _route()
    risex_observation, hedge_observation = _observations()

    module.run_real_data_research_route(
        route=route,
        risex_adapter=RecordingObservationAdapter(risex_observation),
        hedge_adapter=RecordingObservationAdapter(hedge_observation),
        assembled_at=ASSEMBLED_AT,
        mode=EvaluationMode.ENTRY,
    )

    assert not any(
        module_name == "core.execution" or module_name.startswith("core.execution.")
        for module_name in sys.modules
    )
    assert not any(module_name.startswith("apps.paper_runner") for module_name in sys.modules)
    assert not any(module_name.startswith("apps.live_runner") for module_name in sys.modules)
