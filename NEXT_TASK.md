# Next Task

## Task ID

RX-024 — Real Market-Data Route Snapshot Assembly

## Objective

Add the smallest real market-data route snapshot assembly handoff that consumes existing read-only per-venue observations and calls the existing `assemble_route_snapshot()` path for one `RouteCandidate` at a time. Keep this as data assembly only; do not evaluate routes, rank routes, start paper lifecycle, write ledger events, or perform any trading behavior.

## Starting baseline

Start from reviewer-accepted `main` after the read-only Hyperliquid observation adapter is finalized. Before edits, verify the exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-024-real-market-data-route-snapshot-assembly`. Do not implement on `main`.

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

- A narrow assembly handoff that fetches or accepts one RiseX `VenueObservation` and one Hyperliquid `VenueObservation` for an existing `RouteCandidate`, then delegates route-aligned snapshot construction to `assemble_route_snapshot()`.
- Existing venue adapter interfaces and normalized domain contracts only where required for the handoff.
- Deterministic tests using injected adapters or fixtures; tests must not depend on live external availability.
- Focused invariant coverage proving the handoff does not own route decisions, EV, VWAP, ledger writes, paper lifecycle, live behavior, or order placement.
- Required repository metadata updates after implementation.

## Forbidden scope

- No route profitability calculation, route ranking, route eligibility mutation, or calls to `evaluate_route()` from the assembly handoff.
- No second snapshot assembly path; preserve `assemble_route_snapshot()` as the single owner of route snapshot construction.
- No second EV, fee, funding, VWAP/liquidity, basis, route decision, ledger-write, replay, or live execution path.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No private account endpoints, credentials, secrets, orders, live runner behavior, live trading, executable `CapturePlan`, or executable order plan.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement a real-data research runner, funding settlement approval, execution planning, live runner behavior, order placement, monitoring, or dashboards.

## Implementation requirements

- Reuse `VenueAdapter.fetch_observation(symbol) -> VenueObservation` for venue data ingestion.
- Reuse the existing `assemble_route_snapshot()` function for route snapshot construction.
- Keep adapters read-only and per-venue; do not move cross-venue logic into adapters.
- Normalize no economics inside the handoff; economics remain owned by the existing owner modules and consumed later by `evaluate_route()`.
- Missing, malformed, or contradictory observations must fail closed before any route decision can run.
- If any live HTTP boundary is reachable through existing adapters, isolate tests behind injected adapters or fixtures; do not require network access for tests.
- Worker policy: this task touches data-ingestion and snapshot boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `core/pipeline/`
- Likely focused tests under `tests/unit/`
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests for real market-data route snapshot assembly handoff behavior and fail-closed missing/contradictory observation behavior
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
