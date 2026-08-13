from __future__ import annotations

import inspect
import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

import apps.cli.main as cli
from core.accounting.ledger import LedgerEventType
from core.domain.contracts import (
    DecisionResult,
    EstimatedValue,
    FeeComponent,
    FeeModel,
    RouteCandidate,
)
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus, ValueSource
from storage.sqlite.ledger import SQLiteLedger


OMIT = object()

NO_ARG_OUTPUT = """Broad Scan
fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000
fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369
Focused Refresh
fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000
fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369
"""

BASE_ARGS = {
    "route_id": "cli-route-001",
    "capture_id": "cli-capture-001",
    "risex_venue": "RiseX",
    "risex_symbol": "BTC-PERP",
    "risex_side": "buy",
    "hedge_venue": "Hyperliquid",
    "hedge_symbol": "BTC",
    "hedge_side": "sell",
    "target_notional_usd": "500",
    "mode": "ENTRY",
    "assembled_at": "2026-08-13T12:00:00+00:00",
}

ARG_FLAGS = (
    ("route_id", "--route-id"),
    ("capture_id", "--capture-id"),
    ("risex_venue", "--risex-venue"),
    ("risex_symbol", "--risex-symbol"),
    ("risex_side", "--risex-side"),
    ("hedge_venue", "--hedge-venue"),
    ("hedge_symbol", "--hedge-symbol"),
    ("hedge_side", "--hedge-side"),
    ("target_notional_usd", "--target-notional-usd"),
    ("mode", "--mode"),
    ("assembled_at", "--assembled-at"),
)


def _real_data_args(**overrides: object) -> list[str]:
    values = dict(BASE_ARGS)
    values.update(overrides)

    args = ["real-data-route"]
    for key, flag in ARG_FLAGS:
        value = values[key]
        if value is OMIT:
            continue
        args.extend([flag, str(value)])
    return args


def _real_data_report_args(**overrides: object) -> list[str]:
    return [*_real_data_args(**overrides), "--public-readiness-report"]


def _real_data_report_json_args(**overrides: object) -> list[str]:
    return [
        *_real_data_report_args(**overrides),
        "--public-readiness-report-format",
        "json",
    ]


def _paper_trade_args(**overrides: object) -> list[str]:
    values = dict(BASE_ARGS)
    ledger_sqlite_path = overrides.pop("ledger_sqlite_path", OMIT)
    values.update(overrides)

    args = ["paper-trade-route"]
    for key, flag in ARG_FLAGS:
        value = values[key]
        if value is OMIT:
            continue
        args.extend([flag, str(value)])
    if ledger_sqlite_path is not OMIT:
        args.extend(["--ledger-sqlite-path", str(ledger_sqlite_path)])
    return args


def _paper_session_route(**overrides: object) -> dict[str, str]:
    values = dict(BASE_ARGS)
    values.update(overrides)
    return {
        "route_id": str(values["route_id"]),
        "capture_id": str(values["capture_id"]),
        "risex_venue": str(values["risex_venue"]),
        "risex_symbol": str(values["risex_symbol"]),
        "risex_side": str(values["risex_side"]),
        "hedge_venue": str(values["hedge_venue"]),
        "hedge_symbol": str(values["hedge_symbol"]),
        "hedge_side": str(values["hedge_side"]),
        "target_notional_usd": str(values["target_notional_usd"]),
        "mode": str(values["mode"]),
        "assembled_at": str(values["assembled_at"]),
    }


def _paper_session_args(
    tmp_path,
    routes_payload: object,
    *,
    ledger_sqlite_path: object = OMIT,
    session_report_json_path: object = OMIT,
) -> list[str]:
    routes_path = tmp_path / "paper-session-routes.json"
    routes_path.write_text(json.dumps(routes_payload), encoding="utf-8")
    args = ["paper-trade-session", "--routes-json-path", str(routes_path)]
    if ledger_sqlite_path is not OMIT:
        args.extend(["--ledger-sqlite-path", str(ledger_sqlite_path)])
    if session_report_json_path is not OMIT:
        args.extend(["--session-report-json-path", str(session_report_json_path)])
    return args


def test_no_arg_cli_fake_scan_refresh_output_remains_unchanged(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([]) == 0

    assert capsys.readouterr().out == NO_ARG_OUTPUT


def test_real_data_cli_constructs_one_route_and_delegates_once(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed_risex_adapters: list[object] = []
    constructed_hedge_adapters: list[object] = []
    runner_calls: list[dict[str, object]] = []

    class RecordingRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_risex_adapters.append(self)

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_hedge_adapters.append(self)

    def fake_runner(**kwargs: object) -> DecisionResult:
        runner_calls.append(kwargs)
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return DecisionResult(
            route_id=route.route_id,
            mode=kwargs["mode"],
            status=RouteStatus.PAPER_ELIGIBLE,
            reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
            net_profit_usd=Decimal("4.5"),
            entry_ev=SimpleNamespace(
                expected_funding_usd=Decimal("7"),
                total_fees_usd=Decimal("1"),
                simulated_roundtrip_cost_usd=Decimal("1.5"),
            ),
            capture_plan=None,
            decided_at=kwargs["assembled_at"],
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", fake_runner)

    assert cli.main(_real_data_args()) == 0

    assert len(constructed_risex_adapters) == 1
    assert len(constructed_hedge_adapters) == 1
    assert len(runner_calls) == 1
    call = runner_calls[0]
    assert call["risex_adapter"] is constructed_risex_adapters[0]
    assert call["hedge_adapter"] is constructed_hedge_adapters[0]
    assert call["assembled_at"] == datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    assert call["mode"] is EvaluationMode.ENTRY
    assert call["route"] == RouteCandidate(
        route_id="cli-route-001",
        capture_id="cli-capture-001",
        risex_venue="RiseX",
        risex_symbol="BTC-PERP",
        risex_entry_side="buy",
        hedge_venue="Hyperliquid",
        hedge_symbol="BTC",
        hedge_entry_side="sell",
        target_notional_usd=Decimal("500"),
    )
    assert capsys.readouterr().out == (
        "Real Data Route\n"
        "route_id=cli-route-001\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_GATES_NOT_IMPLEMENTED\n"
        "net_profit_usd=4.5\n"
        "expected_funding_usd=7\n"
        "total_fees_usd=1\n"
        "simulated_roundtrip_cost_usd=1.5\n"
    )


def test_real_data_cli_public_readiness_report_outputs_public_evidence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed_risex_adapters: list[object] = []
    constructed_hedge_adapters: list[object] = []
    report_calls: list[dict[str, object]] = []

    class RecordingRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_risex_adapters.append(self)

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_hedge_adapters.append(self)

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        raise AssertionError("default runner must not be called for report output")

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        report_calls.append(kwargs)
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        snapshot = SimpleNamespace(
            captured_at=kwargs["assembled_at"],
            risex_observed_at=datetime(2026, 8, 13, 12, 0, 1, tzinfo=UTC),
            hedge_observed_at=datetime(2026, 8, 13, 12, 0, 2, tzinfo=UTC),
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            hedge_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            funding=SimpleNamespace(
                risex_funding_usd=EstimatedValue(
                    value=Decimal("-0.500"),
                    source=ValueSource.OBSERVED,
                    description="completed public RiseX funding",
                    metadata={
                        "public_funding_rate": "0.001",
                        "public_funding_rate_source": "OBSERVED",
                        "entry_side": "buy",
                        "target_notional_usd": "500",
                    },
                ),
                hedge_funding_usd=EstimatedValue(
                    value=Decimal("0.2000"),
                    source=ValueSource.OBSERVED,
                    description="completed public hedge funding",
                    metadata={
                        "public_funding_rate": "0.0004",
                        "public_funding_rate_source": "OBSERVED",
                        "entry_side": "sell",
                        "target_notional_usd": "500",
                    },
                ),
            ),
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="risex_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=Decimal("0.35000"),
                            source=ValueSource.OBSERVED,
                            description="completed public RiseX fees",
                            metadata={
                                "public_fee_metadata_source": "OBSERVED",
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "target_notional_usd": "500",
                            },
                        ),
                    ),
                    FeeComponent(
                        name="hyperliquid_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=Decimal("0.45000"),
                            source=ValueSource.OBSERVED,
                            description="completed public hedge fees",
                            metadata={
                                "public_fee_metadata_source": "OBSERVED",
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "target_notional_usd": "500",
                            },
                        ),
                    ),
                )
            ),
        )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=kwargs["mode"],
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(RejectReason.LIVE_TRADING_DISABLED,),
                net_profit_usd=Decimal("4.2"),
                entry_ev=SimpleNamespace(
                    expected_funding_usd=Decimal("-0.3000"),
                    total_fees_usd=Decimal("0.80000"),
                    simulated_roundtrip_cost_usd=Decimal("1.1"),
                    net_profit_usd=Decimal("4.2"),
                ),
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_real_data_report_args()) == 0

    assert len(constructed_risex_adapters) == 1
    assert len(constructed_hedge_adapters) == 1
    assert len(report_calls) == 1
    assert capsys.readouterr().out == (
        "Public Readiness Report\n"
        "route_id=cli-route-001\n"
        "capture_id=cli-capture-001\n"
        "risex_venue=RiseX\n"
        "risex_symbol=BTC-PERP\n"
        "risex_side=buy\n"
        "hedge_venue=Hyperliquid\n"
        "hedge_symbol=BTC\n"
        "hedge_side=sell\n"
        "target_notional_usd=500\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_TRADING_DISABLED\n"
        "net_profit_usd=4.2\n"
        "expected_funding_usd=-0.3000\n"
        "total_fees_usd=0.80000\n"
        "simulated_roundtrip_cost_usd=1.1\n"
        "entry_ev_net_profit_usd=4.2\n"
        "snapshot=AVAILABLE\n"
        "snapshot.captured_at=2026-08-13T12:00:00+00:00\n"
        "snapshot.risex_observed_at=2026-08-13T12:00:01+00:00\n"
        "snapshot.hedge_observed_at=2026-08-13T12:00:02+00:00\n"
        "snapshot.risex_funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "snapshot.hedge_funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "funding.risex.value_usd=-0.500\n"
        "funding.risex.source=OBSERVED\n"
        "funding.risex.description=completed public RiseX funding\n"
        "funding.risex.metadata=entry_side=buy;"
        "public_funding_rate=0.001;"
        "public_funding_rate_source=OBSERVED;"
        "target_notional_usd=500\n"
        "funding.hedge.value_usd=0.2000\n"
        "funding.hedge.source=OBSERVED\n"
        "funding.hedge.description=completed public hedge funding\n"
        "funding.hedge.metadata=entry_side=sell;"
        "public_funding_rate=0.0004;"
        "public_funding_rate_source=OBSERVED;"
        "target_notional_usd=500\n"
        "fee.count=2\n"
        "fee.1.name=risex_fee_cash_flow_unknown\n"
        "fee.1.is_default=False\n"
        "fee.1.value_usd=0.35000\n"
        "fee.1.source=OBSERVED\n"
        "fee.1.description=completed public RiseX fees\n"
        "fee.1.metadata=public_fee_completed_fills=entry+estimated_exit;"
        "public_fee_metadata_source=OBSERVED;"
        "target_notional_usd=500\n"
        "fee.2.name=hyperliquid_fee_cash_flow_unknown\n"
        "fee.2.is_default=False\n"
        "fee.2.value_usd=0.45000\n"
        "fee.2.source=OBSERVED\n"
        "fee.2.description=completed public hedge fees\n"
        "fee.2.metadata=public_fee_completed_fills=entry+estimated_exit;"
        "public_fee_metadata_source=OBSERVED;"
        "target_notional_usd=500\n"
        "unknown_components=None\n"
        "public_readiness=READY_FOR_LATER_FAIL_CLOSED_STAGES\n"
        "public_readiness_reasons=public evidence complete for one ENTRY route; "
        "live/order/private/account stages remain outside this report\n"
        "later_fail_closed_blockers=LIVE_TRADING_DISABLED\n"
    )


def test_real_data_cli_public_readiness_report_json_outputs_public_evidence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed_risex_adapters: list[object] = []
    constructed_hedge_adapters: list[object] = []
    report_calls: list[dict[str, object]] = []

    class RecordingRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_risex_adapters.append(self)

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_hedge_adapters.append(self)

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        raise AssertionError("default runner must not be called for JSON report")

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        report_calls.append(kwargs)
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        snapshot = SimpleNamespace(
            captured_at=kwargs["assembled_at"],
            risex_observed_at=datetime(2026, 8, 13, 12, 0, 1, tzinfo=UTC),
            hedge_observed_at=datetime(2026, 8, 13, 12, 0, 2, tzinfo=UTC),
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            hedge_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            funding=SimpleNamespace(
                risex_funding_usd=EstimatedValue(
                    value=Decimal("-0.500"),
                    source=ValueSource.OBSERVED,
                    description="completed public RiseX funding",
                    metadata={
                        "public_funding_rate": "0.001",
                        "public_funding_rate_source": "OBSERVED",
                        "entry_side": "buy",
                        "target_notional_usd": "500",
                    },
                ),
                hedge_funding_usd=EstimatedValue(
                    value=Decimal("0.2000"),
                    source=ValueSource.OBSERVED,
                    description="completed public hedge funding",
                    metadata={
                        "public_funding_rate": "0.0004",
                        "public_funding_rate_source": "OBSERVED",
                        "entry_side": "sell",
                        "target_notional_usd": "500",
                    },
                ),
            ),
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="risex_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=Decimal("0.35000"),
                            source=ValueSource.OBSERVED,
                            description="completed public RiseX fees",
                            metadata={
                                "public_fee_metadata_source": "OBSERVED",
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "target_notional_usd": "500",
                            },
                        ),
                    ),
                    FeeComponent(
                        name="hyperliquid_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=Decimal("0.45000"),
                            source=ValueSource.OBSERVED,
                            description="completed public hedge fees",
                            metadata={
                                "public_fee_metadata_source": "OBSERVED",
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "target_notional_usd": "500",
                            },
                        ),
                    ),
                )
            ),
        )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=kwargs["mode"],
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(RejectReason.LIVE_TRADING_DISABLED,),
                net_profit_usd=Decimal("4.2"),
                entry_ev=SimpleNamespace(
                    expected_funding_usd=Decimal("-0.3000"),
                    total_fees_usd=Decimal("0.80000"),
                    simulated_roundtrip_cost_usd=Decimal("1.1"),
                    net_profit_usd=Decimal("4.2"),
                ),
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_real_data_report_json_args()) == 0

    assert len(constructed_risex_adapters) == 1
    assert len(constructed_hedge_adapters) == 1
    assert len(report_calls) == 1
    assert json.loads(capsys.readouterr().out) == {
        "report": "Public Readiness Report",
        "route": {
            "route_id": "cli-route-001",
            "capture_id": "cli-capture-001",
            "risex_venue": "RiseX",
            "risex_symbol": "BTC-PERP",
            "risex_side": "buy",
            "hedge_venue": "Hyperliquid",
            "hedge_symbol": "BTC",
            "hedge_side": "sell",
            "target_notional_usd": "500",
        },
        "decision": {
            "mode": "ENTRY",
            "status": "PAPER_ELIGIBLE",
            "reasons": ["LIVE_TRADING_DISABLED"],
            "net_profit_usd": "4.2",
            "entry_ev": {
                "expected_funding_usd": "-0.3000",
                "total_fees_usd": "0.80000",
                "simulated_roundtrip_cost_usd": "1.1",
                "net_profit_usd": "4.2",
            },
        },
        "snapshot": {
            "state": "AVAILABLE",
            "captured_at": "2026-08-13T12:00:00+00:00",
            "risex_observed_at": "2026-08-13T12:00:01+00:00",
            "hedge_observed_at": "2026-08-13T12:00:02+00:00",
            "risex_funding_settlement_at": "2026-08-13T16:00:00+00:00",
            "hedge_funding_settlement_at": "2026-08-13T16:00:00+00:00",
            "funding": {
                "risex": {
                    "value_usd": "-0.500",
                    "source": "OBSERVED",
                    "description": "completed public RiseX funding",
                    "metadata": {
                        "entry_side": "buy",
                        "public_funding_rate": "0.001",
                        "public_funding_rate_source": "OBSERVED",
                        "target_notional_usd": "500",
                    },
                },
                "hedge": {
                    "value_usd": "0.2000",
                    "source": "OBSERVED",
                    "description": "completed public hedge funding",
                    "metadata": {
                        "entry_side": "sell",
                        "public_funding_rate": "0.0004",
                        "public_funding_rate_source": "OBSERVED",
                        "target_notional_usd": "500",
                    },
                },
            },
            "fees": {
                "count": 2,
                "components": [
                    {
                        "name": "risex_fee_cash_flow_unknown",
                        "is_default": False,
                        "amount_usd": {
                            "value_usd": "0.35000",
                            "source": "OBSERVED",
                            "description": "completed public RiseX fees",
                            "metadata": {
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "public_fee_metadata_source": "OBSERVED",
                                "target_notional_usd": "500",
                            },
                        },
                    },
                    {
                        "name": "hyperliquid_fee_cash_flow_unknown",
                        "is_default": False,
                        "amount_usd": {
                            "value_usd": "0.45000",
                            "source": "OBSERVED",
                            "description": "completed public hedge fees",
                            "metadata": {
                                "public_fee_completed_fills": "entry+estimated_exit",
                                "public_fee_metadata_source": "OBSERVED",
                                "target_notional_usd": "500",
                            },
                        },
                    },
                ],
            },
        },
        "unknown_components": [],
        "public_readiness": {
            "status": "READY_FOR_LATER_FAIL_CLOSED_STAGES",
            "reasons": [
                "public evidence complete for one ENTRY route; "
                "live/order/private/account stages remain outside this report"
            ],
            "display_only": True,
        },
        "later_fail_closed_blockers": ["LIVE_TRADING_DISABLED"],
    }


def test_real_data_cli_preserves_missing_economics_as_none(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_runner(**kwargs: object) -> DecisionResult:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return DecisionResult(
            route_id=route.route_id,
            mode=kwargs["mode"],
            status=RouteStatus.REJECTED,
            reasons=(),
            net_profit_usd=None,
            entry_ev=None,
            capture_plan=None,
            decided_at=kwargs["assembled_at"],
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", fake_runner)

    assert cli.main(_real_data_args(mode="DISCOVERY")) == 0

    output = capsys.readouterr().out
    assert "reasons=None\n" in output
    assert "net_profit_usd=None\n" in output
    assert "expected_funding_usd=None\n" in output
    assert "total_fees_usd=None\n" in output
    assert "simulated_roundtrip_cost_usd=None\n" in output
    assert "net_profit_usd=0" not in output


def test_real_data_cli_public_readiness_report_preserves_unknown_evidence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        snapshot = SimpleNamespace(
            captured_at=kwargs["assembled_at"],
            risex_observed_at=datetime(2026, 8, 13, 12, 0, 1, tzinfo=UTC),
            hedge_observed_at=datetime(2026, 8, 13, 12, 0, 2, tzinfo=UTC),
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            hedge_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            funding=SimpleNamespace(
                risex_funding_usd=EstimatedValue(
                    value=None,
                    source=ValueSource.UNKNOWN,
                    metadata={"public_funding_rate": "not-a-rate"},
                ),
                hedge_funding_usd=EstimatedValue(
                    value=Decimal("0.2000"),
                    source=ValueSource.OBSERVED,
                ),
            ),
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="risex_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=None,
                            source=ValueSource.UNKNOWN,
                            metadata={
                                "public_fee_maker_bps": "1.25",
                                "public_fee_metadata_source": "OBSERVED",
                            },
                        ),
                    ),
                )
            ),
        )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=kwargs["mode"],
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_real_data_report_args()) == 0

    output = capsys.readouterr().out
    assert "funding.risex.value_usd=None\n" in output
    assert "funding.risex.source=UNKNOWN\n" in output
    assert "fee.1.value_usd=None\n" in output
    assert "fee.1.source=UNKNOWN\n" in output
    assert "expected_funding_usd=None\n" in output
    assert "total_fees_usd=None\n" in output
    assert (
        "unknown_components=funding.risex,fee.1.risex_fee_cash_flow_unknown\n"
        in output
    )
    assert "public_readiness=NOT_READY\n" in output
    assert (
        "public_readiness_reasons=decision status is REJECTED; "
        "Entry EV fields are unavailable; UNKNOWN evidence remains: "
        "funding.risex,fee.1.risex_fee_cash_flow_unknown\n"
        in output
    )
    assert "funding.risex.value_usd=0" not in output
    assert "fee.1.value_usd=0" not in output


def test_real_data_cli_public_readiness_json_preserves_unknown_evidence_as_null(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        snapshot = SimpleNamespace(
            captured_at=kwargs["assembled_at"],
            risex_observed_at=datetime(2026, 8, 13, 12, 0, 1, tzinfo=UTC),
            hedge_observed_at=datetime(2026, 8, 13, 12, 0, 2, tzinfo=UTC),
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            hedge_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
            funding=SimpleNamespace(
                risex_funding_usd=EstimatedValue(
                    value=None,
                    source=ValueSource.UNKNOWN,
                    metadata={"public_funding_rate": "not-a-rate"},
                ),
                hedge_funding_usd=EstimatedValue(
                    value=Decimal("0.2000"),
                    source=ValueSource.OBSERVED,
                ),
            ),
            fees=FeeModel(
                components=(
                    FeeComponent(
                        name="risex_fee_cash_flow_unknown",
                        amount_usd=EstimatedValue(
                            value=None,
                            source=ValueSource.UNKNOWN,
                            metadata={
                                "public_fee_maker_bps": "1.25",
                                "public_fee_metadata_source": "OBSERVED",
                            },
                        ),
                    ),
                )
            ),
        )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=kwargs["mode"],
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_real_data_report_json_args()) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"]["net_profit_usd"] is None
    assert payload["decision"]["entry_ev"] == {
        "expected_funding_usd": None,
        "total_fees_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "net_profit_usd": None,
    }
    assert payload["snapshot"]["funding"]["risex"] == {
        "value_usd": None,
        "source": "UNKNOWN",
        "description": None,
        "metadata": {"public_funding_rate": "not-a-rate"},
    }
    assert payload["snapshot"]["fees"]["components"][0]["amount_usd"] == {
        "value_usd": None,
        "source": "UNKNOWN",
        "description": None,
        "metadata": {
            "public_fee_maker_bps": "1.25",
            "public_fee_metadata_source": "OBSERVED",
        },
    }
    assert payload["unknown_components"] == [
        "funding.risex",
        "fee.1.risex_fee_cash_flow_unknown",
    ]
    assert payload["public_readiness"]["status"] == "NOT_READY"
    assert payload["public_readiness"]["reasons"] == [
        "decision status is REJECTED",
        "Entry EV fields are unavailable",
        "UNKNOWN evidence remains: funding.risex,fee.1.risex_fee_cash_flow_unknown",
    ]
    assert "0" not in json.dumps(payload["decision"]["entry_ev"])


def test_real_data_cli_public_readiness_report_handles_missing_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, None]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=kwargs["mode"],
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            None,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_real_data_report_args()) == 0

    output = capsys.readouterr().out
    assert "snapshot=UNKNOWN\n" in output
    assert "unknown_components=snapshot\n" in output
    assert "public_readiness=NOT_READY\n" in output
    assert (
        "public_readiness_reasons=public snapshot evidence unavailable; "
        "decision status is REJECTED; Entry EV fields are unavailable; "
        "UNKNOWN evidence remains: snapshot\n"
        in output
    )


def test_paper_trade_cli_runs_entry_decision_through_fake_paper_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed_risex_adapters: list[object] = []
    constructed_hedge_adapters: list[object] = []
    runner_calls: list[dict[str, object]] = []

    class RecordingRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_risex_adapters.append(self)

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_hedge_adapters.append(self)

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        runner_calls.append(kwargs)
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        assert kwargs["mode"] is EvaluationMode.ENTRY
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
                net_profit_usd=Decimal("4.5"),
                entry_ev=SimpleNamespace(
                    expected_funding_usd=Decimal("7"),
                    total_fees_usd=Decimal("1"),
                    simulated_roundtrip_cost_usd=Decimal("1.5"),
                    net_profit_usd=Decimal("4.5"),
                ),
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            SimpleNamespace(
                risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
            ),
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_paper_trade_args()) == 0

    assert len(constructed_risex_adapters) == 1
    assert len(constructed_hedge_adapters) == 1
    assert len(runner_calls) == 1
    assert capsys.readouterr().out == (
        "Paper Trade Route\n"
        "route_id=cli-route-001\n"
        "capture_id=cli-capture-001\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_GATES_NOT_IMPLEMENTED\n"
        "decision.net_profit_usd=4.5\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=True\n"
        "paper_start_attribution=entry_paper_eligible_decision\n"
        "paper_start_blockers=None\n"
        "ledger_event_count=4\n"
        "ledger_event_sequences=1,2,3,4\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed\n"
        "paper.expected_funding_usd=7\n"
        "paper.total_fees_usd=1\n"
        "paper.simulated_roundtrip_cost_usd=1.5\n"
        "paper.net_profit_usd=4.5\n"
        "ledger_path=None\n"
    )


def test_paper_trade_cli_records_non_started_rejection_and_preserves_unknown_pnl(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            SimpleNamespace(
                risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
            ),
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_paper_trade_args()) == 0

    output = capsys.readouterr().out
    assert "paper_started=False\n" in output
    assert "paper_start_blockers=decision_status_not_paper_eligible\n" in output
    assert "ledger_event_count=2\n" in output
    assert "ledger_event_types=route_decision,paper_rejection_recorded\n" in output
    assert "decision.net_profit_usd=None\n" in output
    assert "paper.expected_funding_usd=None\n" in output
    assert "paper.total_fees_usd=None\n" in output
    assert "paper.simulated_roundtrip_cost_usd=None\n" in output
    assert "paper.net_profit_usd=None\n" in output
    assert "paper.net_profit_usd=0" not in output


def test_paper_trade_cli_handles_missing_snapshot_without_paper_ledger_events(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, None]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            None,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_paper_trade_args()) == 0

    output = capsys.readouterr().out
    assert "snapshot=UNKNOWN\n" in output
    assert "funding_settlement_at=None\n" in output
    assert "paper_started=False\n" in output
    assert "paper_start_attribution=None\n" in output
    assert "paper_start_blockers=public_snapshot_unavailable\n" in output
    assert "ledger_event_count=0\n" in output
    assert "ledger_event_sequences=None\n" in output
    assert "ledger_event_types=None\n" in output
    assert "paper.expected_funding_usd=None\n" in output
    assert "paper.net_profit_usd=None\n" in output


def test_paper_trade_cli_can_use_explicit_sqlite_ledger_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
                net_profit_usd=Decimal("4.5"),
                entry_ev=SimpleNamespace(
                    expected_funding_usd=Decimal("7"),
                    total_fees_usd=Decimal("1"),
                    simulated_roundtrip_cost_usd=Decimal("1.5"),
                    net_profit_usd=Decimal("4.5"),
                ),
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            SimpleNamespace(
                risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
            ),
        )

    db_path = tmp_path / "paper-ledger.sqlite"
    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_paper_trade_args(ledger_sqlite_path=db_path)) == 0

    output = capsys.readouterr().out
    assert f"ledger_path={db_path}\n" in output
    assert "ledger_event_count=4\n" in output

    reopened = SQLiteLedger(db_path)
    try:
        assert [event.event_type for event in reopened.records()] == [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        ]
    finally:
        reopened.close()


def test_paper_trade_session_runs_finite_routes_serially_with_deterministic_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    constructed_risex_adapters: list[object] = []
    constructed_hedge_adapters: list[object] = []
    runner_calls: list[dict[str, object]] = []

    class RecordingRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_risex_adapters.append(self)

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_hedge_adapters.append(self)

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        runner_calls.append(kwargs)
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        assert kwargs["mode"] is EvaluationMode.ENTRY
        snapshot = SimpleNamespace(
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
        )
        if route.route_id == "session-started":
            return (
                DecisionResult(
                    route_id=route.route_id,
                    mode=EvaluationMode.ENTRY,
                    status=RouteStatus.PAPER_ELIGIBLE,
                    reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
                    net_profit_usd=Decimal("4.5"),
                    entry_ev=SimpleNamespace(
                        expected_funding_usd=Decimal("7"),
                        total_fees_usd=Decimal("1"),
                        simulated_roundtrip_cost_usd=Decimal("1.5"),
                        net_profit_usd=Decimal("4.5"),
                    ),
                    capture_plan=None,
                    decided_at=kwargs["assembled_at"],
                ),
                snapshot,
            )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    routes_payload = [
        _paper_session_route(route_id="session-started", capture_id="capture-started"),
        _paper_session_route(
            route_id="session-rejected",
            capture_id="capture-rejected",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]
    assert cli.main(_paper_session_args(tmp_path, routes_payload)) == 0
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "paper-session-routes.json"
    ]

    assert len(constructed_risex_adapters) == 2
    assert len(constructed_hedge_adapters) == 2
    assert [call["route"].route_id for call in runner_calls] == [
        "session-started",
        "session-rejected",
    ]
    assert capsys.readouterr().out == (
        "Paper Trade Session\n"
        "route_count=2\n"
        "ledger_path=None\n"
        "session_route_index=1\n"
        "Paper Trade Route\n"
        "route_id=session-started\n"
        "capture_id=capture-started\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_GATES_NOT_IMPLEMENTED\n"
        "decision.net_profit_usd=4.5\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=True\n"
        "paper_start_attribution=entry_paper_eligible_decision\n"
        "paper_start_blockers=None\n"
        "ledger_event_count=4\n"
        "ledger_event_sequences=1,2,3,4\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed\n"
        "paper.expected_funding_usd=7\n"
        "paper.total_fees_usd=1\n"
        "paper.simulated_roundtrip_cost_usd=1.5\n"
        "paper.net_profit_usd=4.5\n"
        "ledger_path=None\n"
        "session_route_index=2\n"
        "Paper Trade Route\n"
        "route_id=session-rejected\n"
        "capture_id=capture-rejected\n"
        "mode=ENTRY\n"
        "status=REJECTED\n"
        "reasons=REQUIRED_LIVE_DATA_MISSING\n"
        "decision.net_profit_usd=None\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=False\n"
        "paper_start_attribution=paper_start_blocked_by_decision\n"
        "paper_start_blockers=decision_status_not_paper_eligible\n"
        "ledger_event_count=2\n"
        "ledger_event_sequences=5,6\n"
        "ledger_event_types=route_decision,paper_rejection_recorded\n"
        "paper.expected_funding_usd=None\n"
        "paper.total_fees_usd=None\n"
        "paper.simulated_roundtrip_cost_usd=None\n"
        "paper.net_profit_usd=None\n"
        "ledger_path=None\n"
        "Paper Trade Session Summary\n"
        "routes_total=2\n"
        "routes_with_snapshot=2\n"
        "routes_without_snapshot=0\n"
        "paper_started=1\n"
        "paper_not_started=1\n"
        "decision_status.RESEARCH_ONLY=0\n"
        "decision_status.PAPER_ELIGIBLE=1\n"
        "decision_status.LIVE_ELIGIBLE=0\n"
        "decision_status.REJECTED=1\n"
        "entry_ev_known=1\n"
        "entry_ev_unknown=1\n"
        "paper_expected_funding_known=1\n"
        "paper_expected_funding_unknown=1\n"
        "paper_total_fees_known=1\n"
        "paper_total_fees_unknown=1\n"
        "decision_net_profit_known=1\n"
        "decision_net_profit_unknown=1\n"
        "paper_net_profit_known=1\n"
        "paper_net_profit_unknown=1\n"
        "ledger_event_count=6\n"
        "ledger_event_sequences=1,2,3,4,5,6\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed,route_decision,"
        "paper_rejection_recorded\n"
        "aggregate_paper_net_profit_usd=None\n"
        "ledger_path=None\n"
    )


def test_paper_trade_session_writes_explicit_deterministic_report_history_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        snapshot = SimpleNamespace(
            risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
        )
        if route.route_id == "session-started":
            return (
                DecisionResult(
                    route_id=route.route_id,
                    mode=EvaluationMode.ENTRY,
                    status=RouteStatus.PAPER_ELIGIBLE,
                    reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
                    net_profit_usd=Decimal("4.5"),
                    entry_ev=SimpleNamespace(
                        expected_funding_usd=Decimal("7"),
                        total_fees_usd=Decimal("1"),
                        simulated_roundtrip_cost_usd=Decimal("1.5"),
                        net_profit_usd=Decimal("4.5"),
                    ),
                    capture_plan=None,
                    decided_at=kwargs["assembled_at"],
                ),
                snapshot,
            )
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            snapshot,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    routes_payload = [
        _paper_session_route(route_id="session-started", capture_id="capture-started"),
        _paper_session_route(
            route_id="session-rejected",
            capture_id="capture-rejected",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]
    report_path = tmp_path / "paper-session-report.json"
    args = _paper_session_args(
        tmp_path,
        routes_payload,
        session_report_json_path=report_path,
    )

    assert cli.main(args) == 0
    first_report_text = report_path.read_text(encoding="utf-8")
    assert cli.main(args) == 0
    assert report_path.read_text(encoding="utf-8") == first_report_text

    report = json.loads(first_report_text)
    assert report["report"] == "Paper Trade Session Report"
    assert report["schema_version"] == 1
    assert report["session"] == {
        "ledger_path": None,
        "route_count": 2,
    }
    assert [route["route"]["route_id"] for route in report["routes"]] == [
        "session-started",
        "session-rejected",
    ]
    assert report["routes"][0]["decision"]["entry_ev"] == {
        "expected_funding_usd": "7",
        "net_profit_usd": "4.5",
        "simulated_roundtrip_cost_usd": "1.5",
        "total_fees_usd": "1",
    }
    assert report["routes"][0]["decision"]["net_profit_usd"] == "4.5"
    assert report["routes"][0]["paper"]["net_profit_usd"] == "4.5"
    assert report["routes"][1]["decision"]["entry_ev"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "total_fees_usd": None,
    }
    assert report["routes"][1]["decision"]["net_profit_usd"] is None
    assert report["routes"][1]["paper"]["expected_funding_usd"] is None
    assert report["routes"][1]["paper"]["total_fees_usd"] is None
    assert report["routes"][1]["paper"]["net_profit_usd"] is None
    assert report["summary"]["entry_ev_known"] == 1
    assert report["summary"]["entry_ev_unknown"] == 1
    assert report["summary"]["paper_expected_funding_known"] == 1
    assert report["summary"]["paper_expected_funding_unknown"] == 1
    assert report["summary"]["paper_total_fees_known"] == 1
    assert report["summary"]["paper_total_fees_unknown"] == 1
    assert report["summary"]["decision_net_profit_known"] == 1
    assert report["summary"]["decision_net_profit_unknown"] == 1
    assert report["summary"]["paper_net_profit_known"] == 1
    assert report["summary"]["paper_net_profit_unknown"] == 1
    assert report["summary"]["aggregate_paper_net_profit_usd"] is None
    assert "paper_net_profit_sum" not in report["summary"]
    assert "aggregate_paper_pnl_usd" not in report["summary"]
    assert report["summary"]["ledger_event_sequences"] == [1, 2, 3, 4, 5, 6]
    assert [event["sequence"] for event in report["ledger_events"]] == [1, 2, 3, 4, 5, 6]
    assert '"expected_funding_usd": 0' not in first_report_text
    assert '"total_fees_usd": 0' not in first_report_text
    assert '"net_profit_usd": 0' not in first_report_text

    capsys.readouterr()


def test_paper_trade_session_handles_missing_snapshot_without_paper_events(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, None]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.REJECTED,
                reasons=(RejectReason.REQUIRED_LIVE_DATA_MISSING,),
                net_profit_usd=None,
                entry_ev=None,
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            None,
        )

    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert cli.main(_paper_session_args(tmp_path, [_paper_session_route()])) == 0

    output = capsys.readouterr().out
    assert "snapshot=UNKNOWN\n" in output
    assert "paper_start_blockers=public_snapshot_unavailable\n" in output
    assert "ledger_event_count=0\n" in output
    assert "routes_with_snapshot=0\n" in output
    assert "routes_without_snapshot=1\n" in output
    assert "paper_started=0\n" in output
    assert "paper_not_started=1\n" in output
    assert "entry_ev_known=0\n" in output
    assert "entry_ev_unknown=1\n" in output
    assert "paper_expected_funding_known=0\n" in output
    assert "paper_expected_funding_unknown=1\n" in output
    assert "paper_total_fees_known=0\n" in output
    assert "paper_total_fees_unknown=1\n" in output
    assert "decision_net_profit_unknown=1\n" in output
    assert "paper_net_profit_unknown=1\n" in output
    assert "aggregate_paper_net_profit_usd=None\n" in output
    assert "entry_ev_known=1" not in output
    assert "paper_expected_funding_known=1" not in output
    assert "paper_total_fees_known=1" not in output
    assert "paper.net_profit_usd=0" not in output


def test_paper_trade_session_can_use_explicit_sqlite_ledger_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    class RecordingRiseXAdapter:
        name = "RiseX"

    class RecordingHyperliquidAdapter:
        name = "Hyperliquid"

    def fake_report_runner(**kwargs: object) -> tuple[DecisionResult, object]:
        route = kwargs["route"]
        assert isinstance(route, RouteCandidate)
        return (
            DecisionResult(
                route_id=route.route_id,
                mode=EvaluationMode.ENTRY,
                status=RouteStatus.PAPER_ELIGIBLE,
                reasons=(RejectReason.LIVE_GATES_NOT_IMPLEMENTED,),
                net_profit_usd=Decimal("4.5"),
                entry_ev=SimpleNamespace(
                    expected_funding_usd=Decimal("7"),
                    total_fees_usd=Decimal("1"),
                    simulated_roundtrip_cost_usd=Decimal("1.5"),
                    net_profit_usd=Decimal("4.5"),
                ),
                capture_plan=None,
                decided_at=kwargs["assembled_at"],
            ),
            SimpleNamespace(
                risex_funding_settlement_at=datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
            ),
        )

    db_path = tmp_path / "paper-session-ledger.sqlite"
    monkeypatch.setattr(cli, "RiseXObservationAdapter", RecordingRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", RecordingHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", fake_report_runner)

    assert (
        cli.main(
            _paper_session_args(
                tmp_path,
                [_paper_session_route()],
                ledger_sqlite_path=db_path,
            )
        )
        == 0
    )

    output = capsys.readouterr().out
    assert f"ledger_path={db_path}\n" in output
    assert "ledger_event_count=4\n" in output

    reopened = SQLiteLedger(db_path)
    try:
        assert [event.event_type for event in reopened.records()] == [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        ]
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "routes_payload",
    (
        [],
        {"routes": [_paper_session_route()]},
        [{"routes": [_paper_session_route()]}],
        [_paper_session_route(mode="DISCOVERY")],
        [_paper_session_route(risex_venue="WrongVenue")],
        [_paper_session_route(hedge_venue="WrongVenue")],
        [_paper_session_route(hedge_side="buy")],
        [_paper_session_route(target_notional_usd="0")],
        [_paper_session_route(target_notional_usd="NaN")],
        [_paper_session_route(assembled_at="2026-08-13T12:00:00")],
        [{**_paper_session_route(), "watchlist": "BTC"}],
        [{key: value for key, value in _paper_session_route().items() if key != "route_id"}],
        [{**_paper_session_route(), "target_notional_usd": 500}],
    ),
)
def test_paper_trade_session_rejects_malformed_route_list_before_adapter_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    routes_payload: object,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_report_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("report_runner")
        raise AssertionError("report runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_report_runner)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_paper_session_args(tmp_path, routes_payload))

    assert exc_info.value.code == 2
    assert calls == []


def test_paper_trade_session_rejects_invalid_json_before_adapter_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)

    routes_path = tmp_path / "invalid-session-routes.json"
    routes_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["paper-trade-session", "--routes-json-path", str(routes_path)])

    assert exc_info.value.code == 2
    assert calls == []


def test_paper_trade_session_rejects_over_limit_route_list_before_adapter_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_report_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("report_runner")
        raise AssertionError("report runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_report_runner)

    routes_payload = [
        _paper_session_route(route_id=f"session-route-{index}")
        for index in range(cli._MAX_PAPER_SESSION_ROUTES + 1)
    ]

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_paper_session_args(tmp_path, routes_payload))

    assert exc_info.value.code == 2
    assert calls == []


def test_paper_trade_session_does_not_add_live_order_private_or_telegram_behavior() -> None:
    source = inspect.getsource(cli)
    session_source = inspect.getsource(cli._run_paper_trade_session)

    assert "apps.live_runner" not in source
    assert "core.execution" not in source
    assert "telegram" not in source.lower()
    assert "webhook" not in source.lower()
    assert "run_guarded_live" not in session_source
    assert "order_placement" not in session_source
    assert "approval" not in session_source


def test_real_data_cli_does_not_directly_call_snapshot_handoff_or_evaluate() -> None:
    source = inspect.getsource(cli)

    assert "assemble_route_snapshot_from_adapters" not in source
    assert "evaluate_route" not in source


@pytest.mark.parametrize(
    "overrides",
    (
        {"route_id": ""},
        {"capture_id": " "},
        {"risex_venue": "WrongVenue"},
        {"hedge_venue": "WrongVenue"},
        {"risex_symbol": ""},
        {"hedge_symbol": " "},
        {"risex_side": "hold"},
        {"hedge_side": "hold"},
        {"hedge_side": "buy"},
        {"mode": "LIVE"},
        {"target_notional_usd": "abc"},
        {"target_notional_usd": "0"},
        {"target_notional_usd": "-1"},
        {"target_notional_usd": "NaN"},
        {"target_notional_usd": "Infinity"},
        {"assembled_at": "not-a-date"},
        {"assembled_at": "2026-08-13T12:00:00"},
        {"route_id": OMIT},
        {"target_notional_usd": OMIT},
        {"assembled_at": OMIT},
    ),
)
def test_real_data_cli_rejects_malformed_input_before_adapter_or_runner_calls(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RISEx adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_real_data_args(**overrides))

    assert exc_info.value.code == 2
    assert calls == []


def test_real_data_cli_json_format_requires_public_readiness_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)

    with pytest.raises(SystemExit) as exc_info:
        cli.main([*_real_data_args(), "--public-readiness-report-format", "json"])

    assert exc_info.value.code == 2
    assert calls == []


def test_real_data_cli_report_rejects_malformed_input_before_adapter_or_runner_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_report_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("report_runner")
        raise AssertionError("report runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_report_runner)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_real_data_report_args(route_id=""))

    assert exc_info.value.code == 2
    assert calls == []


@pytest.mark.parametrize(
    "overrides",
    (
        {"route_id": ""},
        {"capture_id": " "},
        {"risex_venue": "WrongVenue"},
        {"hedge_venue": "WrongVenue"},
        {"risex_symbol": ""},
        {"hedge_symbol": " "},
        {"risex_side": "hold"},
        {"hedge_side": "hold"},
        {"hedge_side": "buy"},
        {"mode": "DISCOVERY"},
        {"mode": "LIVE"},
        {"target_notional_usd": "abc"},
        {"target_notional_usd": "0"},
        {"target_notional_usd": "-1"},
        {"target_notional_usd": "NaN"},
        {"target_notional_usd": "Infinity"},
        {"assembled_at": "not-a-date"},
        {"assembled_at": "2026-08-13T12:00:00"},
        {"route_id": OMIT},
        {"target_notional_usd": OMIT},
        {"assembled_at": OMIT},
    ),
)
def test_paper_trade_cli_rejects_malformed_input_before_adapter_or_runner_calls(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("RiseX adapter must not be constructed")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("Hyperliquid adapter must not be constructed")

    def forbidden_report_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("report_runner")
        raise AssertionError("report runner must not be called")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_report_runner)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_paper_trade_args(**overrides))

    assert exc_info.value.code == 2
    assert calls == []
