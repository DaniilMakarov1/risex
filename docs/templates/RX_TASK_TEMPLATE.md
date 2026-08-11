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
- State the worker policy: `workers forbidden`, `workers optional`, or `one supervised worker required`.
- Require one supervised worker/subagent for non-trivial architecture-sensitive tasks, including live-gate, accounting, reconciliation, execution-boundary, ledger, safety-critical, broad contract, owner-boundary, or repository-governance tasks.
- For required-worker tasks, state whether the worker is required for design support only or for implementation support, and list the questions the worker must answer at DESIGN CHECKPOINT.
- State that the worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- State that the worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- State that Parent owns steering, final diff review, validation, commit, push, and final report.
- State that the worker must not commit, push, merge, approve work, or start unrelated scope.
- State that Parent must stop before edits if a required worker is unavailable.

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
