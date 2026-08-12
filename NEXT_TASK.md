# Next Task

## Task ID

RX-031 — Review-Directed Follow-up After RX-030

## Objective

Apply only explicit reviewer-directed fixes or handoff metadata updates after the read-only monitoring dashboard branch is reviewed. Keep the prior dashboard work read-only, downstream of existing owner modules, and free of decisions, polling, ledger writes, execution automation, or orders.

## Starting baseline

Start from reviewer-accepted `main` after the prior dashboard task is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-031-review-directed-follow-up-after-rx-030`. Do not implement on `main`.

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

## Allowed scope

- Explicit reviewer-directed fixes to the read-only dashboard renderer and its focused deterministic tests.
- Repository metadata updates required to record review disposition and prepare the next single handoff.
- No product behavior changes unless the reviewer specifically directs a correction to the already-scoped dashboard display behavior.

## Forbidden scope

- No new product stage, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, or auto-refresh.
- No venue adapters, market-data calls, private endpoints, credentials, account balances, exchange account state, or network-dependent tests.
- No order placement, sendable exchange request construction, order cancellation, order status fetching, or execution automation.
- No route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, or approval-boundary execution.
- No ledger writes, storage migrations, replay changes, paper lifecycle changes, route eligibility mutation, or Capture state transitions.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No new route statuses, reject reasons, canary architecture, hold-next-cycle logic, or live trading by default.

## Implementation requirements

- Treat reviewer feedback as the only source of scope.
- Preserve the read-only dashboard as an app-layer display surface over already-derived deterministic inputs.
- Missing or unknown economics must remain missing display values rather than zero.
- Preserve accepted owner boundaries unless the reviewer explicitly identifies a defect in the prior dashboard task.
- Use a supervised worker/subagent before implementation edits if the reviewer-directed fix touches execution-boundary, order-placement safety, accounting/reconciliation, broad owner-boundary code, or repository-governance code.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `apps/dashboard/`
- Likely focused tests under `tests/unit/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside files required by explicit reviewer feedback.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests covering any reviewer-directed dashboard fix
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
