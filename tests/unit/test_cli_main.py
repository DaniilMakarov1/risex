from __future__ import annotations

import inspect
import json
import shlex
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


def _paper_session_package_args(
    tmp_path,
    command_payload: object,
    *,
    routes_json_output_path: object = OMIT,
    preview_json_output_path: object = OMIT,
    session_report_json_path: object = OMIT,
) -> list[str]:
    payload_path = tmp_path / "paper-session-command-payload.json"
    payload_path.write_text(json.dumps(command_payload), encoding="utf-8")
    args = [
        "build-paper-session-package",
        "--paper-session-command-payload-json-path",
        str(payload_path),
    ]
    if routes_json_output_path is not OMIT:
        args.extend(["--routes-json-output-path", str(routes_json_output_path)])
    if preview_json_output_path is not OMIT:
        args.extend(["--preview-json-output-path", str(preview_json_output_path)])
    if session_report_json_path is not OMIT:
        args.extend(["--session-report-json-path", str(session_report_json_path)])
    return args


def _paper_session_report_payload(**overrides: object) -> dict[str, object]:
    report = {
        "report": "Paper Trade Session Report",
        "schema_version": 1,
        "session": {
            "ledger_path": None,
            "route_count": 2,
        },
        "routes": [
            {
                "route_index": 1,
                "route": {
                    "route_id": "session-started",
                    "capture_id": "capture-started",
                    "risex_venue": "RiseX",
                    "risex_symbol": "BTC-PERP",
                    "risex_side": "buy",
                    "hedge_venue": "Hyperliquid",
                    "hedge_symbol": "BTC",
                    "hedge_side": "sell",
                    "target_notional_usd": "500",
                    "mode": "ENTRY",
                    "assembled_at": "2026-08-13T12:00:00+00:00",
                },
                "decision": {
                    "mode": "ENTRY",
                    "status": "PAPER_ELIGIBLE",
                    "reasons": ["LIVE_GATES_NOT_IMPLEMENTED"],
                    "net_profit_usd": "4.5",
                    "entry_ev": {
                        "expected_funding_usd": "7",
                        "total_fees_usd": "1",
                        "simulated_roundtrip_cost_usd": "1.5",
                        "net_profit_usd": "4.5",
                    },
                },
                "snapshot": {
                    "state": "AVAILABLE",
                    "funding_settlement_at": "2026-08-13T16:00:00+00:00",
                },
                "paper": {
                    "started": True,
                    "start_attribution": "entry_paper_eligible_decision",
                    "start_blockers": [],
                    "expected_funding_usd": "7",
                    "total_fees_usd": "1",
                    "simulated_roundtrip_cost_usd": "1.5",
                    "net_profit_usd": "4.5",
                },
                "ledger_events": [],
            },
            {
                "route_index": 2,
                "route": {
                    "route_id": "session-rejected",
                    "capture_id": "capture-rejected",
                    "risex_venue": "RiseX",
                    "risex_symbol": "BTC-PERP",
                    "risex_side": "buy",
                    "hedge_venue": "Hyperliquid",
                    "hedge_symbol": "BTC",
                    "hedge_side": "sell",
                    "target_notional_usd": "500",
                    "mode": "ENTRY",
                    "assembled_at": "2026-08-13T12:01:00+00:00",
                },
                "decision": {
                    "mode": "ENTRY",
                    "status": "REJECTED",
                    "reasons": ["REQUIRED_LIVE_DATA_MISSING"],
                    "net_profit_usd": None,
                    "entry_ev": {
                        "expected_funding_usd": None,
                        "total_fees_usd": None,
                        "simulated_roundtrip_cost_usd": None,
                        "net_profit_usd": None,
                    },
                },
                "snapshot": {
                    "state": "AVAILABLE",
                    "funding_settlement_at": "2026-08-13T16:00:00+00:00",
                },
                "paper": {
                    "started": False,
                    "start_attribution": "paper_start_blocked_by_decision",
                    "start_blockers": ["decision_status_not_paper_eligible"],
                    "expected_funding_usd": None,
                    "total_fees_usd": None,
                    "simulated_roundtrip_cost_usd": None,
                    "net_profit_usd": None,
                },
                "ledger_events": [],
            },
        ],
        "summary": {
            "routes_total": 2,
            "routes_with_snapshot": 2,
            "routes_without_snapshot": 0,
            "paper_started": 1,
            "paper_not_started": 1,
            "decision_status": {
                "RESEARCH_ONLY": 0,
                "PAPER_ELIGIBLE": 1,
                "LIVE_ELIGIBLE": 0,
                "REJECTED": 1,
            },
            "entry_ev_known": 1,
            "entry_ev_unknown": 1,
            "paper_expected_funding_known": 1,
            "paper_expected_funding_unknown": 1,
            "paper_total_fees_known": 1,
            "paper_total_fees_unknown": 1,
            "decision_net_profit_known": 1,
            "decision_net_profit_unknown": 1,
            "paper_net_profit_known": 1,
            "paper_net_profit_unknown": 1,
            "ledger_event_count": 6,
            "ledger_event_sequences": [1, 2, 3, 4, 5, 6],
            "ledger_event_types": [
                "route_decision",
                "paper_capture_opened",
                "paper_settlement_observed",
                "paper_capture_closed",
                "route_decision",
                "paper_rejection_recorded",
            ],
            "aggregate_paper_net_profit_usd": None,
            "ledger_path": None,
        },
        "ledger_events": [],
    }
    report.update(overrides)
    return report


def _render_paper_session_report_args(tmp_path, report_payload: object) -> list[str]:
    report_path = tmp_path / "paper-session-report.json"
    report_path.write_text(json.dumps(report_payload), encoding="utf-8")
    return [
        "render-paper-session-report",
        "--session-report-json-path",
        str(report_path),
    ]


def _render_paper_session_report_from_payload_args(
    tmp_path,
    display_payload: object,
) -> list[str]:
    payload_path = tmp_path / "paper-session-display-command-payload.json"
    payload_path.write_text(json.dumps(display_payload), encoding="utf-8")
    return [
        "render-paper-session-report-from-payload",
        "--paper-session-display-command-payload-json-path",
        str(payload_path),
    ]


def _build_paper_session_display_payload_args(
    *,
    session_report_json_path: object = OMIT,
    display_payload_json_path: object = OMIT,
) -> list[str]:
    args = ["build-paper-session-display-payload"]
    if session_report_json_path is not OMIT:
        args.extend(["--session-report-json-path", str(session_report_json_path)])
    if display_payload_json_path is not OMIT:
        args.extend(["--display-payload-json-path", str(display_payload_json_path)])
    return args


def _build_paper_session_display_command_preview_args(
    *,
    display_payload_json_path: object = OMIT,
    preview_json_output_path: object = OMIT,
) -> list[str]:
    args = ["build-paper-session-display-command-preview"]
    if display_payload_json_path is not OMIT:
        args.extend(
            [
                "--paper-session-display-command-payload-json-path",
                str(display_payload_json_path),
            ]
        )
    if preview_json_output_path is not OMIT:
        args.extend(["--preview-json-output-path", str(preview_json_output_path)])
    return args


def _parse_paper_session_display_command_text_args(
    tmp_path,
    command_text: str,
    *,
    display_payload_json_path: object = OMIT,
    command_text_path: object = OMIT,
) -> list[str]:
    if command_text_path is OMIT:
        command_text_path = tmp_path / "paper session display command text.txt"
    command_text_path.write_text(command_text, encoding="utf-8")
    args = [
        "parse-paper-session-display-command-text",
        "--paper-session-display-command-text-path",
        str(command_text_path),
    ]
    if display_payload_json_path is not OMIT:
        args.extend(["--display-payload-json-path", str(display_payload_json_path)])
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


def test_render_paper_session_report_outputs_deterministic_stdout_only_display(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("renderer must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("renderer must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("renderer must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("renderer must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("renderer must not call paper lifecycle")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)

    args = _render_paper_session_report_args(tmp_path, _paper_session_report_payload())
    report_path = tmp_path / "paper-session-report.json"
    report_text = report_path.read_text(encoding="utf-8")

    assert cli.main(args) == 0
    first_output = capsys.readouterr().out
    assert cli.main(args) == 0

    assert calls == []
    assert report_path.read_text(encoding="utf-8") == report_text
    assert capsys.readouterr().out == first_output
    assert first_output == (
        "Paper Session Report Display\n"
        "route_count=2\n"
        "route_ids=session-started,session-rejected\n"
        "route.1.route_id=session-started\n"
        "route.1.decision_status=PAPER_ELIGIBLE\n"
        "route.1.paper_started=true\n"
        "route.1.decision_net_profit_usd=4.5\n"
        "route.1.decision_entry_ev_expected_funding_usd=7\n"
        "route.1.decision_entry_ev_total_fees_usd=1\n"
        "route.1.decision_entry_ev_simulated_roundtrip_cost_usd=1.5\n"
        "route.1.decision_entry_ev_net_profit_usd=4.5\n"
        "route.1.paper_expected_funding_usd=7\n"
        "route.1.paper_total_fees_usd=1\n"
        "route.1.paper_simulated_roundtrip_cost_usd=1.5\n"
        "route.1.paper_net_profit_usd=4.5\n"
        "route.2.route_id=session-rejected\n"
        "route.2.decision_status=REJECTED\n"
        "route.2.paper_started=false\n"
        "route.2.decision_net_profit_usd=null\n"
        "route.2.decision_entry_ev_expected_funding_usd=null\n"
        "route.2.decision_entry_ev_total_fees_usd=null\n"
        "route.2.decision_entry_ev_simulated_roundtrip_cost_usd=null\n"
        "route.2.decision_entry_ev_net_profit_usd=null\n"
        "route.2.paper_expected_funding_usd=null\n"
        "route.2.paper_total_fees_usd=null\n"
        "route.2.paper_simulated_roundtrip_cost_usd=null\n"
        "route.2.paper_net_profit_usd=null\n"
        "summary.decision_net_profit_known=1\n"
        "summary.decision_net_profit_unknown=1\n"
        "summary.entry_ev_known=1\n"
        "summary.entry_ev_unknown=1\n"
        "summary.paper_expected_funding_known=1\n"
        "summary.paper_expected_funding_unknown=1\n"
        "summary.paper_net_profit_known=1\n"
        "summary.paper_net_profit_unknown=1\n"
        "summary.paper_total_fees_known=1\n"
        "summary.paper_total_fees_unknown=1\n"
        "summary.aggregate_paper_net_profit_usd=null\n"
    )
    assert "paper_net_profit_usd=0" not in first_output
    assert "summary.aggregate_paper_net_profit_usd=0" not in first_output


@pytest.mark.parametrize(
    "case",
    (
        "top_level_array",
        "empty_routes",
        "route_count_mismatch",
        "numeric_economics",
        "missing_paper_net_profit",
        "missing_entry_ev_expected_funding",
        "missing_aggregate",
        "non_null_aggregate",
        "missing_summary_count",
    ),
)
def test_render_paper_session_report_rejects_malformed_input_before_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    case: str,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("renderer must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("renderer must not construct adapters")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("renderer must not run sessions")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("renderer must not instantiate ledgers")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("renderer must not call paper lifecycle")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)

    if case == "top_level_array":
        malformed_payload: object = []
    else:
        malformed_payload = json.loads(json.dumps(_paper_session_report_payload()))
        assert isinstance(malformed_payload, dict)
        if case == "empty_routes":
            malformed_payload["session"]["route_count"] = 0
            malformed_payload["routes"] = []
        elif case == "route_count_mismatch":
            malformed_payload["session"]["route_count"] = 1
        elif case == "numeric_economics":
            malformed_payload["routes"][1]["paper"]["net_profit_usd"] = 0
        elif case == "missing_paper_net_profit":
            del malformed_payload["routes"][0]["paper"]["net_profit_usd"]
        elif case == "missing_entry_ev_expected_funding":
            del malformed_payload["routes"][0]["decision"]["entry_ev"][
                "expected_funding_usd"
            ]
        elif case == "missing_aggregate":
            del malformed_payload["summary"]["aggregate_paper_net_profit_usd"]
        elif case == "non_null_aggregate":
            malformed_payload["summary"]["aggregate_paper_net_profit_usd"] = "4.5"
        elif case == "missing_summary_count":
            del malformed_payload["summary"]["paper_net_profit_unknown"]
        else:  # pragma: no cover - guarded by parametrization above.
            raise AssertionError(case)

    report_path = tmp_path / "malformed-paper-session-report.json"
    report_path.write_text(json.dumps(malformed_payload), encoding="utf-8")
    original_text = report_path.read_text(encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "render-paper-session-report",
                "--session-report-json-path",
                str(report_path),
            ]
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert report_path.read_text(encoding="utf-8") == original_text
    captured = capsys.readouterr()
    assert captured.out == ""
    if case == "missing_paper_net_profit":
        assert "routes[1].paper.net_profit_usd must be present" in captured.err
    if case == "missing_entry_ev_expected_funding":
        assert (
            "routes[1].decision.entry_ev.expected_funding_usd must be present"
            in captured.err
        )


def test_render_paper_session_report_rejects_invalid_json_before_output(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    report_path = tmp_path / "invalid-paper-session-report.json"
    report_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "render-paper-session-report",
                "--session-report-json-path",
                str(report_path),
            ]
        )

    assert exc_info.value.code == 2
    assert capsys.readouterr().out == ""


def test_render_paper_session_report_from_payload_delegates_to_existing_renderer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display payload command must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display payload command must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display payload command must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display payload command must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display payload command must not call paper lifecycle")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)

    report_path = tmp_path / "paper session report with spaces.json"
    report_path.write_text(
        json.dumps(_paper_session_report_payload()),
        encoding="utf-8",
    )
    report_text = report_path.read_text(encoding="utf-8")

    assert (
        cli.main(
            [
                "render-paper-session-report",
                "--session-report-json-path",
                str(report_path),
            ]
        )
        == 0
    )
    direct_output = capsys.readouterr().out

    args = _render_paper_session_report_from_payload_args(
        tmp_path,
        {
            "schema_version": 1,
            "session_report_json_path": f"  {report_path}  ",
        },
    )
    assert cli.main(args) == 0

    assert calls == []
    assert report_path.read_text(encoding="utf-8") == report_text
    assert capsys.readouterr().out == direct_output
    assert "summary.aggregate_paper_net_profit_usd=null\n" in direct_output
    assert "summary.aggregate_paper_net_profit_usd=0" not in direct_output
    assert "paper_net_profit_usd=0" not in direct_output


@pytest.mark.parametrize(
    "payload",
    (
        {"schema_version": 1, "session_report_json_path": None},
        {
            "schema_version": 1,
            "session_report_json_path": "paper-session-report.json",
            "routes": [],
        },
        {"schema_version": 2, "session_report_json_path": "paper-session-report.json"},
        {"schema_version": 1, "session_report_json_path": ""},
        {"session_report_json_path": "paper-session-report.json"},
    ),
)
def test_render_paper_session_report_from_payload_rejects_malformed_payload_before_report_read(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    payload: object,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display payload command must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display payload command must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display payload command must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display payload command must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display payload command must not call paper lifecycle")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)

    payload_path = tmp_path / "malformed-display-command-payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    report_path = tmp_path / "paper-session-report.json"
    report_path.write_text(json.dumps(_paper_session_report_payload()), encoding="utf-8")
    report_text = report_path.read_text(encoding="utf-8")
    read_paths: list[str] = []
    original_read_text = cli.Path.read_text

    def recording_read_text(self, *args: object, **kwargs: object) -> str:
        read_paths.append(str(self))
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(cli.Path, "read_text", recording_read_text)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "render-paper-session-report-from-payload",
                "--paper-session-display-command-payload-json-path",
                str(payload_path),
            ]
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert read_paths == [str(payload_path)]
    assert report_path.read_text(encoding="utf-8") == report_text
    captured = capsys.readouterr()
    assert captured.out == ""


def test_render_paper_session_report_from_payload_requires_explicit_payload_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbidden_parser(_payload_text: str) -> str:
        calls.append("parser")
        raise AssertionError("payload must not be parsed when fixture path is absent")

    monkeypatch.setattr(
        cli,
        "_paper_session_report_path_from_display_command_payload",
        forbidden_parser,
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["render-paper-session-report-from-payload"])

    assert exc_info.value.code == 2
    assert calls == []


def test_render_paper_session_report_from_payload_has_no_forbidden_runtime_behavior() -> None:
    command_source = inspect.getsource(cli._run_render_paper_session_report_from_payload)
    lowered = command_source.lower()

    assert "_paper_session_report_path_from_display_command_payload" in command_source
    assert "_run_render_paper_session_report" in command_source
    assert "write_text" not in command_source
    assert "run_real_data_research_route" not in command_source
    assert "run_paper_lifecycle" not in command_source
    assert "InMemoryLedger" not in command_source
    assert "SQLiteLedger" not in command_source
    assert "RiseXObservationAdapter" not in command_source
    assert "HyperliquidObservationAdapter" not in command_source
    assert "apps.live_runner" not in command_source
    assert "core.execution" not in command_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "order_placement" not in lowered
    assert "aggregate" not in lowered
    assert "pnl" not in lowered


def test_build_paper_session_display_payload_writes_rx062_fixture(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display payload builder must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display payload builder must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display payload builder must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display payload builder must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display payload builder must not call paper lifecycle")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)

    report_path = tmp_path / "paper session report with spaces.json"
    report_path.write_text(
        json.dumps(_paper_session_report_payload()),
        encoding="utf-8",
    )
    report_text = report_path.read_text(encoding="utf-8")
    display_payload_path = tmp_path / "display payload with spaces.json"
    args = _build_paper_session_display_payload_args(
        session_report_json_path=report_path,
        display_payload_json_path=display_payload_path,
    )

    assert cli.main(args) == 0
    first_payload_text = display_payload_path.read_text(encoding="utf-8")
    first_output = capsys.readouterr().out
    assert cli.main(args) == 0

    assert calls == []
    assert report_path.read_text(encoding="utf-8") == report_text
    assert display_payload_path.read_text(encoding="utf-8") == first_payload_text
    assert capsys.readouterr().out == first_output

    display_payload = json.loads(first_payload_text)
    assert display_payload == {
        "schema_version": 1,
        "session_report_json_path": str(report_path),
    }
    assert set(display_payload) == {"schema_version", "session_report_json_path"}
    assert (
        cli._paper_session_report_path_from_display_command_payload(first_payload_text)
        == str(report_path)
    )
    assert first_output == (
        f"display_payload_json_path={display_payload_path}\n"
        f"session_report_json_path={report_path}\n"
    )

    sanitized_payload = dict(display_payload)
    sanitized_payload["session_report_json_path"] = "<session-report-path>"
    lowered_payload = json.dumps(sanitized_payload, sort_keys=True).lower()
    forbidden_fields = (
        "routes",
        "decision",
        "paper",
        "summary",
        "ledger",
        "aggregate_paper_net_profit_usd",
        "paper_net_profit_usd",
        "telegram",
        "webhook",
        "token",
        "credential",
        "secret",
        "api_key",
        "private",
        "account",
        "balance",
        "order_payload",
        "sendable",
        "live",
        "pnl",
        '"net_profit_usd": 0',
        '"expected_funding_usd": 0',
        '"total_fees_usd": 0',
    )
    for forbidden_field in forbidden_fields:
        assert forbidden_field not in lowered_payload


@pytest.mark.parametrize(
    "case",
    (
        "missing_report",
        "invalid_json",
        "top_level_array",
        "numeric_economics",
        "missing_aggregate",
        "non_null_aggregate",
    ),
)
def test_build_paper_session_display_payload_rejects_malformed_report_before_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    case: str,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display payload builder must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display payload builder must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display payload builder must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display payload builder must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display payload builder must not call paper lifecycle")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("malformed report must fail before artifact write")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    report_path = tmp_path / f"{case}-paper-session-report.json"
    if case != "missing_report":
        if case == "invalid_json":
            malformed_payload: object = "{not-json"
            report_path.write_text(str(malformed_payload), encoding="utf-8")
        elif case == "top_level_array":
            report_path.write_text(json.dumps([]), encoding="utf-8")
        else:
            malformed_report = json.loads(json.dumps(_paper_session_report_payload()))
            assert isinstance(malformed_report, dict)
            if case == "numeric_economics":
                malformed_report["routes"][1]["paper"]["net_profit_usd"] = 0
            elif case == "missing_aggregate":
                del malformed_report["summary"]["aggregate_paper_net_profit_usd"]
            elif case == "non_null_aggregate":
                malformed_report["summary"]["aggregate_paper_net_profit_usd"] = "4.5"
            else:  # pragma: no cover - guarded by parametrization above.
                raise AssertionError(case)
            report_path.write_text(json.dumps(malformed_report), encoding="utf-8")
    original_report_text = (
        None if not report_path.exists() else report_path.read_text(encoding="utf-8")
    )
    display_payload_path = tmp_path / "display-payload.json"

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _build_paper_session_display_payload_args(
                session_report_json_path=report_path,
                display_payload_json_path=display_payload_path,
            )
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert not display_payload_path.exists()
    if original_report_text is not None:
        assert report_path.read_text(encoding="utf-8") == original_report_text
    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.parametrize(
    "omitted",
    ("session_report_json_path", "display_payload_json_path"),
)
def test_build_paper_session_display_payload_requires_explicit_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    omitted: str,
) -> None:
    calls: list[str] = []

    def forbidden_read_text(self, *_args: object, **_kwargs: object) -> str:
        calls.append(str(self))
        raise AssertionError("report must not be read when required paths are absent")

    monkeypatch.setattr(cli.Path, "read_text", forbidden_read_text)

    kwargs = {
        "session_report_json_path": tmp_path / "paper-session-report.json",
        "display_payload_json_path": tmp_path / "display-payload.json",
    }
    kwargs[omitted] = OMIT

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_build_paper_session_display_payload_args(**kwargs))

    assert exc_info.value.code == 2
    assert calls == []


def test_build_paper_session_display_payload_has_no_forbidden_runtime_behavior() -> None:
    builder_source = inspect.getsource(cli._run_build_paper_session_display_payload)
    lowered = builder_source.lower()

    assert "_validated_paper_session_report_display_values" in builder_source
    assert "_paper_session_report_path_from_display_command_payload" in builder_source
    assert "_write_json_artifact" in builder_source
    assert "run_real_data_research_route" not in builder_source
    assert "run_paper_lifecycle" not in builder_source
    assert "InMemoryLedger" not in builder_source
    assert "SQLiteLedger" not in builder_source
    assert "RiseXObservationAdapter" not in builder_source
    assert "HyperliquidObservationAdapter" not in builder_source
    assert "apps.live_runner" not in builder_source
    assert "core.execution" not in builder_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "order_placement" not in lowered
    assert "aggregate" not in lowered
    assert "pnl" not in lowered


def test_build_paper_session_display_command_preview_writes_deterministic_manifest(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display command preview must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display command preview must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display command preview must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display command preview must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display command preview must not call paper lifecycle")

    def forbidden_render(
        _args: object,
        _parser: object,
    ) -> None:
        calls.append("render")
        raise AssertionError("display command preview must not render reports")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)
    monkeypatch.setattr(cli, "_run_render_paper_session_report", forbidden_render)
    monkeypatch.setattr(
        cli,
        "_run_render_paper_session_report_from_payload",
        forbidden_render,
    )

    report_path = tmp_path / "missing paper session report with spaces.json"
    display_payload_path = tmp_path / "display payload with spaces.json"
    preview_path = tmp_path / "display command preview with spaces.json"
    display_payload_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    original_read_text = cli.Path.read_text
    read_paths: list[str] = []

    def recording_read_text(self, *args: object, **kwargs: object) -> str:
        read_paths.append(str(self))
        if str(self) == str(report_path):
            raise AssertionError("display command preview must not read report JSON")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(cli.Path, "read_text", recording_read_text)
    args = _build_paper_session_display_command_preview_args(
        display_payload_json_path=display_payload_path,
        preview_json_output_path=preview_path,
    )

    assert cli.main(args) == 0
    first_preview_artifact = original_read_text(preview_path, encoding="utf-8")
    first_output = capsys.readouterr().out
    assert cli.main(args) == 0

    assert calls == []
    assert read_paths == [str(display_payload_path), str(display_payload_path)]
    assert original_read_text(preview_path, encoding="utf-8") == first_preview_artifact
    assert capsys.readouterr().out == first_output
    assert not report_path.exists()

    preview = json.loads(first_preview_artifact)
    assert preview == {
        "preview": "Paper Session Display Command Preview",
        "schema_version": 1,
        "display_payload_json_path": str(display_payload_path),
        "manual_command": {
            "argv": [
                "python3",
                "-m",
                "apps.cli.main",
                "render-paper-session-report-from-payload",
                "--paper-session-display-command-payload-json-path",
                str(display_payload_path),
            ],
            "text": (
                "python3 -m apps.cli.main render-paper-session-report-from-payload "
                "--paper-session-display-command-payload-json-path "
                f"'{display_payload_path}'"
            ),
        },
    }

    sanitized_preview = dict(preview)
    sanitized_preview["display_payload_json_path"] = "<display-payload-path>"
    sanitized_preview["manual_command"] = {
        "argv": [
            "<python>",
            "-m",
            "apps.cli.main",
            "render-paper-session-report-from-payload",
            "--paper-session-display-command-payload-json-path",
            "<display-payload-path>",
        ],
        "text": (
            "python3 -m apps.cli.main render-paper-session-report-from-payload "
            "--paper-session-display-command-payload-json-path "
            "<display-payload-path>"
        ),
    }
    lowered_preview = json.dumps(sanitized_preview, sort_keys=True).lower()
    forbidden_fields = (
        "routes",
        "decision",
        "paper_started",
        "paper_outcome",
        "summary",
        "ledger",
        "aggregate_paper_net_profit_usd",
        "paper_net_profit_usd",
        "expected_funding_usd",
        "total_fees_usd",
        "telegram",
        "webhook",
        "token",
        "credential",
        "secret",
        "api_key",
        "private",
        "account",
        "balance",
        "order_payload",
        "sendable",
        "live",
        "pnl",
        '"net_profit_usd": 0',
        '"expected_funding_usd": 0',
        '"total_fees_usd": 0',
    )
    for forbidden_field in forbidden_fields:
        assert forbidden_field not in lowered_preview

    assert first_output == (
        "Paper Session Display Command Preview\n"
        f"display_payload_json_path={display_payload_path}\n"
        f"preview_json_path={preview_path}\n"
    )


@pytest.mark.parametrize(
    "payload",
    (
        "{not-json",
        json.dumps([]),
        json.dumps({"schema_version": 1}),
        json.dumps({"session_report_json_path": "/tmp/report.json"}),
        json.dumps(
            {
                "schema_version": 1,
                "session_report_json_path": "/tmp/report.json",
                "routes": [],
            }
        ),
        json.dumps({"schema_version": 2, "session_report_json_path": "/tmp/report.json"}),
        json.dumps({"schema_version": 1, "session_report_json_path": None}),
        json.dumps({"schema_version": 1, "session_report_json_path": ""}),
    ),
)
def test_build_paper_session_display_command_preview_rejects_malformed_payload_before_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    payload: str,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("display command preview must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("display command preview must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("display command preview must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("display command preview must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("display command preview must not call paper lifecycle")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("malformed payload must fail before artifact write")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    payload_path = tmp_path / "malformed-display-command-payload.json"
    payload_path.write_text(payload, encoding="utf-8")
    preview_path = tmp_path / "display-command-preview.json"

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _build_paper_session_display_command_preview_args(
                display_payload_json_path=payload_path,
                preview_json_output_path=preview_path,
            )
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert not preview_path.exists()
    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.parametrize(
    "omitted",
    ("display_payload_json_path", "preview_json_output_path"),
)
def test_build_paper_session_display_command_preview_requires_explicit_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    omitted: str,
) -> None:
    calls: list[str] = []

    def forbidden_read_text(self, *_args: object, **_kwargs: object) -> str:
        calls.append(str(self))
        raise AssertionError("payload must not be read when required paths are absent")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("artifact must not be written when paths are absent")

    monkeypatch.setattr(cli.Path, "read_text", forbidden_read_text)
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    kwargs = {
        "display_payload_json_path": tmp_path / "display-payload.json",
        "preview_json_output_path": tmp_path / "display-command-preview.json",
    }
    kwargs[omitted] = OMIT

    with pytest.raises(SystemExit) as exc_info:
        cli.main(_build_paper_session_display_command_preview_args(**kwargs))

    assert exc_info.value.code == 2
    assert calls == []


def test_build_paper_session_display_command_preview_has_no_forbidden_runtime_behavior() -> None:
    builder_source = (
        inspect.getsource(cli._run_build_paper_session_display_command_preview)
        + inspect.getsource(cli._paper_session_display_command_preview_json)
    )
    lowered = builder_source.lower()

    assert "_paper_session_report_path_from_display_command_payload" in builder_source
    assert "_write_json_artifact" in builder_source
    assert "shlex.join" in builder_source
    assert "_run_render_paper_session_report" not in builder_source
    assert "json.loads" not in builder_source
    assert "run_real_data_research_route" not in builder_source
    assert "run_paper_lifecycle" not in builder_source
    assert "InMemoryLedger" not in builder_source
    assert "SQLiteLedger" not in builder_source
    assert "RiseXObservationAdapter" not in builder_source
    assert "HyperliquidObservationAdapter" not in builder_source
    assert "apps.live_runner" not in builder_source
    assert "core.execution" not in builder_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "order_placement" not in lowered
    assert "aggregate" not in lowered
    assert "pnl" not in lowered


def test_parse_paper_session_display_command_text_writes_rx062_fixture(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("command text parser must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("command text parser must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("command text parser must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("command text parser must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("command text parser must not call paper lifecycle")

    def forbidden_render(
        _args: object,
        _parser: object,
    ) -> None:
        calls.append("render")
        raise AssertionError("command text parser must not render reports")

    def forbidden_preview(**_kwargs: object) -> dict[str, object]:
        calls.append("preview")
        raise AssertionError("command text parser must not build previews")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route", forbidden_runner)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)
    monkeypatch.setattr(cli, "_run_render_paper_session_report", forbidden_render)
    monkeypatch.setattr(
        cli,
        "_run_render_paper_session_report_from_payload",
        forbidden_render,
    )
    monkeypatch.setattr(cli, "_paper_session_display_command_preview_json", forbidden_preview)

    report_path = tmp_path / "missing paper session report with spaces.json"
    command_text_path = tmp_path / "display command text with spaces.txt"
    display_payload_path = tmp_path / "display payload with spaces.json"
    command_text = (
        "paper-session-report-display --session-report-json-path "
        f"{shlex.quote(str(report_path))}"
    )
    args = _parse_paper_session_display_command_text_args(
        tmp_path,
        command_text,
        display_payload_json_path=display_payload_path,
        command_text_path=command_text_path,
    )

    original_read_text = cli.Path.read_text
    read_paths: list[str] = []

    def recording_read_text(self, *args: object, **kwargs: object) -> str:
        read_paths.append(str(self))
        if str(self) == str(report_path):
            raise AssertionError("command text parser must not read report JSON")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(cli.Path, "read_text", recording_read_text)

    assert cli.main(args) == 0
    first_payload_text = original_read_text(display_payload_path, encoding="utf-8")
    first_output = capsys.readouterr().out
    assert cli.main(args) == 0

    assert calls == []
    assert read_paths == [str(command_text_path), str(command_text_path)]
    assert original_read_text(display_payload_path, encoding="utf-8") == first_payload_text
    assert capsys.readouterr().out == first_output
    assert not report_path.exists()

    display_payload = json.loads(first_payload_text)
    assert display_payload == {
        "schema_version": 1,
        "session_report_json_path": str(report_path),
    }
    assert set(display_payload) == {"schema_version", "session_report_json_path"}
    assert (
        cli._paper_session_report_path_from_display_command_payload(first_payload_text)
        == str(report_path)
    )
    assert first_output == (
        "Paper Session Display Command Text Parser\n"
        f"command_text_path={command_text_path}\n"
        f"display_payload_json_path={display_payload_path}\n"
        f"session_report_json_path={report_path}\n"
    )

    sanitized_payload = dict(display_payload)
    sanitized_payload["session_report_json_path"] = "<session-report-path>"
    lowered_payload = json.dumps(sanitized_payload, sort_keys=True).lower()
    forbidden_fields = (
        "routes",
        "decision",
        "paper",
        "summary",
        "ledger",
        "aggregate_paper_net_profit_usd",
        "paper_net_profit_usd",
        "telegram",
        "webhook",
        "token",
        "credential",
        "secret",
        "api_key",
        "private",
        "account",
        "balance",
        "order_payload",
        "sendable",
        "live",
        "pnl",
        '"net_profit_usd": 0',
        '"expected_funding_usd": 0',
        '"total_fees_usd": 0',
    )
    for forbidden_field in forbidden_fields:
        assert forbidden_field not in lowered_payload


@pytest.mark.parametrize(
    "command_text",
    (
        "",
        "paper-session-report-display",
        "paper-session-report-display --session-report-json-path",
        "paper-session-report-display --session-report-json-path ''",
        "paper-session-report-display --session-report-json-path=/tmp/report.json",
        "paper-session-report-display /tmp/report.json --session-report-json-path",
        "paper-session-report-display --wrong-flag /tmp/report.json",
        "paper-session-report-display --session-report-json-path /tmp/report.json extra",
        "paper-session-report-display --session-report-json-path /tmp/report.json --chat-id 1",
        "paper-session-report-display --session-report-json-path /tmp/report.json --route-id route-1",
        "paper-session-report-display --session-report-json-path /tmp/report.json --net-profit-usd 0",
        "render-paper-session-report --session-report-json-path /tmp/report.json",
        "paper-trade-session --routes-json-path /tmp/routes.json",
        "paper-session-report-display --session-report-json-path '/tmp/report.json",
    ),
)
def test_parse_paper_session_display_command_text_rejects_malformed_text_before_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    command_text: str,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("command text parser must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("command text parser must not construct adapters")

    class ForbiddenLedger:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            calls.append("ledger")
            raise AssertionError("command text parser must not instantiate ledgers")

    def forbidden_runner(**_kwargs: object) -> DecisionResult:
        calls.append("runner")
        raise AssertionError("command text parser must not run sessions")

    def forbidden_lifecycle(**_kwargs: object) -> object:
        calls.append("paper_lifecycle")
        raise AssertionError("command text parser must not call paper lifecycle")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("malformed command text must fail before artifact write")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "InMemoryLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "SQLiteLedger", ForbiddenLedger)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)
    monkeypatch.setattr(cli, "run_paper_lifecycle", forbidden_lifecycle)
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    display_payload_path = tmp_path / "display-payload.json"

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _parse_paper_session_display_command_text_args(
                tmp_path,
                command_text,
                display_payload_json_path=display_payload_path,
            )
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert not display_payload_path.exists()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_parse_paper_session_display_command_text_rejects_payload_parser_failure_before_artifact(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    def failing_display_payload_validator(_payload_text: str) -> str:
        calls.append("display_payload_validator")
        raise cli.argparse.ArgumentTypeError("display payload parser failed")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("parser failure must fail before artifact write")

    monkeypatch.setattr(
        cli,
        "_paper_session_report_path_from_display_command_payload",
        failing_display_payload_validator,
    )
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    report_path = tmp_path / "paper-session-report.json"
    display_payload_path = tmp_path / "display-payload.json"
    command_text = (
        "paper-session-report-display --session-report-json-path "
        f"{shlex.quote(str(report_path))}"
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _parse_paper_session_display_command_text_args(
                tmp_path,
                command_text,
                display_payload_json_path=display_payload_path,
            )
        )

    assert exc_info.value.code == 2
    assert calls == ["display_payload_validator"]
    assert not display_payload_path.exists()
    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.parametrize(
    "omitted",
    ("command_text_path", "display_payload_json_path"),
)
def test_parse_paper_session_display_command_text_requires_explicit_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    omitted: str,
) -> None:
    calls: list[str] = []

    def forbidden_read_text(self, *_args: object, **_kwargs: object) -> str:
        calls.append(str(self))
        raise AssertionError("command text must not be read when paths are absent")

    def forbidden_artifact_write(_path: str, _payload: object) -> None:
        calls.append("artifact_write")
        raise AssertionError("artifact must not be written when paths are absent")

    monkeypatch.setattr(cli.Path, "read_text", forbidden_read_text)
    monkeypatch.setattr(cli, "_write_json_artifact", forbidden_artifact_write)

    args = ["parse-paper-session-display-command-text"]
    if omitted != "command_text_path":
        args.extend(
            [
                "--paper-session-display-command-text-path",
                str(tmp_path / "display-command.txt"),
            ]
        )
    if omitted != "display_payload_json_path":
        args.extend(["--display-payload-json-path", str(tmp_path / "payload.json")])

    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)

    assert exc_info.value.code == 2
    assert calls == []


def test_parse_paper_session_display_command_text_has_no_forbidden_runtime_behavior() -> None:
    parser_source = inspect.getsource(cli._run_parse_paper_session_display_command_text)
    lowered = parser_source.lower()

    assert "_paper_session_display_command_payload_from_command_text" in parser_source
    assert "_paper_session_report_path_from_display_command_payload" in parser_source
    assert "_write_json_artifact" in parser_source
    assert "_run_render_paper_session_report" not in parser_source
    assert "_paper_session_display_command_preview_json" not in parser_source
    assert "run_real_data_research_route" not in parser_source
    assert "run_paper_lifecycle" not in parser_source
    assert "InMemoryLedger" not in parser_source
    assert "SQLiteLedger" not in parser_source
    assert "RiseXObservationAdapter" not in parser_source
    assert "HyperliquidObservationAdapter" not in parser_source
    assert "apps.live_runner" not in parser_source
    assert "core.execution" not in parser_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "order_placement" not in lowered
    assert "aggregate" not in lowered
    assert "pnl" not in lowered


def test_render_paper_session_report_renderer_has_no_forbidden_runtime_behavior() -> None:
    renderer_source = "".join(
        inspect.getsource(getattr(cli, name))
        for name in (
            "_run_render_paper_session_report",
            "_paper_session_report_display_lines",
            "_validated_paper_session_report_display_values",
            "_paper_report_mapping",
            "_paper_report_list",
            "_paper_report_int",
            "_paper_report_string",
            "_paper_report_bool",
            "_paper_report_economics_value",
            "_paper_report_economics_field",
        )
    )
    lowered = renderer_source.lower()

    assert "read_text" in renderer_source
    assert "write_text" not in renderer_source
    assert "run_real_data_research_route" not in renderer_source
    assert "run_paper_lifecycle" not in renderer_source
    assert "InMemoryLedger" not in renderer_source
    assert "SQLiteLedger" not in renderer_source
    assert "RiseXObservationAdapter" not in renderer_source
    assert "HyperliquidObservationAdapter" not in renderer_source
    assert "apps.live_runner" not in renderer_source
    assert "core.execution" not in renderer_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "order_placement" not in lowered


def test_build_paper_session_package_writes_deterministic_local_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("builder must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("builder must not construct adapters")

    def forbidden_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("runner")
        raise AssertionError("builder must not run paper sessions")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_runner)

    routes = [
        _paper_session_route(route_id="package-route-001", capture_id="package-cap-001"),
        _paper_session_route(
            route_id="package-route-002",
            capture_id="package-cap-002",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]
    routes_output_path = tmp_path / "operator routes with spaces.json"
    preview_output_path = tmp_path / "operator-preview.json"
    intended_report_path = tmp_path / "operator session report with spaces.json"
    args = _paper_session_package_args(
        tmp_path,
        {"routes": routes},
        routes_json_output_path=routes_output_path,
        preview_json_output_path=preview_output_path,
        session_report_json_path=intended_report_path,
    )

    assert cli.main(args) == 0
    first_route_artifact = routes_output_path.read_text(encoding="utf-8")
    first_preview_artifact = preview_output_path.read_text(encoding="utf-8")
    capsys.readouterr()
    assert cli.main(args) == 0
    assert routes_output_path.read_text(encoding="utf-8") == first_route_artifact
    assert preview_output_path.read_text(encoding="utf-8") == first_preview_artifact

    assert calls == []
    assert not intended_report_path.exists()
    assert json.loads(first_route_artifact) == routes
    assert cli._paper_session_routes_from_json_path(str(routes_output_path))[0][
        0
    ].route_id == "package-route-001"

    preview = json.loads(first_preview_artifact)
    assert preview == {
        "preview": "Paper Trade Session Operator Package",
        "schema_version": 1,
        "route_count": 2,
        "route_ids": ["package-route-001", "package-route-002"],
        "routes_json_path": str(routes_output_path),
        "session_report_json_path": str(intended_report_path),
        "manual_command": {
            "argv": [
                "python3",
                "-m",
                "apps.cli.main",
                "paper-trade-session",
                "--routes-json-path",
                str(routes_output_path),
                "--session-report-json-path",
                str(intended_report_path),
            ],
            "text": (
                "python3 -m apps.cli.main paper-trade-session "
                f"--routes-json-path '{routes_output_path}' "
                f"--session-report-json-path '{intended_report_path}'"
            ),
        },
    }

    sanitized_preview = dict(preview)
    sanitized_preview["routes_json_path"] = "<operator-routes-path>"
    sanitized_preview["session_report_json_path"] = "<operator-report-path>"
    sanitized_preview["manual_command"] = {
        "argv": [
            "<python>",
            "-m",
            "apps.cli.main",
            "paper-trade-session",
            "--routes-json-path",
            "<operator-routes-path>",
            "--session-report-json-path",
            "<operator-report-path>",
        ],
        "text": (
            "python3 -m apps.cli.main paper-trade-session "
            "--routes-json-path <operator-routes-path> "
            "--session-report-json-path <operator-report-path>"
        ),
    }
    combined_artifacts = (
        json.dumps(json.loads(first_route_artifact), sort_keys=True)
        + "\n"
        + json.dumps(sanitized_preview, sort_keys=True)
    )
    forbidden_fields = (
        "entry_ev",
        "decision",
        "summary",
        "ledger",
        "aggregate_paper_net_profit_usd",
        "paper_net_profit_usd",
        "telegram",
        "webhook",
        "token",
        "credential",
        "secret",
        "api_key",
        "private",
        "account",
        "balance",
        "order_payload",
        "sendable",
        "live",
        "pnl",
        '"net_profit_usd": 0',
        '"expected_funding_usd": 0',
        '"total_fees_usd": 0',
    )
    lowered_artifacts = combined_artifacts.lower()
    for forbidden_field in forbidden_fields:
        assert forbidden_field not in lowered_artifacts

    assert capsys.readouterr().out == (
        "Paper Session Operator Package\n"
        "route_count=2\n"
        "route_ids=package-route-001,package-route-002\n"
        f"routes_json_path={routes_output_path}\n"
        f"preview_json_path={preview_output_path}\n"
        f"session_report_json_path={intended_report_path}\n"
    )


@pytest.mark.parametrize(
    "payload",
    (
        {"routes": []},
        {"routes": [_paper_session_route(mode="DISCOVERY")]},
        {"routes": [{**_paper_session_route(), "watchlist": "BTC"}]},
        {"routes": [_paper_session_route(target_notional_usd="NaN")]},
        {"routes": [_paper_session_route(assembled_at="2026-08-13T12:00:00")]},
        {"command": "paper-trade-session", "routes": [_paper_session_route()]},
        [
            _paper_session_route(route_id=f"package-route-{index}")
            for index in range(cli._MAX_PAPER_SESSION_ROUTES + 1)
        ],
    ),
)
def test_build_paper_session_package_rejects_malformed_payload_before_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    payload: object,
) -> None:
    calls: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            calls.append("risex_adapter")
            raise AssertionError("builder must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            calls.append("hedge_adapter")
            raise AssertionError("builder must not construct adapters")

    def forbidden_report_runner(**_kwargs: object) -> tuple[DecisionResult, object]:
        calls.append("report_runner")
        raise AssertionError("builder must not run sessions")

    monkeypatch.setattr(cli, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(cli, "HyperliquidObservationAdapter", ForbiddenHyperliquidAdapter)
    monkeypatch.setattr(cli, "run_real_data_research_route_with_snapshot", forbidden_report_runner)

    routes_output_path = tmp_path / "operator-routes.json"
    preview_output_path = tmp_path / "operator-preview.json"
    intended_report_path = tmp_path / "operator-session-report.json"

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _paper_session_package_args(
                tmp_path,
                payload,
                routes_json_output_path=routes_output_path,
                preview_json_output_path=preview_output_path,
                session_report_json_path=intended_report_path,
            )
        )

    assert exc_info.value.code == 2
    assert calls == []
    assert not routes_output_path.exists()
    assert not preview_output_path.exists()
    assert not intended_report_path.exists()


@pytest.mark.parametrize(
    "omitted",
    (
        "routes_json_output_path",
        "preview_json_output_path",
        "session_report_json_path",
    ),
)
def test_build_paper_session_package_requires_explicit_output_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    omitted: str,
) -> None:
    calls: list[str] = []

    def forbidden_parser(_payload_text: str) -> list[dict[str, str]]:
        calls.append("parser")
        raise AssertionError("payload must not be parsed when required paths are absent")

    monkeypatch.setattr(cli, "_paper_session_route_list_from_command_payload", forbidden_parser)

    kwargs = {
        "routes_json_output_path": tmp_path / "operator-routes.json",
        "preview_json_output_path": tmp_path / "operator-preview.json",
        "session_report_json_path": tmp_path / "operator-session-report.json",
    }
    kwargs[omitted] = OMIT

    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            _paper_session_package_args(
                tmp_path,
                {"routes": [_paper_session_route()]},
                **kwargs,
            )
        )

    assert exc_info.value.code == 2
    assert calls == []


def test_build_paper_session_package_builder_has_no_forbidden_runtime_behavior() -> None:
    package_source = (
        inspect.getsource(cli._run_build_paper_session_package)
        + inspect.getsource(cli._paper_session_package_preview_json)
    )
    lowered = package_source.lower()

    assert "_paper_session_route_list_from_command_payload" in package_source
    assert "run_real_data_research_route" not in package_source
    assert "run_paper_lifecycle" not in package_source
    assert "InMemoryLedger" not in package_source
    assert "SQLiteLedger" not in package_source
    assert "RiseXObservationAdapter" not in package_source
    assert "HyperliquidObservationAdapter" not in package_source
    assert "paper_session_report_json" not in package_source
    assert "apps.live_runner" not in package_source
    assert "core.execution" not in package_source
    assert "reconciliation" not in lowered
    assert "replay" not in lowered
    assert "telegram" not in lowered
    assert "webhook" not in lowered
    assert "token" not in lowered
    assert "credential" not in lowered
    assert "secret" not in lowered
    assert "api_key" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "urllib" not in lowered
    assert "socket" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
    assert "aggregate" not in lowered
    assert "pnl" not in lowered


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
