import importlib.util
from pathlib import Path


def _load_validator():
    path = Path("scripts/validate_next_task.py")
    spec = importlib.util.spec_from_file_location("validate_next_task", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_next_task = _load_validator()


def _valid_next_task_text() -> str:
    return """# Next Task

## Task ID

RX-012 - Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

## Objective

Add deterministic offline evidence bundle governance for the next live-gate task.

## Starting baseline

Start from `main @ <reviewer_accepted_head>`.

## Branch

Create and work on `task/rx-012-live-gate-evidence-bundle`.

## Allowed scope

- `core/risk/gates.py`

## Forbidden scope

- No live runner behavior.

## Implementation requirements

- Preserve the single route decision path.

## Required files

- `core/risk/gates.py`

## Required tests

- `python scripts/validate_next_task.py`

## Required report format

Return one fenced Markdown code block with no prose outside.
"""


def test_current_next_task_passes_validator() -> None:
    assert validate_next_task.validate_file(Path("NEXT_TASK.md")) == []


def test_validator_rejects_missing_required_sections() -> None:
    invalid_text = _valid_next_task_text().replace(
        "## Required tests\n\n- `python scripts/validate_next_task.py`\n\n",
        "",
    )

    errors = validate_next_task.validate_text(invalid_text)

    assert "Missing required section: Required tests." in errors


def test_validator_rejects_duplicate_task_id_sections() -> None:
    invalid_text = _valid_next_task_text() + "\n## Task ID\n\nRX-013 - Duplicate task\n"

    errors = validate_next_task.validate_text(invalid_text)

    assert "Duplicate section: Task ID." in errors
    assert any("exactly one task definition" in error for error in errors)


def test_validator_rejects_multiple_task_definitions() -> None:
    invalid_text = _valid_next_task_text().replace(
        "## Objective",
        "RX-013 - Duplicate task\n\n## Objective",
    )

    errors = validate_next_task.validate_text(invalid_text)

    assert "NEXT_TASK.md must contain exactly one task definition; found 2." in errors


def test_validator_rejects_empty_task_id_section() -> None:
    invalid_text = _valid_next_task_text().replace(
        "RX-012 - Offline Live Gate Evidence Bundle Design and Fake Replay Coverage",
        "",
    )

    errors = validate_next_task.validate_text(invalid_text)

    assert "Required section is empty: Task ID." in errors
    assert "Task ID section must contain exactly one non-empty task definition line." in errors


def test_task_template_contains_required_sections() -> None:
    template = Path("docs/templates/RX_TASK_TEMPLATE.md").read_text()

    for section in validate_next_task.REQUIRED_SECTIONS:
        assert f"## {section}" in template


def test_report_and_worker_templates_preserve_role_boundaries() -> None:
    workflow = Path("docs/WORKFLOW.md").read_text()
    report_template = Path("docs/templates/RX_REPORT_TEMPLATE.md").read_text()
    worker_template = Path("docs/templates/WORKER_CHECKPOINT_TEMPLATE.md").read_text()
    review_checklist = Path("docs/templates/REVIEW_CHECKLIST.md").read_text()

    for required_text in ("Parent Codex", "Worker", "Reviewer", "NEXT_TASK.md"):
        assert required_text in workflow

    assert "New functions/classes/contracts added and why each was necessary" in report_template
    assert "Orchestration log" in report_template
    assert "DESIGN CHECKPOINT" in worker_template
    assert "CODE CHECKPOINT" in worker_template
    assert "TEST CHECKPOINT" in worker_template
    assert "VALIDATION CHECKPOINT" in worker_template
    assert "No second route model" in review_checklist


def test_ci_runs_next_task_validator_and_compileall_includes_scripts() -> None:
    ci = Path(".github/workflows/ci.yml").read_text()

    assert "python scripts/validate_next_task.py" in ci
    assert "python -m compileall apps core storage tests scripts" in ci
