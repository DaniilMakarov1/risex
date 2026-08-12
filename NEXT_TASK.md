# Next Task

## Task ID

RX-027 — Execution Planning Without Orders

## Objective

Add the smallest non-sending execution planning contract for one existing Capture, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-verified prerequisite evidence. The plan must describe intended entry and unwind actions without sending orders, calling private endpoints, mutating route eligibility, or enabling live trading.

## Starting baseline

Start from reviewer-accepted `main` after the approval-gated funding settlement verification task is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-027-execution-planning-without-orders`. Do not implement on `main`.

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

- One non-sending execution planning workflow for one explicit existing Capture, route, and settlement timestamp.
- Reuse existing `RouteCandidate`, `Capture`, funding verification, ledger reconciliation, CapturePlan freshness, and execution-capability evidence contracts where applicable.
- Plan output may describe intended venues, symbols, sides, target notional, settlement timestamp, and required prerequisite evidence references.
- Deterministic tests with injected fixtures only.
- Minimal owner-module additions only where the final design checkpoint proves they are necessary.
- Required repository metadata updates after implementation.

## Forbidden scope

- No order placement.
- No live runner behavior.
- No private endpoints, credentials, account balances, exchange account state, automatic polling, or network-dependent tests.
- No route discovery, ranking, watchlists, background loops, paper lifecycle changes, real-data research runner behavior changes, funding settlement verifier changes unless strictly required by the plan contract.
- No second route decision path, snapshot path, funding verifier, ledger-write path, replay path, VWAP/liquidity path, economics path, or live execution path.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not add monitoring, dashboards, guarded live runner behavior, or order placement.

## Implementation requirements

- Plans must be non-executable evidence only and must not contain exchange credentials or sendable API requests.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, or non-executable execution capability evidence must fail closed.
- Planning must remain downstream of existing route decisions, settlement verification, ledger reconciliation, and execution-capability evidence.
- Any ledger writes, if strictly needed, must use existing append-only ledger helpers or a narrowly justified accounting-owned event; do not add update/delete behavior.
- Do not call `evaluate_route()`, assemble snapshots, calculate profitability, call venue adapters, import live runner behavior, or place orders.
- Tests must inject all prerequisite evidence and avoid live network dependency.
- Worker policy: this task touches execution-boundary and live-adjacent safety boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `core/execution/`
- Likely `core/domain/contracts.py` only if a new narrow non-sending plan contract is strictly necessary
- Likely `core/risk/gates.py` only if prerequisite gating must be reused or extended
- Likely focused tests under `tests/unit/` or `tests/replay/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused execution planning tests for successful non-sending plans and fail-closed missing/stale/malformed/cross-identity prerequisite evidence
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
