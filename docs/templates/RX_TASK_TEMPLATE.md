# RX Task Template

## Task ID

RX-000 - Short task name

## Objective

State the concrete outcome for this one task. Do not include strategy changes or unrelated follow-up work.

## Starting baseline

Start from `main @ <commit_sha>`.

## Branch

Create and work on `task/rx-000-short-name`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, or HEAD does not match the stated baseline.

Read:

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Allowed scope

- List every file or directory this task may change.

## Forbidden scope

- No product behavior changes unless this task explicitly requires them.
- No route evaluation changes unless this task explicitly requires them.
- No economics changes unless this task explicitly requires them.
- No risk gate changes unless this task explicitly requires them.
- No domain contract changes unless this task explicitly requires them.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No new route statuses.
- No new RejectReason values.
- No canary architecture.
- No broad refactors.
- No speculative helpers or future hooks.

## Implementation requirements

- List the exact implementation constraints for this task.
- State which owner module owns any changed business logic.
- State whether workers are allowed or required.
- State that workers must use the checkpoint protocol when used.

## Required files

- List the files expected to change or be created.

## Required tests

- `python scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- `git status --short`

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
- Orchestration log
- Next suggested task
