# Next Task

## Task ID

RX-014 - Offline Live Gate Evidence Bundle SQLite Persistence Replay Coverage

## Objective

Add deterministic SQLite persistence replay coverage for the fake live gate evidence bundle ledger event introduced by the prior task. The task should prove that `live_gate_evidence_bundle_recorded` payloads round-trip through `storage/sqlite/ledger.py` and replay the same way as in-memory ledger records. It must not change live eligibility, route decisions, economics, adapters, orders, or live trading behavior.

## Starting baseline

Start from reviewer-accepted `main` after the prior task is accepted and merged.

## Branch

Create and work on `task/rx-014-live-gate-bundle-sqlite-replay`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, or HEAD does not match the reviewer-accepted baseline.

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

- `storage/sqlite/ledger.py`
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

- No product behavior changes beyond deterministic SQLite round-trip replay coverage for fake live gate evidence bundle ledger records.
- No route evaluation changes.
- No risk gate behavior changes unless a persistence bug makes existing replay impossible, and then keep the change narrowly scoped.
- No economics changes.
- No VWAP/liquidity recalculation changes.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No executable `CapturePlan` or executable order plan.
- No live trading enablement.
- No new route statuses.
- No new `RejectReason` values.
- No canary architecture.
- No hold-next-cycle logic.
- No second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, replay module, or live execution path.
- No broad refactors.
- No speculative helpers or future hooks.

## Implementation requirements

- Preserve `evaluate_route(route, snapshot, mode)` as the only route decision path.
- Keep fake bundle-check logic in `core/risk/gates.py`.
- Keep append-only ledger writes in `core/accounting/ledger.py`.
- Keep replay validation in `core/accounting/reconciliation.py`.
- Use the existing SQLite ledger contract; do not introduce migrations or a second storage layer unless an actual round-trip bug requires the smallest possible fix.
- Prove that a valid fake bundle ledger record persisted to SQLite replays with the same outcome and referenced sequences as the in-memory ledger path.
- Prove that malformed or contradictory persisted bundle evidence still fails closed after SQLite round-trip.
- SQLite replay tests must not recalculate EV, fees, funding, VWAP, basis, or profitability.
- SQLite replay tests must not call adapters, call execution modules, place orders, create live plans, mutate route eligibility decisions, or return `LIVE_ELIGIBLE`.
- Even with a persisted and replayed successful fake bundle check, current route decisions must remain blocked by `LIVE_GATES_NOT_IMPLEMENTED` until a later accepted task implements a safe live path.
- Use a supervised worker/subagent if repository governance requires one for this architecture-sensitive task.

## Required files

- `storage/sqlite/ledger.py`
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
