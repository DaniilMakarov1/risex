from __future__ import annotations

import json
import shlex
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import apps.cli.main as cli
from core.accounting.ledger import LedgerEventType
from core.domain.contracts import (
    EstimatedValue,
    FeeComponent,
    FeeModel,
    OrderBook,
    OrderBookLevel,
    VenueObservation,
)
from core.domain.enums import ValueSource
from core.economics.fees import (
    PUBLIC_FEE_ACCOUNT_SCOPE_KEY,
    PUBLIC_FEE_METADATA_KIND_KEY,
    PUBLIC_FEE_METADATA_SOURCE_KEY,
    PUBLIC_FEE_TAKER_BPS_METADATA_KEY,
)
from core.economics.funding import (
    PUBLIC_FUNDING_RATE_METADATA_KEY,
    PUBLIC_FUNDING_RATE_SOURCE_METADATA_KEY,
)
from storage.sqlite.ledger import SQLiteLedger


BASE_SESSION_ROUTE = {
    "route_id": "session-smoke-started",
    "capture_id": "capture-smoke-started",
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


def _paper_session_route(**overrides: object) -> dict[str, str]:
    values = dict(BASE_SESSION_ROUTE)
    values.update(overrides)
    return {key: str(value) for key, value in values.items()}


def _paper_session_args(
    tmp_path,
    routes_payload: object,
    *,
    ledger_sqlite_path: object,
    session_report_json_path: object,
) -> list[str]:
    routes_path = tmp_path / "paper-session-smoke-routes.json"
    routes_path.write_text(json.dumps(routes_payload), encoding="utf-8")
    return [
        "paper-trade-session",
        "--routes-json-path",
        str(routes_path),
        "--ledger-sqlite-path",
        str(ledger_sqlite_path),
        "--session-report-json-path",
        str(session_report_json_path),
    ]


def _order_book(
    *,
    venue: str,
    symbol: str,
    bid: str,
    ask: str,
) -> OrderBook:
    return OrderBook(
        venue=venue,
        symbol=symbol,
        bids=(OrderBookLevel(price=Decimal(bid), size=Decimal("10")),),
        asks=(OrderBookLevel(price=Decimal(ask), size=Decimal("10")),),
    )


def _funding_value(public_rate: str | None) -> EstimatedValue:
    metadata = {}
    if public_rate is not None:
        metadata = {
            PUBLIC_FUNDING_RATE_METADATA_KEY: public_rate,
            PUBLIC_FUNDING_RATE_SOURCE_METADATA_KEY: ValueSource.OBSERVED.value,
        }
    return EstimatedValue(
        value=None,
        source=ValueSource.UNKNOWN,
        description="test-only public funding fixture",
        metadata=metadata,
    )


def _fee_model(public_taker_bps: str | None) -> FeeModel:
    metadata = {}
    if public_taker_bps is not None:
        metadata = {
            PUBLIC_FEE_METADATA_SOURCE_KEY: ValueSource.OBSERVED.value,
            PUBLIC_FEE_METADATA_KIND_KEY: "fee_rate_fields",
            PUBLIC_FEE_ACCOUNT_SCOPE_KEY: "account_independent",
            PUBLIC_FEE_TAKER_BPS_METADATA_KEY: public_taker_bps,
            f"{PUBLIC_FEE_TAKER_BPS_METADATA_KEY}_field": "taker_fee_bps",
            f"{PUBLIC_FEE_TAKER_BPS_METADATA_KEY}_container": "fixture",
        }
    return FeeModel(
        components=(
            FeeComponent(
                name="fixture_fee_cash_flow_unknown",
                amount_usd=EstimatedValue(
                    value=None,
                    source=ValueSource.UNKNOWN,
                    description="test-only public fee fixture",
                    metadata=metadata,
                ),
            ),
        )
    )


def _observation(
    *,
    venue: str,
    symbol: str,
    observed_at: datetime,
    funding_settlement_at: datetime,
    bid: str,
    ask: str,
    public_funding_rate: str | None,
    public_taker_bps: str | None,
) -> VenueObservation:
    return VenueObservation(
        venue=venue,
        symbol=symbol,
        observed_at=observed_at,
        order_book=_order_book(venue=venue, symbol=symbol, bid=bid, ask=ask),
        expected_funding_usd=_funding_value(public_funding_rate),
        funding_settlement_at=funding_settlement_at,
        fees=_fee_model(public_taker_bps),
    )


def _assert_string_or_none(value: object) -> None:
    assert value is None or isinstance(value, str)


def _install_deterministic_public_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, str]]:
    observed_at = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    funding_settlement_at = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
    adapter_calls: list[tuple[str, str]] = []

    risex_observations = {
        "BTC-PERP": _observation(
            venue="RiseX",
            symbol="BTC-PERP",
            observed_at=observed_at,
            funding_settlement_at=funding_settlement_at,
            bid="100",
            ask="100",
            public_funding_rate="-0.004",
            public_taker_bps="5",
        ),
        "ETH-PERP": _observation(
            venue="RiseX",
            symbol="ETH-PERP",
            observed_at=observed_at,
            funding_settlement_at=funding_settlement_at,
            bid="50",
            ask="50",
            public_funding_rate=None,
            public_taker_bps=None,
        ),
    }
    hedge_observations = {
        "BTC": _observation(
            venue="Hyperliquid",
            symbol="BTC",
            observed_at=observed_at,
            funding_settlement_at=funding_settlement_at,
            bid="100",
            ask="100",
            public_funding_rate="0.012",
            public_taker_bps="5",
        ),
        "ETH": _observation(
            venue="Hyperliquid",
            symbol="ETH",
            observed_at=observed_at,
            funding_settlement_at=funding_settlement_at,
            bid="50",
            ask="50",
            public_funding_rate=None,
            public_taker_bps=None,
        ),
    }

    class DeterministicRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            adapter_calls.append(("RiseX", "__init__"))

        def fetch_observation(self, symbol: str) -> VenueObservation:
            adapter_calls.append(("RiseX", symbol))
            return risex_observations[symbol]

    class DeterministicHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            adapter_calls.append(("Hyperliquid", "__init__"))

        def fetch_observation(self, symbol: str) -> VenueObservation:
            adapter_calls.append(("Hyperliquid", symbol))
            return hedge_observations[symbol]

    monkeypatch.setattr(cli, "RiseXObservationAdapter", DeterministicRiseXAdapter)
    monkeypatch.setattr(
        cli,
        "HyperliquidObservationAdapter",
        DeterministicHyperliquidAdapter,
    )
    return adapter_calls


def test_paper_trade_session_runtime_smoke_uses_deterministic_adapters_and_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    report_path = tmp_path / "paper-session-smoke-report.json"
    ledger_path = tmp_path / "paper-session-smoke-ledger.sqlite"
    adapter_calls = _install_deterministic_public_adapters(monkeypatch)

    routes_payload = [
        _paper_session_route(),
        _paper_session_route(
            route_id="session-smoke-unknown",
            capture_id="capture-smoke-unknown",
            risex_symbol="ETH-PERP",
            hedge_symbol="ETH",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]

    assert (
        cli.main(
            _paper_session_args(
                tmp_path,
                routes_payload,
                ledger_sqlite_path=ledger_path,
                session_report_json_path=report_path,
            )
        )
        == 0
    )

    output = capsys.readouterr().out
    assert output == (
        "Paper Trade Session\n"
        "route_count=2\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=1\n"
        "Paper Trade Route\n"
        "route_id=session-smoke-started\n"
        "capture_id=capture-smoke-started\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_TRADING_DISABLED\n"
        "decision.net_profit_usd=7.0000\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=True\n"
        "paper_start_attribution=entry_paper_eligible_decision\n"
        "paper_start_blockers=None\n"
        "ledger_event_count=4\n"
        "ledger_event_sequences=1,2,3,4\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed\n"
        "paper.expected_funding_usd=8.000\n"
        "paper.total_fees_usd=1.0000\n"
        "paper.simulated_roundtrip_cost_usd=0\n"
        "paper.net_profit_usd=7.0000\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=2\n"
        "Paper Trade Route\n"
        "route_id=session-smoke-unknown\n"
        "capture_id=capture-smoke-unknown\n"
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
        f"ledger_path={ledger_path}\n"
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
        f"ledger_path={ledger_path}\n"
    )
    assert "aggregate_paper_net_profit_usd=0" not in output
    assert "paper.net_profit_usd=0" not in output
    assert adapter_calls == [
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "BTC-PERP"),
        ("Hyperliquid", "BTC"),
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "ETH-PERP"),
        ("Hyperliquid", "ETH"),
    ]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["session"] == {
        "ledger_path": str(ledger_path),
        "route_count": 2,
    }
    assert report["summary"] == {
        "aggregate_paper_net_profit_usd": None,
        "decision_net_profit_known": 1,
        "decision_net_profit_unknown": 1,
        "decision_status": {
            "LIVE_ELIGIBLE": 0,
            "PAPER_ELIGIBLE": 1,
            "REJECTED": 1,
            "RESEARCH_ONLY": 0,
        },
        "entry_ev_known": 1,
        "entry_ev_unknown": 1,
        "ledger_event_count": 6,
        "ledger_event_sequences": [1, 2, 3, 4, 5, 6],
        "ledger_event_types": [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_REJECTION_RECORDED.value,
        ],
        "ledger_path": str(ledger_path),
        "paper_expected_funding_known": 1,
        "paper_expected_funding_unknown": 1,
        "paper_net_profit_known": 1,
        "paper_net_profit_unknown": 1,
        "paper_not_started": 1,
        "paper_started": 1,
        "paper_total_fees_known": 1,
        "paper_total_fees_unknown": 1,
        "routes_total": 2,
        "routes_with_snapshot": 2,
        "routes_without_snapshot": 0,
    }
    assert "aggregate_paper_pnl_usd" not in report["summary"]

    started_route, unknown_route = report["routes"]
    assert started_route["decision"]["status"] == "PAPER_ELIGIBLE"
    assert started_route["decision"]["net_profit_usd"] == "7.0000"
    assert started_route["decision"]["entry_ev"] == {
        "expected_funding_usd": "8.000",
        "net_profit_usd": "7.0000",
        "simulated_roundtrip_cost_usd": "0",
        "total_fees_usd": "1.0000",
    }
    assert started_route["paper"]["started"] is True
    assert started_route["paper"]["net_profit_usd"] == "7.0000"
    assert [event["event_type"] for event in started_route["ledger_events"]] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_CAPTURE_OPENED.value,
        LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
        LedgerEventType.PAPER_CAPTURE_CLOSED.value,
    ]

    assert unknown_route["decision"]["status"] == "REJECTED"
    assert unknown_route["decision"]["net_profit_usd"] is None
    assert unknown_route["decision"]["entry_ev"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "total_fees_usd": None,
    }
    assert unknown_route["paper"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "start_attribution": "paper_start_blocked_by_decision",
        "start_blockers": ["decision_status_not_paper_eligible"],
        "started": False,
        "total_fees_usd": None,
    }
    assert [event["event_type"] for event in unknown_route["ledger_events"]] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_REJECTION_RECORDED.value,
    ]

    for route_report in report["routes"]:
        economics = (
            route_report["decision"]["net_profit_usd"],
            *route_report["decision"]["entry_ev"].values(),
            route_report["paper"]["expected_funding_usd"],
            route_report["paper"]["total_fees_usd"],
            route_report["paper"]["simulated_roundtrip_cost_usd"],
            route_report["paper"]["net_profit_usd"],
        )
        for value in economics:
            _assert_string_or_none(value)

    reopened = SQLiteLedger(ledger_path)
    try:
        assert [event.event_type for event in reopened.records()] == [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_REJECTION_RECORDED.value,
        ]
    finally:
        reopened.close()


def test_paper_session_package_output_feeds_runtime_report_and_display_smoke(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    routes_output_path = tmp_path / "package runtime routes.json"
    preview_output_path = tmp_path / "package-runtime-preview.json"
    report_path = tmp_path / "package runtime report.json"
    ledger_path = tmp_path / "package-runtime-ledger.sqlite"
    command_payload_path = tmp_path / "package-runtime-command-payload.json"
    adapter_calls = _install_deterministic_public_adapters(monkeypatch)

    routes = [
        _paper_session_route(
            route_id="package-runtime-started",
            capture_id="capture-package-runtime-started",
        ),
        _paper_session_route(
            route_id="package-runtime-unknown",
            capture_id="capture-package-runtime-unknown",
            risex_symbol="ETH-PERP",
            hedge_symbol="ETH",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]
    command_payload_path.write_text(
        json.dumps({"routes": routes}),
        encoding="utf-8",
    )

    assert (
        cli.main(
            [
                "build-paper-session-package",
                "--paper-session-command-payload-json-path",
                str(command_payload_path),
                "--routes-json-output-path",
                str(routes_output_path),
                "--preview-json-output-path",
                str(preview_output_path),
                "--session-report-json-path",
                str(report_path),
            ]
        )
        == 0
    )
    assert adapter_calls == []
    assert not report_path.exists()
    assert not ledger_path.exists()
    assert capsys.readouterr().out == (
        "Paper Session Operator Package\n"
        "route_count=2\n"
        "route_ids=package-runtime-started,package-runtime-unknown\n"
        f"routes_json_path={routes_output_path}\n"
        f"preview_json_path={preview_output_path}\n"
        f"session_report_json_path={report_path}\n"
    )

    generated_routes = json.loads(routes_output_path.read_text(encoding="utf-8"))
    assert generated_routes == routes
    assert all(set(route) == set(BASE_SESSION_ROUTE) for route in generated_routes)
    parsed_generated_routes = cli._paper_session_routes_from_json_path(
        str(routes_output_path)
    )
    assert [route.route_id for route, _assembled_at in parsed_generated_routes] == [
        "package-runtime-started",
        "package-runtime-unknown",
    ]

    preview = json.loads(preview_output_path.read_text(encoding="utf-8"))
    expected_package_command = [
        "python3",
        "-m",
        "apps.cli.main",
        "paper-trade-session",
        "--routes-json-path",
        str(routes_output_path),
        "--session-report-json-path",
        str(report_path),
    ]
    assert preview == {
        "preview": "Paper Trade Session Operator Package",
        "schema_version": 1,
        "route_count": 2,
        "route_ids": ["package-runtime-started", "package-runtime-unknown"],
        "routes_json_path": str(routes_output_path),
        "session_report_json_path": str(report_path),
        "manual_command": {
            "argv": expected_package_command,
            "text": shlex.join(expected_package_command),
        },
    }
    preview_text = json.dumps(preview, sort_keys=True)
    assert "ledger_events" not in preview_text
    assert "aggregate_paper_net_profit_usd" not in preview_text
    assert "paper_net_profit_usd" not in preview_text

    assert (
        cli.main(
            [
                "paper-trade-session",
                "--routes-json-path",
                str(routes_output_path),
                "--ledger-sqlite-path",
                str(ledger_path),
                "--session-report-json-path",
                str(report_path),
            ]
        )
        == 0
    )
    runtime_output = capsys.readouterr().out
    assert runtime_output == (
        "Paper Trade Session\n"
        "route_count=2\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=1\n"
        "Paper Trade Route\n"
        "route_id=package-runtime-started\n"
        "capture_id=capture-package-runtime-started\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_TRADING_DISABLED\n"
        "decision.net_profit_usd=7.0000\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=True\n"
        "paper_start_attribution=entry_paper_eligible_decision\n"
        "paper_start_blockers=None\n"
        "ledger_event_count=4\n"
        "ledger_event_sequences=1,2,3,4\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed\n"
        "paper.expected_funding_usd=8.000\n"
        "paper.total_fees_usd=1.0000\n"
        "paper.simulated_roundtrip_cost_usd=0\n"
        "paper.net_profit_usd=7.0000\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=2\n"
        "Paper Trade Route\n"
        "route_id=package-runtime-unknown\n"
        "capture_id=capture-package-runtime-unknown\n"
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
        f"ledger_path={ledger_path}\n"
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
        f"ledger_path={ledger_path}\n"
    )
    assert "aggregate_paper_net_profit_usd=0" not in runtime_output
    assert "paper.net_profit_usd=0" not in runtime_output
    assert adapter_calls == [
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "BTC-PERP"),
        ("Hyperliquid", "BTC"),
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "ETH-PERP"),
        ("Hyperliquid", "ETH"),
    ]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["session"] == {
        "ledger_path": str(ledger_path),
        "route_count": 2,
    }
    assert report["summary"] == {
        "aggregate_paper_net_profit_usd": None,
        "decision_net_profit_known": 1,
        "decision_net_profit_unknown": 1,
        "decision_status": {
            "LIVE_ELIGIBLE": 0,
            "PAPER_ELIGIBLE": 1,
            "REJECTED": 1,
            "RESEARCH_ONLY": 0,
        },
        "entry_ev_known": 1,
        "entry_ev_unknown": 1,
        "ledger_event_count": 6,
        "ledger_event_sequences": [1, 2, 3, 4, 5, 6],
        "ledger_event_types": [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_REJECTION_RECORDED.value,
        ],
        "ledger_path": str(ledger_path),
        "paper_expected_funding_known": 1,
        "paper_expected_funding_unknown": 1,
        "paper_net_profit_known": 1,
        "paper_net_profit_unknown": 1,
        "paper_not_started": 1,
        "paper_started": 1,
        "paper_total_fees_known": 1,
        "paper_total_fees_unknown": 1,
        "routes_total": 2,
        "routes_with_snapshot": 2,
        "routes_without_snapshot": 0,
    }
    assert "aggregate_paper_pnl_usd" not in report["summary"]

    started_route, unknown_route = report["routes"]
    assert started_route["route"]["route_id"] == "package-runtime-started"
    assert started_route["decision"]["status"] == "PAPER_ELIGIBLE"
    assert started_route["decision"]["net_profit_usd"] == "7.0000"
    assert started_route["decision"]["entry_ev"] == {
        "expected_funding_usd": "8.000",
        "net_profit_usd": "7.0000",
        "simulated_roundtrip_cost_usd": "0",
        "total_fees_usd": "1.0000",
    }
    assert started_route["paper"]["started"] is True
    assert started_route["paper"]["net_profit_usd"] == "7.0000"
    assert [event["event_type"] for event in started_route["ledger_events"]] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_CAPTURE_OPENED.value,
        LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
        LedgerEventType.PAPER_CAPTURE_CLOSED.value,
    ]

    assert unknown_route["route"]["route_id"] == "package-runtime-unknown"
    assert unknown_route["decision"]["status"] == "REJECTED"
    assert unknown_route["decision"]["net_profit_usd"] is None
    assert unknown_route["decision"]["entry_ev"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "total_fees_usd": None,
    }
    assert unknown_route["paper"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "start_attribution": "paper_start_blocked_by_decision",
        "start_blockers": ["decision_status_not_paper_eligible"],
        "started": False,
        "total_fees_usd": None,
    }
    assert [event["event_type"] for event in unknown_route["ledger_events"]] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_REJECTION_RECORDED.value,
    ]

    for route_report in report["routes"]:
        economics = (
            route_report["decision"]["net_profit_usd"],
            *route_report["decision"]["entry_ev"].values(),
            route_report["paper"]["expected_funding_usd"],
            route_report["paper"]["total_fees_usd"],
            route_report["paper"]["simulated_roundtrip_cost_usd"],
            route_report["paper"]["net_profit_usd"],
        )
        for value in economics:
            _assert_string_or_none(value)

    reopened = SQLiteLedger(ledger_path)
    try:
        assert [event.event_type for event in reopened.records()] == [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_REJECTION_RECORDED.value,
        ]
    finally:
        reopened.close()

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
    display_output = capsys.readouterr().out
    assert display_output == (
        "Paper Session Report Display\n"
        "route_count=2\n"
        "route_ids=package-runtime-started,package-runtime-unknown\n"
        "route.1.route_id=package-runtime-started\n"
        "route.1.decision_status=PAPER_ELIGIBLE\n"
        "route.1.paper_started=true\n"
        "route.1.decision_net_profit_usd=7.0000\n"
        "route.1.decision_entry_ev_expected_funding_usd=8.000\n"
        "route.1.decision_entry_ev_total_fees_usd=1.0000\n"
        "route.1.decision_entry_ev_simulated_roundtrip_cost_usd=0\n"
        "route.1.decision_entry_ev_net_profit_usd=7.0000\n"
        "route.1.paper_expected_funding_usd=8.000\n"
        "route.1.paper_total_fees_usd=1.0000\n"
        "route.1.paper_simulated_roundtrip_cost_usd=0\n"
        "route.1.paper_net_profit_usd=7.0000\n"
        "route.2.route_id=package-runtime-unknown\n"
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
    assert "aggregate_paper_net_profit_usd=0" not in display_output
    assert "route.2.paper_net_profit_usd=0" not in display_output


def test_paper_session_operator_display_artifact_chain_end_to_end_smoke(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    routes_output_path = tmp_path / "operator display routes.json"
    package_preview_path = tmp_path / "operator-display-package-preview.json"
    report_path = tmp_path / "operator display report.json"
    ledger_path = tmp_path / "operator-display-ledger.sqlite"
    command_payload_path = tmp_path / "operator-display-command-payload.json"
    display_payload_path = tmp_path / "operator-display-payload.json"
    display_preview_path = tmp_path / "operator-display-preview.json"
    command_text_path = tmp_path / "operator-display-command.txt"
    command_text_preview_path = tmp_path / "operator-display-command-preview.json"
    parsed_payload_path = tmp_path / "operator-display-parsed-payload.json"
    adapter_calls = _install_deterministic_public_adapters(monkeypatch)

    routes = [
        _paper_session_route(
            route_id="operator-display-started",
            capture_id="capture-operator-display-started",
        ),
        _paper_session_route(
            route_id="operator-display-unknown",
            capture_id="capture-operator-display-unknown",
            risex_symbol="ETH-PERP",
            hedge_symbol="ETH",
            assembled_at="2026-08-13T12:01:00+00:00",
        ),
    ]
    command_payload_path.write_text(
        json.dumps({"routes": routes}),
        encoding="utf-8",
    )
    assert command_payload_path.exists()

    assert (
        cli.main(
            [
                "build-paper-session-package",
                "--paper-session-command-payload-json-path",
                str(command_payload_path),
                "--routes-json-output-path",
                str(routes_output_path),
                "--preview-json-output-path",
                str(package_preview_path),
                "--session-report-json-path",
                str(report_path),
            ]
        )
        == 0
    )
    assert adapter_calls == []
    assert not report_path.exists()
    assert not ledger_path.exists()
    assert capsys.readouterr().out == (
        "Paper Session Operator Package\n"
        "route_count=2\n"
        "route_ids=operator-display-started,operator-display-unknown\n"
        f"routes_json_path={routes_output_path}\n"
        f"preview_json_path={package_preview_path}\n"
        f"session_report_json_path={report_path}\n"
    )

    generated_routes = json.loads(routes_output_path.read_text(encoding="utf-8"))
    assert generated_routes == routes
    assert all(set(route) == set(BASE_SESSION_ROUTE) for route in generated_routes)
    parsed_generated_routes = cli._paper_session_routes_from_json_path(
        str(routes_output_path)
    )
    assert [route.route_id for route, _assembled_at in parsed_generated_routes] == [
        "operator-display-started",
        "operator-display-unknown",
    ]

    expected_package_command = [
        "python3",
        "-m",
        "apps.cli.main",
        "paper-trade-session",
        "--routes-json-path",
        str(routes_output_path),
        "--session-report-json-path",
        str(report_path),
    ]
    package_preview = json.loads(package_preview_path.read_text(encoding="utf-8"))
    assert package_preview == {
        "preview": "Paper Trade Session Operator Package",
        "schema_version": 1,
        "route_count": 2,
        "route_ids": ["operator-display-started", "operator-display-unknown"],
        "routes_json_path": str(routes_output_path),
        "session_report_json_path": str(report_path),
        "manual_command": {
            "argv": expected_package_command,
            "text": shlex.join(expected_package_command),
        },
    }
    package_preview_text = json.dumps(package_preview, sort_keys=True)
    assert "ledger_events" not in package_preview_text
    assert "aggregate_paper_net_profit_usd" not in package_preview_text
    assert "paper_net_profit_usd" not in package_preview_text

    assert (
        cli.main(
            [
                "paper-trade-session",
                "--routes-json-path",
                str(routes_output_path),
                "--ledger-sqlite-path",
                str(ledger_path),
                "--session-report-json-path",
                str(report_path),
            ]
        )
        == 0
    )
    runtime_output = capsys.readouterr().out
    assert runtime_output == (
        "Paper Trade Session\n"
        "route_count=2\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=1\n"
        "Paper Trade Route\n"
        "route_id=operator-display-started\n"
        "capture_id=capture-operator-display-started\n"
        "mode=ENTRY\n"
        "status=PAPER_ELIGIBLE\n"
        "reasons=LIVE_TRADING_DISABLED\n"
        "decision.net_profit_usd=7.0000\n"
        "snapshot=AVAILABLE\n"
        "funding_settlement_at=2026-08-13T16:00:00+00:00\n"
        "paper_started=True\n"
        "paper_start_attribution=entry_paper_eligible_decision\n"
        "paper_start_blockers=None\n"
        "ledger_event_count=4\n"
        "ledger_event_sequences=1,2,3,4\n"
        "ledger_event_types=route_decision,paper_capture_opened,"
        "paper_settlement_observed,paper_capture_closed\n"
        "paper.expected_funding_usd=8.000\n"
        "paper.total_fees_usd=1.0000\n"
        "paper.simulated_roundtrip_cost_usd=0\n"
        "paper.net_profit_usd=7.0000\n"
        f"ledger_path={ledger_path}\n"
        "session_route_index=2\n"
        "Paper Trade Route\n"
        "route_id=operator-display-unknown\n"
        "capture_id=capture-operator-display-unknown\n"
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
        f"ledger_path={ledger_path}\n"
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
        f"ledger_path={ledger_path}\n"
    )
    assert "aggregate_paper_net_profit_usd=0" not in runtime_output
    assert "paper.net_profit_usd=0" not in runtime_output
    assert adapter_calls == [
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "BTC-PERP"),
        ("Hyperliquid", "BTC"),
        ("RiseX", "__init__"),
        ("Hyperliquid", "__init__"),
        ("RiseX", "ETH-PERP"),
        ("Hyperliquid", "ETH"),
    ]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["session"] == {
        "ledger_path": str(ledger_path),
        "route_count": 2,
    }
    assert report["summary"]["aggregate_paper_net_profit_usd"] is None
    assert "aggregate_paper_pnl_usd" not in report["summary"]
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
    assert report["summary"]["ledger_event_sequences"] == [1, 2, 3, 4, 5, 6]
    assert report["summary"]["ledger_event_types"] == [
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_CAPTURE_OPENED.value,
        LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
        LedgerEventType.PAPER_CAPTURE_CLOSED.value,
        LedgerEventType.ROUTE_DECISION_RECORDED.value,
        LedgerEventType.PAPER_REJECTION_RECORDED.value,
    ]

    started_route, unknown_route = report["routes"]
    assert started_route["route"]["route_id"] == "operator-display-started"
    assert started_route["decision"]["status"] == "PAPER_ELIGIBLE"
    assert started_route["decision"]["entry_ev"] == {
        "expected_funding_usd": "8.000",
        "net_profit_usd": "7.0000",
        "simulated_roundtrip_cost_usd": "0",
        "total_fees_usd": "1.0000",
    }
    assert started_route["paper"]["started"] is True
    assert started_route["paper"]["net_profit_usd"] == "7.0000"

    assert unknown_route["route"]["route_id"] == "operator-display-unknown"
    assert unknown_route["decision"]["status"] == "REJECTED"
    assert unknown_route["decision"]["entry_ev"] == {
        "expected_funding_usd": None,
        "net_profit_usd": None,
        "simulated_roundtrip_cost_usd": None,
        "total_fees_usd": None,
    }
    assert unknown_route["paper"]["started"] is False
    assert unknown_route["paper"]["net_profit_usd"] is None

    for route_report in report["routes"]:
        economics = (
            route_report["decision"]["net_profit_usd"],
            *route_report["decision"]["entry_ev"].values(),
            route_report["paper"]["expected_funding_usd"],
            route_report["paper"]["total_fees_usd"],
            route_report["paper"]["simulated_roundtrip_cost_usd"],
            route_report["paper"]["net_profit_usd"],
        )
        for value in economics:
            _assert_string_or_none(value)

    reopened = SQLiteLedger(ledger_path)
    try:
        assert [event.event_type for event in reopened.records()] == [
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_CAPTURE_OPENED.value,
            LedgerEventType.PAPER_SETTLEMENT_OBSERVED.value,
            LedgerEventType.PAPER_CAPTURE_CLOSED.value,
            LedgerEventType.ROUTE_DECISION_RECORDED.value,
            LedgerEventType.PAPER_REJECTION_RECORDED.value,
        ]
    finally:
        reopened.close()

    assert (
        cli.main(
            [
                "build-paper-session-display-payload",
                "--session-report-json-path",
                str(report_path),
                "--display-payload-json-path",
                str(display_payload_path),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        f"display_payload_json_path={display_payload_path}\n"
        f"session_report_json_path={report_path}\n"
    )
    assert json.loads(display_payload_path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "session_report_json_path": str(report_path),
    }

    assert (
        cli.main(
            [
                "build-paper-session-display-command-preview",
                "--paper-session-display-command-payload-json-path",
                str(display_payload_path),
                "--preview-json-output-path",
                str(display_preview_path),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "Paper Session Display Command Preview\n"
        f"display_payload_json_path={display_payload_path}\n"
        f"preview_json_path={display_preview_path}\n"
    )
    expected_display_command = [
        "python3",
        "-m",
        "apps.cli.main",
        "render-paper-session-report-from-payload",
        "--paper-session-display-command-payload-json-path",
        str(display_payload_path),
    ]
    display_preview = json.loads(display_preview_path.read_text(encoding="utf-8"))
    assert display_preview == {
        "preview": "Paper Session Display Command Preview",
        "schema_version": 1,
        "display_payload_json_path": str(display_payload_path),
        "manual_command": {
            "argv": expected_display_command,
            "text": shlex.join(expected_display_command),
        },
    }
    display_preview_text = json.dumps(display_preview, sort_keys=True)
    assert "ledger" not in display_preview_text
    assert "aggregate_paper_net_profit_usd" not in display_preview_text
    assert "paper_net_profit_usd" not in display_preview_text

    command_text = (
        "paper-session-report-display --session-report-json-path "
        f"{shlex.quote(str(report_path))}"
    )
    command_text_path.write_text(command_text, encoding="utf-8")
    assert command_text_path.read_text(encoding="utf-8") == command_text

    assert (
        cli.main(
            [
                "build-paper-session-display-command-text-preview",
                "--paper-session-display-command-text-path",
                str(command_text_path),
                "--display-payload-json-path",
                str(parsed_payload_path),
                "--preview-json-output-path",
                str(command_text_preview_path),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "Paper Session Display Command Text Preview\n"
        f"command_text_path={command_text_path}\n"
        f"intended_display_payload_json_path={parsed_payload_path}\n"
        f"preview_json_path={command_text_preview_path}\n"
        f"session_report_json_path={report_path}\n"
    )
    assert not parsed_payload_path.exists()
    expected_parser_command = [
        "python3",
        "-m",
        "apps.cli.main",
        "parse-paper-session-display-command-text",
        "--paper-session-display-command-text-path",
        str(command_text_path),
        "--display-payload-json-path",
        str(parsed_payload_path),
    ]
    command_text_preview = json.loads(
        command_text_preview_path.read_text(encoding="utf-8")
    )
    assert command_text_preview == {
        "schema_version": 1,
        "command_text_fixture_path": str(command_text_path),
        "intended_display_payload_json_path": str(parsed_payload_path),
        "normalized_session_report_json_path": str(report_path),
        "manual_command": {
            "argv": expected_parser_command,
            "text": shlex.join(expected_parser_command),
        },
    }
    command_text_preview_text = json.dumps(command_text_preview, sort_keys=True)
    assert "ledger" not in command_text_preview_text
    assert "aggregate_paper_net_profit_usd" not in command_text_preview_text
    assert "paper_net_profit_usd" not in command_text_preview_text

    assert (
        cli.main(
            [
                "parse-paper-session-display-command-text",
                "--paper-session-display-command-text-path",
                str(command_text_path),
                "--display-payload-json-path",
                str(parsed_payload_path),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "Paper Session Display Command Text Parser\n"
        f"command_text_path={command_text_path}\n"
        f"display_payload_json_path={parsed_payload_path}\n"
        f"session_report_json_path={report_path}\n"
    )
    assert json.loads(parsed_payload_path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "session_report_json_path": str(report_path),
    }

    assert (
        cli.main(
            [
                "render-paper-session-report-from-payload",
                "--paper-session-display-command-payload-json-path",
                str(parsed_payload_path),
            ]
        )
        == 0
    )
    payload_backed_display_output = capsys.readouterr().out
    assert payload_backed_display_output == (
        "Paper Session Report Display\n"
        "route_count=2\n"
        "route_ids=operator-display-started,operator-display-unknown\n"
        "route.1.route_id=operator-display-started\n"
        "route.1.decision_status=PAPER_ELIGIBLE\n"
        "route.1.paper_started=true\n"
        "route.1.decision_net_profit_usd=7.0000\n"
        "route.1.decision_entry_ev_expected_funding_usd=8.000\n"
        "route.1.decision_entry_ev_total_fees_usd=1.0000\n"
        "route.1.decision_entry_ev_simulated_roundtrip_cost_usd=0\n"
        "route.1.decision_entry_ev_net_profit_usd=7.0000\n"
        "route.1.paper_expected_funding_usd=8.000\n"
        "route.1.paper_total_fees_usd=1.0000\n"
        "route.1.paper_simulated_roundtrip_cost_usd=0\n"
        "route.1.paper_net_profit_usd=7.0000\n"
        "route.2.route_id=operator-display-unknown\n"
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
    assert "aggregate_paper_net_profit_usd=0" not in payload_backed_display_output
    assert "route.2.paper_net_profit_usd=0" not in payload_backed_display_output
