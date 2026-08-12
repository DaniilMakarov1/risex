import inspect
import re
from pathlib import Path
from typing import get_type_hints

from core.domain.contracts import LiveGateEvidenceBundle, VenueObservation
from core.pipeline.snapshot import assemble_route_snapshot_from_adapters
from core.venues.base import VenueAdapter


PRODUCTION_ROOTS = (Path("apps"), Path("core"))
SOURCE_ROOTS = (Path("apps"), Path("core"), Path("storage"), Path("tests"))


def _production_python_files() -> tuple[Path, ...]:
    return tuple(path for root in PRODUCTION_ROOTS for path in root.rglob("*.py"))


def test_canary_runner_is_not_introduced() -> None:
    assert not any("canary_runner" in path.as_posix() for root in SOURCE_ROOTS for path in root.rglob("*"))


def test_production_code_does_not_introduce_hold_or_next_cycle_states() -> None:
    production_text = "\n".join(path.read_text() for path in _production_python_files())

    assert "HOLDING_NEXT_CYCLE" not in production_text
    assert "NEXT_CYCLE" not in production_text


def test_production_code_does_not_introduce_expected_basis_change() -> None:
    production_text = "\n".join(path.read_text() for path in _production_python_files())

    assert "expected_basis_change" not in production_text


def test_evaluate_route_is_the_single_route_decision_function() -> None:
    definitions: list[Path] = []
    for path in _production_python_files():
        if re.search(r"^def evaluate_route\(", path.read_text(), flags=re.MULTILINE):
            definitions.append(path)

    assert definitions == [Path("core/pipeline/evaluate.py")]


def test_assemble_route_snapshot_is_the_single_snapshot_assembly_function() -> None:
    definitions: list[Path] = []
    for path in _production_python_files():
        if re.search(r"^def assemble_route_snapshot\(", path.read_text(), flags=re.MULTILINE):
            definitions.append(path)

    assert definitions == [Path("core/pipeline/snapshot.py")]


def test_real_market_data_handoff_delegates_without_decisions_or_second_logic() -> None:
    source = inspect.getsource(assemble_route_snapshot_from_adapters)

    assert "fetch_observation" in source
    assert "assemble_route_snapshot(" in source
    assert "evaluate_route" not in source
    assert "calculate_entry_ev" not in source
    assert "calculate_executable_quote" not in source
    assert "calculate_total_fees_usd" not in source
    assert "calculate_total_expected_funding_usd" not in source
    assert "calculate_current_unwind_pnl_usd" not in source
    assert "core.accounting" not in source
    assert "core.execution" not in source
    assert "apps.paper_runner" not in source
    assert "apps.live_runner" not in source
    assert "CapturePlan(" not in source


def test_business_logic_function_definitions_stay_in_single_owner_modules() -> None:
    expected_owners = {
        "calculate_total_fees_usd": Path("core/economics/fees.py"),
        "calculate_total_expected_funding_usd": Path("core/economics/funding.py"),
        "calculate_executable_quote": Path("core/economics/liquidity.py"),
        "calculate_current_unwind_pnl_usd": Path("core/economics/basis.py"),
        "calculate_entry_ev": Path("core/economics/ev.py"),
        "evaluate_route": Path("core/pipeline/evaluate.py"),
        "assemble_route_snapshot": Path("core/pipeline/snapshot.py"),
        "assemble_route_snapshot_from_adapters": Path("core/pipeline/snapshot.py"),
        "check_live_gate_evidence_bundle": Path("core/risk/gates.py"),
        "append_live_gate_evidence_bundle_event": Path("core/accounting/ledger.py"),
        "replay_live_gate_evidence_bundle_recording": Path(
            "core/accounting/reconciliation.py"
        ),
    }

    for function_name, expected_path in expected_owners.items():
        definitions = [
            path
            for path in _production_python_files()
            if re.search(rf"^def {function_name}\(", path.read_text(), flags=re.MULTILINE)
        ]
        assert definitions == [expected_path]


def test_business_logic_modules_stay_in_expected_files() -> None:
    assert {path.relative_to(Path("core/economics")) for path in Path("core/economics").rglob("*.py")} == {
        Path("__init__.py"),
        Path("basis.py"),
        Path("errors.py"),
        Path("ev.py"),
        Path("fees.py"),
        Path("funding.py"),
        Path("liquidity.py"),
    }
    assert {path.relative_to(Path("core/risk")) for path in Path("core/risk").rglob("*.py")} == {
        Path("__init__.py"),
        Path("gates.py"),
    }
    assert {path.relative_to(Path("core/pipeline")) for path in Path("core/pipeline").rglob("*.py")} == {
        Path("__init__.py"),
        Path("evaluate.py"),
        Path("offline_scan.py"),
        Path("scan_refresh.py"),
        Path("snapshot.py"),
    }


def test_offline_orchestration_does_not_import_business_logic_or_execution() -> None:
    orchestration_sources = (
        Path("core/pipeline/offline_scan.py").read_text(),
        Path("core/pipeline/scan_refresh.py").read_text(),
    )

    for source in orchestration_sources:
        assert "core.economics" not in source
        assert "core.risk" not in source
        assert "core.execution" not in source
        assert "core.accounting" not in source
        assert "apps.paper_runner" not in source
        assert "apps.live_runner" not in source
        assert "def evaluate_route(" not in source
        assert "def assemble_route_snapshot(" not in source


def test_scan_refresh_reuses_offline_candidate_orchestration() -> None:
    scan_refresh_source = Path("core/pipeline/scan_refresh.py").read_text()

    assert "evaluate_offline_candidates" in scan_refresh_source
    assert "assemble_route_snapshot" not in scan_refresh_source
    assert "evaluate_route" not in scan_refresh_source
    assert "calculate_entry_ev" not in scan_refresh_source
    assert "calculate_executable_quote" not in scan_refresh_source


def test_live_gate_evidence_bundle_contract_is_domain_only_and_gate_logic_is_risk_only() -> None:
    assert LiveGateEvidenceBundle.__module__ == "core.domain.contracts"

    domain_source = Path("core/domain/contracts.py").read_text()
    evaluate_source = Path("core/pipeline/evaluate.py").read_text()

    assert "class LiveGateEvidenceBundle" in domain_source
    assert "check_live_gate_evidence_bundle" not in domain_source
    assert "check_live_gate_evidence_bundle" not in evaluate_source
    assert "LiveGateEvidenceBundle" in evaluate_source


def test_venue_adapter_contract_is_per_venue_observation_only() -> None:
    adapter_source = Path("core/venues/base.py").read_text()
    return_hints = get_type_hints(VenueAdapter.fetch_observation)

    assert hasattr(VenueAdapter, "fetch_observation")
    assert not hasattr(VenueAdapter, "fetch_order_book")
    assert not hasattr(VenueAdapter, "fetch_snapshot")
    assert return_hints["return"] is VenueObservation
    assert "VenueSnapshot" not in adapter_source
    assert "fetch_order_book" not in adapter_source
    assert "fetch_snapshot" not in adapter_source


def test_only_read_only_venue_adapters_are_introduced_without_secrets_or_dashboard_code() -> None:
    production_text = "\n".join(path.read_text().lower() for path in _production_python_files())
    venue_python_files = {path.relative_to(Path("core/venues")) for path in Path("core/venues").rglob("*.py")}
    dashboard_python_files = tuple(Path("apps/dashboard").rglob("*.py"))
    storage_python_files = {path.relative_to(Path("storage")) for path in Path("storage").rglob("*.py")}

    assert venue_python_files == {
        Path("__init__.py"),
        Path("base.py"),
        Path("hyperliquid.py"),
        Path("risex.py"),
    }
    assert all(path.name == "__init__.py" and path.read_text() == "" for path in dashboard_python_files)
    assert storage_python_files == {
        Path("__init__.py"),
        Path("sqlite/__init__.py"),
        Path("sqlite/ledger.py"),
    }
    assert "api_key" not in production_text
    assert "secret_key" not in production_text
    assert "private_key" not in production_text


def test_risex_adapter_stays_read_only_observation_only() -> None:
    risex_source = Path("core/venues/risex.py").read_text()

    assert "VenueObservation" in risex_source
    assert "VenueSnapshot" not in risex_source
    assert "assemble_route_snapshot" not in risex_source
    assert "evaluate_route" not in risex_source
    assert "calculate_entry_ev" not in risex_source
    assert "calculate_executable_quote" not in risex_source
    assert "core.pipeline" not in risex_source
    assert "core.economics" not in risex_source
    assert "core.risk" not in risex_source
    assert "core.accounting" not in risex_source
    assert "core.execution" not in risex_source
    assert "apps.paper_runner" not in risex_source
    assert "apps.live_runner" not in risex_source
    assert "Hyperliquid" not in risex_source
    assert "/v1/orders" not in risex_source
    assert "/v1/auth" not in risex_source
    assert "/v1/portfolio" not in risex_source
    assert "api_key" not in risex_source.lower()
    assert "secret" not in risex_source.lower()


def test_hyperliquid_adapter_stays_read_only_observation_only() -> None:
    hyperliquid_source = Path("core/venues/hyperliquid.py").read_text()

    assert "VenueObservation" in hyperliquid_source
    assert "VenueSnapshot" not in hyperliquid_source
    assert "assemble_route_snapshot" not in hyperliquid_source
    assert "evaluate_route" not in hyperliquid_source
    assert "calculate_entry_ev" not in hyperliquid_source
    assert "calculate_executable_quote" not in hyperliquid_source
    assert "core.pipeline" not in hyperliquid_source
    assert "core.economics" not in hyperliquid_source
    assert "core.risk" not in hyperliquid_source
    assert "core.accounting" not in hyperliquid_source
    assert "core.execution" not in hyperliquid_source
    assert "apps.paper_runner" not in hyperliquid_source
    assert "apps.live_runner" not in hyperliquid_source
    assert "clearinghouseState" not in hyperliquid_source
    assert "openOrders" not in hyperliquid_source
    assert "userFills" not in hyperliquid_source
    assert "/exchange" not in hyperliquid_source
    assert "api_key" not in hyperliquid_source.lower()
    assert "secret" not in hyperliquid_source.lower()


def test_paper_runner_stays_downstream_of_route_decisions() -> None:
    paper_runner_source = Path("apps/paper_runner/lifecycle.py").read_text()

    assert "evaluate_route" not in paper_runner_source
    assert "assemble_route_snapshot" not in paper_runner_source
    assert "calculate_entry_ev" not in paper_runner_source
    assert "core.economics" not in paper_runner_source
    assert "core.risk" not in paper_runner_source
    assert "core.execution" not in paper_runner_source
    assert "apps.live_runner" not in paper_runner_source
    assert "CapturePlan(" not in paper_runner_source


def test_no_stale_rx004_archive_code_is_introduced() -> None:
    production_paths = tuple(path.as_posix().lower() for path in _production_python_files())

    assert not Path("archive").exists()
    assert not any("rx-004-scan-refresh" in path for path in production_paths)
