from __future__ import annotations

import json
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


def test_paper_trade_session_runtime_smoke_uses_deterministic_adapters_and_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    observed_at = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    funding_settlement_at = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)
    report_path = tmp_path / "paper-session-smoke-report.json"
    ledger_path = tmp_path / "paper-session-smoke-ledger.sqlite"
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
