## Task ID

RX-Q001 — Repository Workflow and Quality Guardrails

## Objective

Add repository-level workflow and quality guardrails so future Codex sessions follow supervised-worker protocol, avoid unnecessary abstractions, complete NEXT_TASK.md consistently, and preserve RiseX architecture boundaries.

## Allowed scope

- AGENTS.md
- docs/WORKFLOW.md
- docs/templates/RX_TASK_TEMPLATE.md
- docs/templates/RX_REPORT_TEMPLATE.md
- docs/templates/WORKER_CHECKPOINT_TEMPLATE.md
- docs/templates/REVIEW_CHECKLIST.md
- scripts/validate_next_task.py
- tests/invariant/test_next_task_template.py
- tests/invariant/test_no_forbidden_imports.py
- .github/PULL_REQUEST_TEMPLATE.md
- .github/workflows/ci.yml only if needed to run the new validator
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Forbidden scope

- No product behavior changes.
- No route evaluation changes.
- No economics changes.
- No risk gate changes.
- No domain contract changes unless strictly needed for docs/tests, which should not be needed.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No new route statuses.
- No new RejectReason values.
- No canary architecture.
- No broad refactors.
- No speculative helpers or future hooks.

## Required files

- AGENTS.md
- docs/WORKFLOW.md
- docs/templates/RX_TASK_TEMPLATE.md
- docs/templates/RX_REPORT_TEMPLATE.md
- docs/templates/WORKER_CHECKPOINT_TEMPLATE.md
- docs/templates/REVIEW_CHECKLIST.md
- scripts/validate_next_task.py
- tests/invariant/test_next_task_template.py
- tests/invariant/test_no_forbidden_imports.py
- .github/PULL_REQUEST_TEMPLATE.md
- .github/workflows/ci.yml
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Required tests

- python scripts/validate_next_task.py
- python3 -m pytest tests/invariant
- python3 -m pytest
- python3 -m compileall apps core storage tests scripts
- python3 -m apps.cli.main
- git diff --check
- git diff --cached --check
- git status --short

## Required report format

Return one fenced Markdown code block with no prose outside.

Include:

- Task ID
- Repository path
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- New functions/classes/contracts added and why each was necessary
- Tests run
- Exact test results
- Working-tree status
- Known limitations
- Risk impact
- Orchestration log, if workers were used
- Next suggested task
