# RiseX Repository Workflow

This repository uses one RX task per Codex session and one task branch per RX task. The workflow exists to preserve the capture-centric architecture, keep live trading disabled by default, and prevent unrelated refactors from entering task branches.

## Roles

### Parent Codex

- Owns task scope, branch creation, architecture checks, final diff review, validation, commit, push, and final report.
- Reads `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md` before edits.
- Stops before edits when the checkout is dirty, the remote is unexpected, the branch is wrong, or the starting HEAD does not match the task prompt.
- Keeps implementation inside the task's allowed scope and refuses forbidden product, trading, adapter, network, secret, route-status, reject-reason, or architecture changes.
- Updates `STATUS.md`, `DECISIONS.md` when needed, and `NEXT_TASK.md` before final validation.

### Worker

- May assist only on non-trivial tasks and only under Parent supervision.
- Must not commit, push, merge, change branch strategy, approve work, or start unrelated work.
- Must stop at each required checkpoint:
  - DESIGN CHECKPOINT before edits.
  - CODE CHECKPOINT after implementation.
  - TEST CHECKPOINT after tests are added or changed.
  - VALIDATION CHECKPOINT after commands run.
- Must report files changed, contracts changed, tests added, validation results, limitations, and any forbidden scope avoided.

### Reviewer

- Reviews the task branch after Parent validation and push.
- Accepts, rejects, or requests fixes.
- Is the only role that can mark a task accepted.
- Reviewer acceptance updates the accepted baseline on `main`; implementation completion on a task branch is not acceptance.

## Branch Discipline

- Start each new RX task from the stated baseline on `main`.
- Never implement on `main`.
- Use `task/rx-NNN-short-name` for task branches unless the task prompt gives an exact branch name.
- Push only the assigned task branch.
- Do not merge to `main` without reviewer acceptance.

## Scope Discipline

- Keep changes to the task's allowed files.
- Do not make product behavior changes during governance, docs, CI, or template tasks.
- Do not add broad refactors, speculative helpers, placeholder live paths, duplicate owner modules, or future hooks.
- A new abstraction is allowed only when it is required by the current task, belongs to the authoritative owner module, is used immediately, and is covered by tests.

## NEXT_TASK.md Discipline

`NEXT_TASK.md` is the handoff contract for the next Codex session. It must:

- Contain exactly one next task.
- Include every required section from `docs/templates/RX_TASK_TEMPLATE.md`.
- Avoid duplicate task definitions.
- Pass `python scripts/validate_next_task.py`.

The current task may be implementation-complete and pending review, but it must not be written as accepted until reviewer acceptance is explicit.

## Required Validation

Run these before final report unless the task prompt adds stricter commands:

```bash
python scripts/validate_next_task.py
python3 -m pytest tests/invariant
python3 -m pytest
python3 -m compileall apps core storage tests scripts
python3 -m apps.cli.main
git diff --check
git diff --cached --check
git status --short
```

## Final Report

Return one fenced Markdown code block with no prose outside. Use `docs/templates/RX_REPORT_TEMPLATE.md` and include the orchestration log even when no workers were used.
