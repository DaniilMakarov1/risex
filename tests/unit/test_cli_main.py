from __future__ import annotations

import inspect
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

import apps.cli.main as cli
from core.domain.contracts import DecisionResult, RouteCandidate
from core.domain.enums import EvaluationMode, RejectReason, RouteStatus


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
