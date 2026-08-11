# Next Task

## Task ID

RX-021 — Paper Result Attribution And PnL Explanation

## Objective

Add the next missing deterministic paper-result attribution and PnL explanation layer downstream of existing route decisions and fake paper lifecycle events. The output should explain why a fake paper run started or did not start, preserve the route decision economics already produced by `evaluate_route()`, and make paper outcomes easier to inspect without recalculating route profitability or changing eligibility.

## Starting baseline

Start from reviewer-accepted `main` after RX-020 is reviewed and accepted. Before edits, verify the exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-021-paper-result-attribution-pnl-explanation`. Do not implement on `main`.

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

- Existing fake paper lifecycle result and rejection reporting.
- Existing `DecisionResult` economics already produced by the single `evaluate_route()` path.
- Existing append-only ledger events only if needed to persist or replay paper-result explanation evidence through the current accounting owner module.
- Focused paper lifecycle, ledger, and invariant tests proving explanations are deterministic and downstream-only.
- Required repository metadata updates after implementation.

## Forbidden scope

- No product strategy changes.
- No new route statuses.
- No new `RejectReason` values.
- No route profitability recalculation outside `evaluate_route()`.
- No second EV, fee, funding, VWAP/liquidity, basis, route decision, snapshot assembly, ledger-write, replay, or live execution path.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No adapters, network calls, API clients, credentials, secrets, orders, live runner behavior, live trading, executable `CapturePlan`, or executable order plan.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement read-only adapters, real market-data snapshot assembly, real-data research runner, funding settlement approval, execution planning, live runner behavior, order placement, monitoring, or dashboards.

## Implementation requirements

- Keep paper-result explanation downstream of existing `DecisionResult` values and `run_paper_lifecycle()`.
- Preserve `evaluate_route(route, snapshot, mode)` as the single route decision path.
- Preserve `assemble_route_snapshot()` as the single route snapshot assembly path.
- Preserve append-only ledger behavior; if ledger evidence changes are needed, keep them in `core/accounting/ledger.py` and deterministic replay in the existing accounting/reconciliation owner boundary.
- Do not recalculate EV, fees, funding, VWAP, basis, or profitability in the paper runner.
- Do not start paper captures for discovery decisions, rejected decisions, research-only decisions, or live-eligible decisions.
- Keep outputs deterministic, fake-data-only, offline, and non-trading.
- Worker policy: this task touches paper lifecycle/accounting-facing result contracts, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `apps/paper_runner/lifecycle.py`
- Likely focused tests under `tests/unit/`
- Possibly `core/accounting/ledger.py` and replay tests only if paper-result explanation must be recorded as append-only evidence
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests for fake paper-result attribution and PnL explanation behavior
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
