# Next Task

## Task ID

RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders

## Objective

Add the smallest read-only monitoring/dashboard surface for already-derived local evidence after the explicit approval-gated order-boundary task is reviewed and accepted. The dashboard must display one existing Capture, one existing RouteCandidate, one explicit funding settlement timestamp, existing route decision/evidence state, existing non-sending execution plan state, existing guarded no-order readiness state, and existing approval-boundary result state from caller-supplied deterministic fixtures only. It must not make decisions, poll venues, place orders, write ledger events, or change lifecycle state.

## Starting baseline

Start from reviewer-accepted `main` after the explicit approval-gated order-boundary task is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-030-read-only-monitoring-dashboard-without-decisions-or-orders`. Do not implement on `main`.

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

- One read-only dashboard or monitor view over one existing Capture and one existing route.
- Use caller-supplied deterministic fixture inputs only.
- Reuse existing Capture, RouteCandidate, DecisionResult, funding verification, ledger reconciliation, live-gate bundle, non-sending execution plan, guarded readiness, approval evidence, and approval-boundary result contracts.
- Display status summaries and fail-closed missing-data states without recomputing product decisions.
- Minimal app-layer code under the dashboard owner area only, plus focused deterministic tests and repository metadata updates.

## Forbidden scope

- No route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, or auto-refresh.
- No venue adapters, public market-data calls, private endpoints, credentials, account balances, exchange account state, or network-dependent tests.
- No order placement, sendable exchange request construction, order cancellation, order status fetching, or execution automation.
- No route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, or approval-boundary execution unless strictly isolated to tests that provide already-derived fixture outputs.
- No ledger writes, storage migrations, replay changes, paper lifecycle changes, route eligibility mutation, or Capture state transitions.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No new route statuses, reject reasons, canary architecture, hold-next-cycle logic, or live trading by default.

## Implementation requirements

- The dashboard must remain read-only and downstream of existing owner modules.
- Missing, malformed, stale, cross-capture, cross-route, cross-settlement, unverified, unreconciled, non-ready, disabled-live, false approval, stale approval, or boundary-blocked inputs must render as blocked/missing state instead of recalculating or silently normalizing values.
- The implementation must not call `evaluate_route()`, assemble snapshots, calculate profitability, call venue adapters, replay funding or ledger history, write ledger events, call order-boundary execution, use real credentials, or perform network I/O.
- Any display model must preserve unknown/missing economics as missing rather than zero.
- Tests must inject all input evidence and avoid live network dependency.
- Use a supervised worker/subagent before implementation edits if the final design touches execution-boundary, order-placement safety, accounting/reconciliation, or broad owner-boundary code. If the work stays strictly read-only app/dashboard display code, worker use is optional under `AGENTS.md`.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `apps/dashboard/`
- Likely focused tests under `tests/unit/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside owner modules required by the final design.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused read-only dashboard tests for exact identity rendering, missing/malformed/cross-identity fail-closed display state, blocked guarded readiness, blocked approval-boundary result, unknown economics preserved as missing, and no network/order/ledger dependency
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
