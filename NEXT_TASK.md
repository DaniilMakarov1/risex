# Next Task

## Task ID

RX-013 - Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage

## Objective

Add deterministic append-only ledger recording and replay coverage for fake live gate evidence bundle results. The task should record bundle-check outcomes as offline evidence only, downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, execution capability, and the RX-012 bundle gate. It must not enable live trading or create executable order plans.

## Starting baseline

Start from reviewer-accepted `main` after RX-Q002 is accepted and merged.

## Branch

Create and work on `task/rx-013-live-gate-evidence-bundle-ledger-replay`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, or HEAD does not match the stated accepted RX-Q002 baseline.

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

- `core/accounting/ledger.py`
- `core/accounting/reconciliation.py`
- `core/accounting/__init__.py`
- `core/risk/gates.py`
- `core/pipeline/evaluate.py`
- `tests/replay/test_live_gate_evidence_bundle.py`
- `tests/replay/test_ledger_reconciliation.py`
- `tests/invariant/test_economics_boundaries.py`
- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `IMPLEMENTATION_PLAN.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

## Forbidden scope

- No product behavior changes beyond deterministic offline ledger recording/replay for fake live gate evidence bundle outcomes.
- No route evaluation changes outside optional recording of already-computed bundle-check evidence through existing owner boundaries.
- No economics changes.
- No VWAP/liquidity recalculation changes.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No executable `CapturePlan` or executable order plan.
- No live trading enablement.
- No new route statuses.
- No new RejectReason values unless the final RX-013 prompt explicitly requires a centralized reason and updates invariant tests.
- No canary architecture.
- No hold-next-cycle logic.
- No second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, or live execution path.
- No broad refactors.
- No speculative helpers or future hooks.

## Implementation requirements

- Preserve `evaluate_route(route, snapshot, mode)` as the only route decision path.
- Keep fake bundle-check logic in `core/risk/gates.py`.
- Keep append-only ledger writes in `core/accounting/ledger.py`.
- Reuse the RX-012 `LiveGateEvidenceBundle` contract and existing evidence contracts.
- Any new ledger event payload must be immutable, deterministic, capture-scoped, route-scoped, settlement-scoped, and fail closed on missing, duplicated, stale, unknown, or contradictory evidence during replay.
- Ledger replay must not recalculate EV, fees, funding, VWAP, basis, or profitability.
- Ledger replay must not call adapters, call execution modules, place orders, create live plans, mutate route eligibility decisions, or return `LIVE_ELIGIBLE`.
- Even with a recorded successful fake bundle check, current route decisions must remain blocked by `LIVE_GATES_NOT_IMPLEMENTED` until a later accepted task implements a safe live path.
- Exactly one supervised worker/subagent is required for design support before implementation.
- The worker must stop at DESIGN CHECKPOINT before any implementation edits. Parent Codex must read the checkpoint and approve the direction or steer before implementation continues.
- If the required worker is unavailable, Parent Codex must stop before edits and report the blocker.
- Parent Codex owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- At DESIGN CHECKPOINT, the worker must answer:
  - What minimal ledger event contract is needed?
  - Which existing RX-012 bundle evidence and gate result can be reused?
  - Where should append-only recording live?
  - Where should replay validation live?
  - What files need changes?
  - What abstractions are unnecessary and must be avoided?
  - What tests should prove fail-closed behavior?
  - Confirm no live trading, no orders, no adapters, no new route status, no second decision path.
- If the worker continues beyond design support, it must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT.

## Required files

- `core/accounting/ledger.py`
- `core/accounting/reconciliation.py`
- `core/accounting/__init__.py`
- `core/risk/gates.py`
- `core/pipeline/evaluate.py`
- `tests/replay/test_live_gate_evidence_bundle.py`
- `tests/replay/test_ledger_reconciliation.py`
- `tests/invariant/test_economics_boundaries.py`
- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `IMPLEMENTATION_PLAN.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

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
