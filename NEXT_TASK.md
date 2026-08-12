# Next Task

## Task ID

RX-029 — Explicit Approval-Gated Order Placement Boundary

## Objective

Add the smallest explicit approval-gated order placement boundary downstream of the guarded no-order live runner. The workflow must consume one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing no-order ready guarded live runner result, one existing non-sending execution plan, and one explicit caller-supplied approval. Live trading must remain disabled by default, and tests must remain deterministic with injected fixtures only.

## Starting baseline

Start from reviewer-accepted `main` after RX-028 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-029-explicit-approval-gated-order-placement-boundary`. Do not implement on `main`.

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

- One explicit approval-gated order placement boundary for one existing Capture, route, funding settlement timestamp, guarded no-order ready result, and non-sending execution plan.
- Reuse the existing guarded live runner result, non-sending execution-planning contract, route identity, product rules, and centralized execution owner module.
- The workflow may require `ProductRules.live_trading_enabled is True`, but live trading must remain disabled by default.
- Deterministic tests with injected fixtures only.
- Minimal owner-module additions only where the worker DESIGN checkpoint proves they are necessary.
- Required repository metadata updates after implementation.

## Forbidden scope

- No automatic order placement.
- No background loops, watchlists, route discovery, ranking, polling, monitoring dashboards, or paper lifecycle changes.
- No private endpoints, credentials, account balances, exchange account state, or network-dependent tests.
- No real exchange adapters or public market-data adapter changes.
- No route evaluation, snapshot assembly, profitability calculation, funding verification changes, ledger reconciliation changes, live-gate bundle changes, or non-sending execution-planning changes unless strictly required by the order boundary contract.
- No second route decision path, snapshot path, funding verifier, ledger-write path, replay path, VWAP/liquidity path, economics path, live-runner path, execution-planning path, or order path.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No canary architecture.
- No hold-next-cycle logic.
- Do not enable live trading by default.
- Do not promote monitoring, dashboards, or later roadmap work into this task.

## Implementation requirements

- The order placement boundary must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, execution-capability evidence, live-gate bundle checks, non-sending execution planning, and guarded no-order live runner readiness.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution capability evidence, missing non-sending plan, stale non-sending plan, disabled live switch, non-ready guarded result, missing approval, false approval, stale approval, or cross-identity approval must fail closed.
- The workflow must not call `evaluate_route()`, assemble snapshots, calculate profitability, call venue adapters, replay funding or ledger history, write ledger events unless strictly justified by an accounting-owned event, or use real credentials.
- Any future sendable material must be created only inside the authoritative `core/execution/` owner boundary and only after exact explicit approval has passed.
- Tests must inject all prerequisite evidence and avoid live network dependency.
- Worker policy: this task touches execution-boundary and order-placement safety boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker.
- The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- Worker must not commit, push, merge, approve work, or start unrelated scope.

## Required files

- Likely `core/execution/orders.py`
- Likely `apps/live_runner/` only if the existing guarded no-order result needs a strictly necessary compatibility check
- Likely focused tests under `tests/unit/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused approval-gated order-boundary tests for live-disabled fail-closed behavior, missing/false/stale/cross-identity approval, missing/stale prerequisite evidence, non-ready guarded result, successful explicit approval through injected deterministic order boundary, and no network or credential dependency
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
