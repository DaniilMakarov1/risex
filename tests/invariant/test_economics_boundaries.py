import re
from pathlib import Path
from typing import get_type_hints

from core.domain.contracts import VenueObservation
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


def test_business_logic_function_definitions_stay_in_single_owner_modules() -> None:
    expected_owners = {
        "calculate_total_fees_usd": Path("core/economics/fees.py"),
        "calculate_total_expected_funding_usd": Path("core/economics/funding.py"),
        "calculate_executable_quote": Path("core/economics/liquidity.py"),
        "calculate_current_unwind_pnl_usd": Path("core/economics/basis.py"),
        "calculate_entry_ev": Path("core/economics/ev.py"),
        "evaluate_route": Path("core/pipeline/evaluate.py"),
        "assemble_route_snapshot": Path("core/pipeline/snapshot.py"),
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
        Path("snapshot.py"),
    }


def test_offline_scan_orchestration_does_not_import_business_logic_or_execution() -> None:
    offline_scan_source = Path("core/pipeline/offline_scan.py").read_text()

    assert "core.economics" not in offline_scan_source
    assert "core.risk" not in offline_scan_source
    assert "core.execution" not in offline_scan_source
    assert "apps.paper_runner" not in offline_scan_source
    assert "apps.live_runner" not in offline_scan_source
    assert "def evaluate_route(" not in offline_scan_source
    assert "def assemble_route_snapshot(" not in offline_scan_source


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


def test_no_real_adapters_secrets_persistence_or_dashboard_code_are_introduced() -> None:
    production_text = "\n".join(path.read_text().lower() for path in _production_python_files())
    venue_python_files = {path.relative_to(Path("core/venues")) for path in Path("core/venues").rglob("*.py")}
    dashboard_python_files = tuple(Path("apps/dashboard").rglob("*.py"))
    storage_python_files = {path.relative_to(Path("storage")) for path in Path("storage").rglob("*.py")}

    assert venue_python_files == {Path("__init__.py"), Path("base.py")}
    assert all(path.name == "__init__.py" and path.read_text() == "" for path in dashboard_python_files)
    assert storage_python_files == {Path("__init__.py"), Path("sqlite/__init__.py")}
    assert "api_key" not in production_text
    assert "secret_key" not in production_text
    assert "private_key" not in production_text


def test_no_scan_watchlist_or_stale_rx004_archive_code_is_introduced() -> None:
    production_paths = tuple(path.as_posix().lower() for path in _production_python_files())
    production_text = "\n".join(path.read_text().lower() for path in _production_python_files())

    assert not Path("archive").exists()
    assert not any("rx-004-scan-refresh" in path for path in production_paths)
    assert not any("watchlist" in path for path in production_paths)
    assert "broad_scan" not in production_text
    assert "focused_refresh" not in production_text
    assert "watchlist" not in production_text
