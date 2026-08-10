# Next Task

## Task ID

RX-012 - Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

## Objective

Add deterministic offline evidence-bundle contracts and fake replay coverage for the future live gate sequence. The bundle must remain downstream of route decisions, ledger reconciliation, funding settlement verification, CapturePlan freshness, and execution-capability evidence. It must not enable live trading or create executable order plans.

## Starting baseline

Start from reviewer-accepted `main` after RX-Q001 is accepted and merged.

## Branch

Create and work on `task/rx-012-offline-live-gate-evidence-bundle`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, or HEAD does not match the stated baseline.

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

- `core/domain/contracts.py`
- `core/domain/__init__.py`
- `core/risk/gates.py`
- `core/pipeline/evaluate.py`
- `tests/unit/test_risk_gates.py`
- `tests/unit/test_evaluate_route.py`
- `tests/replay/test_live_gate_evidence_bundle.py`
- `tests/invariant/test_economics_boundaries.py`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

## Forbidden scope

- No product behavior changes beyond deterministic offline fake live-gate evidence bundling.
- No route evaluation changes outside passing and checking the new fake evidence bundle through the existing `evaluate_route()` path.
- No economics changes.
- No VWAP/liquidity recalculation changes.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No ledger write path changes unless the final RX-012 prompt explicitly requires them.
- No live runner behavior.
- No adapters, orders, network calls, API clients, credentials, secrets, or trading logic.
- No executable `CapturePlan` or executable order plan.
- No live trading enablement.
- No new route statuses.
- No new RejectReason values unless the RX-012 prompt explicitly requires a centralized reason and updates invariant tests.
- No canary architecture.
- No hold-next-cycle logic.
- No second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, or live execution path.
- No broad refactors.
- No speculative helpers or future hooks.

## Implementation requirements

- Preserve `evaluate_route(route, snapshot, mode)` as the only route decision path.
- Keep fake evidence bundle logic in the authoritative live/risk gate boundary, `core/risk/gates.py`.
- Reuse existing evidence contracts where possible: ledger reconciliation, funding settlement verification, CapturePlan freshness, and execution capability.
- Any new domain contract must be immutable, deterministic, timezone-aware where timestamps are used, fail closed on missing/unknown/contradictory evidence, and be used immediately by gate tests.
- The bundle must not recalculate EV, fees, funding, VWAP, basis, or profitability.
- The bundle must not read storage, call adapters, call execution modules, place orders, create live plans, mutate route eligibility decisions, or return `LIVE_ELIGIBLE`.
- Even with live trading manually enabled and exact fake evidence, current route decisions must remain blocked by `LIVE_GATES_NOT_IMPLEMENTED` until a later accepted task implements a safe live path.
- Worker usage is optional. If used, workers must follow the checkpoint protocol in `docs/templates/WORKER_CHECKPOINT_TEMPLATE.md`.

## Required files

- `core/domain/contracts.py`
- `core/domain/__init__.py`
- `core/risk/gates.py`
- `core/pipeline/evaluate.py`
- `tests/unit/test_risk_gates.py`
- `tests/unit/test_evaluate_route.py`
- `tests/replay/test_live_gate_evidence_bundle.py`
- `tests/invariant/test_economics_boundaries.py`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `README.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

## Required tests

- `python scripts/validate_next_task.py`
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
