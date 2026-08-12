# Next Task

## Task ID

RX-028 — Guarded Live Runner Without Orders

## Objective

Add the smallest guarded live runner workflow that consumes one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing non-sending execution plan, and already-derived prerequisite evidence. The runner must prove that live execution remains blocked unless every accepted gate is present and the live switch is explicit, but it must not place orders or construct sendable exchange requests.

## Starting baseline

Start from reviewer-accepted `main` after RX-027 — Execution Planning Without Orders is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-028-guarded-live-runner-without-orders`. Do not implement on `main`.

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

- One guarded live runner workflow for one explicit existing Capture, route, settlement timestamp, and non-sending execution plan.
- Reuse existing route, capture, funding verification, ledger reconciliation, CapturePlan freshness, execution-capability evidence, live-gate bundle, and non-sending execution-planning contracts where applicable.
- The runner may return a deterministic result explaining whether the live runner remained blocked or reached a no-order dry-run ready state.
- The runner may check `ProductRules.live_trading_enabled`, but live trading must remain disabled by default.
- Deterministic tests with injected fixtures only.
- Minimal owner-module additions only where the final design checkpoint proves they are necessary.
- Required repository metadata updates after implementation.

## Forbidden scope

- No order placement.
- No sendable exchange API requests, order payloads, private endpoints, credentials, account balances, exchange account state, automatic polling, or network-dependent tests.
- No route discovery, ranking, watchlists, background loops, paper lifecycle changes, real-data research runner behavior changes, funding settlement verifier changes, ledger reconciliation changes, or execution planning changes unless strictly required by the guarded runner contract.
- No second route decision path, snapshot path, funding verifier, ledger-write path, replay path, VWAP/liquidity path, economics path, execution-planning path, or order path.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not enable live trading by default.
- Do not promote order placement, monitoring, dashboards, or later roadmap work into this task.

## Implementation requirements

- The guarded live runner must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, execution-capability evidence, live-gate bundle checks, and non-sending execution planning.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution capability evidence, missing non-sending plan, stale non-sending plan, live switch disabled, or any sendable order material must fail closed.
- The runner must not call `evaluate_route()`, assemble snapshots, calculate profitability, call venue adapters, import or call order placement behavior, write ledger events unless strictly justified by an accounting-owned event, or place orders.
- If `ProductRules.live_trading_enabled` is false, the runner must fail closed before any no-order ready state.
- Even when `ProductRules.live_trading_enabled` is true and all prerequisite evidence is exact, RX-028 must stop at a no-order guarded state and must not send orders.
- Tests must inject all prerequisite evidence and avoid live network dependency.
- Worker policy: this task touches live-runner and execution-boundary safety boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker.
- The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- Worker must not commit, push, merge, approve work, or start unrelated scope.

## Required files

- Likely `apps/live_runner/`
- Likely `core/execution/planning.py` only if the existing non-sending plan contract needs a strictly necessary compatibility check
- Likely `core/risk/gates.py` only if existing gate reuse is insufficient and the design checkpoint proves a risk-owned check is necessary
- Likely focused tests under `tests/unit/` or `tests/replay/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused guarded live runner tests for live-disabled fail-closed behavior, successful no-order guarded readiness, and fail-closed missing/stale/malformed/cross-identity prerequisite evidence
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
