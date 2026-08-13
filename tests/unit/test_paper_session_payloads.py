from __future__ import annotations

import argparse
import inspect
import json

import pytest

from apps.cli import paper_session_payloads as payloads
from core.domain.contracts import RouteCandidate
from core.domain.enums import EvaluationMode


def _paper_session_route(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "route_id": "payload-route-001",
        "capture_id": "payload-capture-001",
        "risex_venue": "RiseX",
        "risex_symbol": "BTC-PERP",
        "risex_side": "buy",
        "hedge_venue": "Hyperliquid",
        "hedge_symbol": "BTC",
        "hedge_side": "sell",
        "target_notional_usd": "500.00",
        "mode": "ENTRY",
        "assembled_at": "2026-08-13T12:00:00+00:00",
    }
    values.update(overrides)
    return values


def test_paper_session_command_payload_converts_to_route_list_shape() -> None:
    route_fixture = _paper_session_route()

    parsed = payloads.paper_session_route_list_from_command_payload(
        json.dumps({"routes": [route_fixture]})
    )

    assert parsed == [route_fixture]
    assert set(parsed[0]) == payloads.PAPER_SESSION_ROUTE_FIELDS
    route_inputs = payloads.validate_paper_session_route_list(
        parsed,
        payload_name="routes-json-path",
    )
    route, assembled_at = route_inputs[0]
    assert isinstance(route, RouteCandidate)
    assert route.route_id == "payload-route-001"
    assert route.capture_id == "payload-capture-001"
    assert route.risex_venue == "RiseX"
    assert route.risex_symbol == "BTC-PERP"
    assert route.risex_entry_side == "buy"
    assert route.hedge_venue == "Hyperliquid"
    assert route.hedge_symbol == "BTC"
    assert route.hedge_entry_side == "sell"
    assert str(route.target_notional_usd) == "500.00"
    assert assembled_at.isoformat() == "2026-08-13T12:00:00+00:00"


def test_paper_session_command_payload_accepts_exact_25_entry_routes() -> None:
    routes = [
        _paper_session_route(
            route_id=f"payload-route-{index:02d}",
            capture_id=f"payload-capture-{index:02d}",
        )
        for index in range(1, payloads.MAX_PAPER_SESSION_ROUTES + 1)
    ]

    parsed = payloads.paper_session_route_list_from_command_payload(json.dumps(routes))

    assert len(parsed) == payloads.MAX_PAPER_SESSION_ROUTES
    assert [route["route_id"] for route in parsed] == [
        f"payload-route-{index:02d}"
        for index in range(1, payloads.MAX_PAPER_SESSION_ROUTES + 1)
    ]
    assert all(route["mode"] == EvaluationMode.ENTRY.value for route in parsed)
    assert all(set(route) == payloads.PAPER_SESSION_ROUTE_FIELDS for route in parsed)


@pytest.mark.parametrize(
    "payload",
    (
        "",
        "{not-json",
        json.dumps({"routes": []}),
        json.dumps(
            [
                _paper_session_route(
                    route_id=f"payload-route-{index:02d}",
                    capture_id=f"payload-capture-{index:02d}",
                )
                for index in range(1, payloads.MAX_PAPER_SESSION_ROUTES + 2)
            ]
        ),
        json.dumps({"command": "paper-trade-session", "routes": [_paper_session_route()]}),
        json.dumps({"routes": [{**_paper_session_route(), "watchlist": "BTC"}]}),
        json.dumps(
            {
                "routes": [
                    {
                        key: value
                        for key, value in _paper_session_route().items()
                        if key != "route_id"
                    }
                ]
            }
        ),
        json.dumps({"routes": [_paper_session_route(mode="DISCOVERY")]}),
        json.dumps({"routes": [_paper_session_route(risex_venue="WrongVenue")]}),
        json.dumps({"routes": [_paper_session_route(hedge_venue="WrongVenue")]}),
        json.dumps({"routes": [_paper_session_route(hedge_side="buy")]}),
        json.dumps({"routes": [_paper_session_route(target_notional_usd="NaN")]}),
        json.dumps({"routes": [_paper_session_route(target_notional_usd=500)]}),
        json.dumps({"routes": [_paper_session_route(assembled_at="2026-08-13T12:00:00")]}),
        json.dumps({"routes": [_paper_session_route(entry_ev=None)]}),
        json.dumps({"routes": [_paper_session_route(aggregate_paper_net_profit_usd=None)]}),
    ),
)
def test_paper_session_command_payload_rejects_malformed_payloads(
    monkeypatch: pytest.MonkeyPatch,
    payload: str,
) -> None:
    constructed_adapters: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_adapters.append("risex")
            raise AssertionError("parser must not construct a RiseX adapter")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_adapters.append("hyperliquid")
            raise AssertionError("parser must not construct a Hyperliquid adapter")

    monkeypatch.setattr(payloads, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(
        payloads,
        "HyperliquidObservationAdapter",
        ForbiddenHyperliquidAdapter,
    )

    with pytest.raises(argparse.ArgumentTypeError):
        payloads.paper_session_route_list_from_command_payload(payload)

    assert constructed_adapters == []


def test_paper_session_command_payload_does_not_emit_economics_or_pnl_fields() -> None:
    parsed = payloads.paper_session_route_list_from_command_payload(
        json.dumps({"routes": [_paper_session_route()]})
    )

    assert parsed == [_paper_session_route()]
    route_payload = parsed[0]
    assert "entry_ev" not in route_payload
    assert "paper" not in route_payload
    assert "summary" not in route_payload
    assert "decision_net_profit_usd" not in route_payload
    assert "paper_net_profit_usd" not in route_payload
    assert "aggregate_paper_net_profit_usd" not in route_payload


def test_paper_session_display_command_payload_normalizes_report_path() -> None:
    parsed = payloads.paper_session_report_path_from_display_command_payload(
        json.dumps(
            {
                "schema_version": 1,
                "session_report_json_path": "  /tmp/paper-session-report.json  ",
            }
        )
    )

    assert parsed == "/tmp/paper-session-report.json"


def test_paper_session_display_command_text_builds_rx062_payload() -> None:
    parsed = payloads.paper_session_display_command_payload_from_command_text(
        "paper-session-report-display --session-report-json-path "
        "/tmp/paper-session-report.json"
    )

    assert parsed == {
        "schema_version": 1,
        "session_report_json_path": "/tmp/paper-session-report.json",
    }
    assert set(parsed) == {"schema_version", "session_report_json_path"}
    assert (
        payloads.paper_session_report_path_from_display_command_payload(
            json.dumps(parsed, sort_keys=True)
        )
        == "/tmp/paper-session-report.json"
    )


def test_paper_session_display_command_text_accepts_quoted_path_with_spaces() -> None:
    parsed = payloads.paper_session_display_command_payload_from_command_text(
        "paper-session-report-display --session-report-json-path "
        "'/tmp/paper session report.json'"
    )

    assert parsed == {
        "schema_version": 1,
        "session_report_json_path": "/tmp/paper session report.json",
    }


def test_paper_session_display_command_text_validates_generated_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator_calls: list[str] = []

    def recording_validator(payload_text: str) -> str:
        validator_calls.append(payload_text)
        return "/tmp/paper-session-report.json"

    monkeypatch.setattr(
        payloads,
        "paper_session_report_path_from_display_command_payload",
        recording_validator,
    )

    parsed = payloads.paper_session_display_command_payload_from_command_text(
        "paper-session-report-display --session-report-json-path "
        "/tmp/paper-session-report.json"
    )

    assert parsed == {
        "schema_version": 1,
        "session_report_json_path": "/tmp/paper-session-report.json",
    }
    assert len(validator_calls) == 1
    assert json.loads(validator_calls[0]) == parsed


def test_paper_session_display_command_text_rejects_validator_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mismatching_validator(_payload_text: str) -> str:
        return "/tmp/other-report.json"

    monkeypatch.setattr(
        payloads,
        "paper_session_report_path_from_display_command_payload",
        mismatching_validator,
    )

    with pytest.raises(argparse.ArgumentTypeError):
        payloads.paper_session_display_command_payload_from_command_text(
            "paper-session-report-display --session-report-json-path "
            "/tmp/paper-session-report.json"
        )


@pytest.mark.parametrize(
    "command_text",
    (
        "",
        "paper-session-report-display",
        "paper-session-report-display --session-report-json-path",
        "paper-session-report-display --session-report-json-path ''",
        "paper-session-report-display --session-report-json-path   ",
        "paper-session-report-display --session-report-json-path=/tmp/report.json",
        "--session-report-json-path /tmp/report.json",
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
def test_paper_session_display_command_text_rejects_malformed_commands(
    monkeypatch: pytest.MonkeyPatch,
    command_text: str,
) -> None:
    constructed_adapters: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_adapters.append("risex")
            raise AssertionError("command text parser must not construct adapters")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_adapters.append("hyperliquid")
            raise AssertionError("command text parser must not construct adapters")

    monkeypatch.setattr(payloads, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(
        payloads,
        "HyperliquidObservationAdapter",
        ForbiddenHyperliquidAdapter,
    )

    with pytest.raises(argparse.ArgumentTypeError):
        payloads.paper_session_display_command_payload_from_command_text(command_text)

    assert constructed_adapters == []


def test_paper_session_display_command_text_parser_has_no_side_effect_behavior() -> None:
    source = inspect.getsource(
        payloads.paper_session_display_command_payload_from_command_text
    )
    lowered = source.lower()

    assert "shlex.split" in source
    assert "paper_session_report_path_from_display_command_payload" in source
    assert "read_text" not in source
    assert "write_text" not in source
    assert "run_paper_lifecycle" not in source
    assert "run_real_data_research_route" not in source
    assert "InMemoryLedger" not in source
    assert "SQLiteLedger" not in source
    assert "RiseXObservationAdapter" not in source
    assert "HyperliquidObservationAdapter" not in source
    assert "aggregate" not in lowered
    assert "pnl" not in lowered
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


@pytest.mark.parametrize(
    "payload",
    (
        "",
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
        json.dumps(
            {
                "schema_version": 1,
                "session_report_json_path": "/tmp/report.json",
                "aggregate_paper_net_profit_usd": None,
            }
        ),
        json.dumps(
            {
                "schema_version": None,
                "session_report_json_path": "/tmp/report.json",
            }
        ),
        json.dumps(
            {
                "schema_version": True,
                "session_report_json_path": "/tmp/report.json",
            }
        ),
        json.dumps(
            {
                "schema_version": "1",
                "session_report_json_path": "/tmp/report.json",
            }
        ),
        json.dumps(
            {
                "schema_version": 2,
                "session_report_json_path": "/tmp/report.json",
            }
        ),
        json.dumps({"schema_version": 1, "session_report_json_path": None}),
        json.dumps({"schema_version": 1, "session_report_json_path": ""}),
        json.dumps({"schema_version": 1, "session_report_json_path": "   "}),
        json.dumps({"schema_version": 1, "session_report_json_path": 500}),
    ),
)
def test_paper_session_display_command_payload_rejects_malformed_payloads(
    monkeypatch: pytest.MonkeyPatch,
    payload: str,
) -> None:
    constructed_adapters: list[str] = []

    class ForbiddenRiseXAdapter:
        name = "RiseX"

        def __init__(self) -> None:
            constructed_adapters.append("risex")
            raise AssertionError("parser must not construct a RiseX adapter")

    class ForbiddenHyperliquidAdapter:
        name = "Hyperliquid"

        def __init__(self) -> None:
            constructed_adapters.append("hyperliquid")
            raise AssertionError("parser must not construct a Hyperliquid adapter")

    monkeypatch.setattr(payloads, "RiseXObservationAdapter", ForbiddenRiseXAdapter)
    monkeypatch.setattr(
        payloads,
        "HyperliquidObservationAdapter",
        ForbiddenHyperliquidAdapter,
    )

    with pytest.raises(argparse.ArgumentTypeError):
        payloads.paper_session_report_path_from_display_command_payload(payload)

    assert constructed_adapters == []


def test_paper_session_display_command_payload_parser_has_no_side_effect_behavior() -> None:
    source = inspect.getsource(
        payloads.paper_session_report_path_from_display_command_payload
    )
    lowered = source.lower()

    assert "json.loads" in source
    assert "read_text" not in source
    assert "write_text" not in source
    assert "run_paper_lifecycle" not in source
    assert "run_real_data_research_route" not in source
    assert "InMemoryLedger" not in source
    assert "SQLiteLedger" not in source
    assert "RiseXObservationAdapter" not in source
    assert "HyperliquidObservationAdapter" not in source
    assert "aggregate" not in lowered
    assert "pnl" not in lowered
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


def test_paper_session_payload_layer_has_no_forbidden_runtime_behavior() -> None:
    source = inspect.getsource(payloads)
    lowered = source.lower()

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
    assert "run_paper_lifecycle" not in source
    assert "run_real_data_research_route" not in source
    assert "InMemoryLedger" not in source
    assert "SQLiteLedger" not in source
    assert "write_text" not in source
    assert "core.execution" not in source
    assert "apps.live_runner" not in source
    assert "order_placement" not in lowered
    assert "private" not in lowered
    assert "account" not in lowered
    assert "balance" not in lowered
    assert "watchlist" not in lowered
    assert "poll" not in lowered
    assert "schedule" not in lowered
    assert "alert" not in lowered
    assert "ranking" not in lowered
