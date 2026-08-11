# Next Task

## Task ID

RX-016 - Offline SQLite Ledger Reopen Fail-Closed Replay Coverage

## Objective

Add deterministic offline coverage proving that malformed, stale, or contradictory append-only evidence persisted after reopening a SQLite ledger still fails closed through the existing reconciliation replay and explicit reconciliation gate. The task must not change live eligibility, route decisions, economics, adapters, orders, or live trading behavior.

## Starting baseline

Start from reviewer-accepted `main` after the previous task is accepted and merged.

## Branch

Create and work on `task/rx-016-sqlite-ledger-reopen-fail-closed-replay`.

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
- `tests/unit/test_ledger.py`
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

- No product behavior changes beyond deterministic SQLite reopen fail-closed replay coverage.
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

- Preserve `SQLiteLedger` as the existing minimal append-only persistence contract.
- Use the existing SQLite ledger contract; do not introduce migrations or a second storage layer unless an actual reopen replay bug requires the smallest possible fix.
- Prove that malformed, stale, or contradictory persisted appends after reopening an existing SQLite ledger remain unreconciled after SQLite round-trip.
- Prove that `is_ledger_explicitly_reconciled(reopened.records())` remains false for those fail-closed histories.
- Prove replay outcomes are deterministic from reopened SQLite records.
- SQLite replay tests must not recalculate EV, fees, funding, VWAP, basis, or profitability.
- SQLite replay tests must not call adapters, call execution modules, place orders, create live plans, mutate route eligibility decisions, or return `LIVE_ELIGIBLE`.
- Worker policy: one supervised worker required.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- `storage/sqlite/ledger.py`
- `tests/unit/test_ledger.py`
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
