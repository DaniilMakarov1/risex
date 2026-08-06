import re
from pathlib import Path


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


def test_business_logic_function_definitions_stay_in_single_owner_modules() -> None:
    expected_owners = {
        "calculate_total_fees_usd": Path("core/economics/fees.py"),
        "calculate_total_expected_funding_usd": Path("core/economics/funding.py"),
        "calculate_executable_quote": Path("core/economics/liquidity.py"),
        "calculate_current_unwind_pnl_usd": Path("core/economics/basis.py"),
        "calculate_entry_ev": Path("core/economics/ev.py"),
        "evaluate_route": Path("core/pipeline/evaluate.py"),
    }

    for function_name, expected_path in expected_owners.items():
        definitions = [
            path
            for path in _production_python_files()
            if re.search(rf"^def {function_name}\(", path.read_text(), flags=re.MULTILINE)
        ]
        assert definitions == [expected_path]
