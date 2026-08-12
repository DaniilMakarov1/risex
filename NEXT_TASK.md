# Next Task

## Task ID

RX-025 — Real-Data Research Runner

## Objective

Add the smallest non-trading real-data research runner that uses existing `RouteCandidate` inputs, existing read-only venue adapters, the existing real market-data snapshot handoff, and the existing route decision pipeline. Keep it as a research-only runner: assemble and evaluate one explicit route at a time, report deterministic decision output, and do not start paper lifecycle, write ledger events, plan execution, or trade.

## Starting baseline

Start from reviewer-accepted `main` after the real market-data route snapshot assembly handoff is finalized. Before edits, verify the exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-025-real-data-research-runner`. Do not implement on `main`.

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

- A narrow non-trading research runner for one explicit existing `RouteCandidate` at a time.
- Reuse existing read-only `VenueAdapter.fetch_observation(symbol)` implementations.
- Reuse the existing real market-data snapshot handoff and `assemble_route_snapshot()` path.
- Reuse the existing `evaluate_route(route, snapshot, mode)` decision path.
- Deterministic tests with injected adapters and fixtures only.
- Minimal CLI or app wiring only if needed to expose the research runner without changing fake runner behavior.
- Required repository metadata updates after implementation.

## Forbidden scope

- No route ranking, broad opportunity discovery, watchlists, background loops, paper lifecycle, ledger writes, funding settlement verification, execution planning, orders, live runner behavior, credentials, private endpoints, or live trading.
- No second snapshot assembly path; preserve `assemble_route_snapshot()` as the single owner of route snapshot construction.
- No second route decision path; preserve `evaluate_route(route, snapshot, mode)` as the single owner of route decisions.
- No second EV, fee, funding, VWAP/liquidity, basis, ledger-write, replay, or live execution path.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement funding settlement approval, execution planning, guarded live runner behavior, order placement, monitoring, or dashboards.

## Implementation requirements

- The runner must accept or construct exactly one explicit `RouteCandidate`; do not discover or rank routes.
- Snapshot creation must flow through the existing real market-data snapshot handoff and then the existing `assemble_route_snapshot()` path.
- Route decisions must flow through `evaluate_route(route, snapshot, mode)` only after successful snapshot assembly.
- Snapshot assembly or adapter failures must fail closed without evaluating the route.
- The runner must not write to the append-only ledger.
- Tests must inject fake adapters and avoid live network dependency.
- Worker policy: this task touches runner and route-decision orchestration boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `apps/research_runner/`
- Likely `apps/cli/`
- Likely focused tests under `tests/unit/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests for real-data research runner success and fail-closed snapshot/adapter failure behavior
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
