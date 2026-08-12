# Next Task

## Task ID

RX-022 — Read-only RiseX Observation Adapter

## Objective

Add a read-only RiseX adapter that fetches and normalizes per-venue `VenueObservation` inputs only. Keep it downstream of venue data ingestion and upstream of the existing `assemble_route_snapshot()` path; do not evaluate routes, rank routes, start paper lifecycle, write ledger events, or perform any trading behavior inside the adapter.

## Starting baseline

Start from reviewer-accepted `main` with RX-021 finalized. Before edits, verify the exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-022-read-only-risex-observation-adapter`. Do not implement on `main`.

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

- A read-only RiseX venue adapter that returns normalized `VenueObservation` values for one RiseX venue/symbol at a time.
- Minimal adapter tests using deterministic fixtures or injected read-only responses; tests must not depend on live external availability.
- Existing venue adapter interfaces and normalized domain contracts only where required for the RiseX adapter.
- Focused invariant coverage proving the adapter does not own route decisions, EV, VWAP, ledger writes, paper lifecycle, live behavior, or order placement.
- Required repository metadata updates after implementation.

## Forbidden scope

- No Hyperliquid adapter; keep that as a later separate task.
- No route profitability calculation, route ranking, route eligibility mutation, or calls to `evaluate_route()` from the adapter.
- No route snapshot assembly inside the adapter; preserve `assemble_route_snapshot()` as the single snapshot path.
- No second EV, fee, funding, VWAP/liquidity, basis, route decision, snapshot assembly, ledger-write, replay, or live execution path.
- No standalone spread, price-impact, basis, slippage, max-level, hidden-buffer, or safety-margin filters.
- No private account endpoints, credentials, secrets, orders, live runner behavior, live trading, executable `CapturePlan`, or executable order plan.
- No canary architecture.
- No hold-next-cycle logic.
- No speculative helpers, wrappers, unused abstractions, or future hooks.
- Do not implement real market-data route snapshot assembly, real-data research runner, funding settlement approval, execution planning, live runner behavior, order placement, monitoring, or dashboards.

## Implementation requirements

- Keep adapters read-only and per-venue: they may fetch/parse RiseX market data and produce one `VenueObservation`, but they must not assemble cross-venue route snapshots or evaluate route profitability.
- Preserve `VenueAdapter.fetch_observation(symbol) -> VenueObservation` as the adapter-facing contract unless code inspection proves the current interface differs.
- Normalize timestamps as timezone-aware values and preserve unknown economics explicitly through existing `EstimatedValue`/`ValueSource` contracts.
- Do not silently convert missing fees, funding, order-book depth, or timestamps into zero/default success values.
- If a live HTTP boundary is introduced, isolate it behind deterministic tests that use fixtures or injected fake responses; do not require network access for tests.
- Worker policy: this task touches adapter and data-ingestion boundaries, so one supervised worker/subagent is required before implementation edits. If worker tooling is unavailable, stop before edits and report the blocker. The worker must stop at DESIGN CHECKPOINT before edits and at CODE, TEST, and VALIDATION checkpoints if it continues.
- Parent owns steering, final diff review, validation, commit, push, and final report.

## Required files

- Likely `core/venues/`
- Likely focused tests under `tests/unit/`
- Possibly deterministic fixture files under `tests/fixtures/` only if needed
- Repository metadata files required by `AGENTS.md`
- Do not touch product code outside the owner modules required by the final design checkpoint.

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- Focused tests for read-only RiseX observation normalization and fail-closed missing/unknown data behavior
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
