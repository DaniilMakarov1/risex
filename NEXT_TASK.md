# Next Task

## Task ID

RX-032 — Product Owner Roadmap Authorization Gate

## Objective

Require explicit Product Owner or Control Tower authorization before promoting any new product, execution, monitoring, adapter, or governance stage. If a concrete authorized next task is supplied, update repository handoff metadata only. If no concrete authorization is supplied, stop and report blocked without inventing a product stage.

## Starting baseline

Start from reviewer-accepted `main` after the RX-031 metadata-only follow-up is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-032-product-owner-roadmap-authorization-gate`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

Read:

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md
- docs/WORKFLOW.md
- Relevant templates in `docs/templates/`

## Allowed scope

- Repository handoff metadata required to record explicit Product Owner or Control Tower authorization for exactly one next task.
- `STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `NEXT_TASK.md`.
- `DECISIONS.md` only if the supplied authorization makes or changes an architectural or repository-governance decision.
- Validation-only changes are not allowed unless required to keep the existing handoff validator passing after metadata edits.

## Forbidden scope

- No product behavior changes.
- No dashboard behavior changes.
- No route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, or auto-refresh.
- No venue adapters, market-data calls, private endpoints, credentials, account balances, exchange account state, or network-dependent tests.
- No order placement, sendable exchange request construction, order cancellation, order status fetching, or execution automation.
- No route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, or approval-boundary execution.
- No ledger writes, storage migrations, replay changes, paper lifecycle changes, route eligibility mutation, or Capture state transitions.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No new route statuses, reject reasons, canary architecture, hold-next-cycle logic, or live trading by default.
- No new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.

## Implementation requirements

- Treat explicit Product Owner or Control Tower authorization as the only source for promoting a new task.
- Do not infer authorization from roadmap sequence, previous assistant reports, or the existence of a future-stage idea in documentation.
- If authorization supplies a concrete next task, prepare exactly one `NEXT_TASK.md` handoff for that task and keep the branch metadata-only.
- If authorization does not supply a concrete next task, stop and report blocked without editing product code or inventing a handoff.
- Preserve RX-030 as the latest accepted product task unless reviewer-accepted `main` has changed.
- Preserve RX-031 as a metadata-only review-directed follow-up unless reviewer acceptance says otherwise.
- Worker policy: workers are optional because this is metadata-only control-gate work. Use a supervised worker only if the supplied authorization requires non-trivial repository-governance changes; if a worker becomes required and unavailable, stop before edits.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `NEXT_TASK.md`
- `DECISIONS.md` only if required by an explicit architecture or repository-governance decision
- Do not touch product code.

## Required tests

- `python3 scripts/validate_next_task.py`
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
