# Next Task

## Task ID

RX-038 - One-Route Real Data CLI Toward Live Readiness

## Objective

After this Product Owner roadmap direction gate is reviewer-accepted, add a manual CLI entry point for one explicitly supplied RiseX plus Hyperliquid route. The CLI must use the existing read-only public RiseX and Hyperliquid adapters, the existing one-route real-data snapshot handoff, and the existing one-route real-data research runner/evaluate path. Keep the work read-only, public-data-only, one-route-at-a-time, fail-closed, and non-trading.

## Starting baseline

Start from reviewer-accepted `main` after this Product Owner roadmap direction gate is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-038-one-route-real-data-cli-toward-live-readiness`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: one manual read-only public-data CLI entry point for one explicit route, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, automation, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

Read:

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md
- docs/WORKFLOW.md
- Relevant templates in `docs/templates/`

## Allowed scope

- Add one manual CLI entry point for one explicitly supplied route.
- Use the existing `RouteCandidate` contract for route identity, venues, symbols, entry sides, and target notional.
- Use the existing read-only public `RiseXObservationAdapter`.
- Use the existing read-only public `HyperliquidObservationAdapter`.
- Use the existing `assemble_route_snapshot_from_adapters()` handoff only through the existing real-data research runner.
- Use the existing `run_real_data_research_route()` path and existing `evaluate_route(route, snapshot, mode)` decision path.
- Accept exactly one route at a time from explicit CLI inputs, including explicit route identity, symbols, opposing entry sides, target notional, evaluation mode, and timezone-aware assembly timestamp.
- Fail closed on missing, unknown, malformed, non-finite, zero, negative, or contradictory CLI inputs.
- Preserve unknown values as unknown; unknown values must never silently become zero or default economics.
- Print or return the resulting one-route decision in a deterministic, inspectable CLI format.
- `apps/cli/main.py`
- Focused CLI tests under `tests/`
- Invariant tests only if needed to lock the CLI boundary.
- Governance docs needed to record the completed handoff and next task.

## Forbidden scope

- No live trading.
- No live trading by default.
- No route discovery.
- No route ranking.
- No watchlists.
- No background loops.
- No polling.
- No scheduling.
- No alerts.
- No automatic refresh.
- No private endpoints.
- No credentials.
- No API keys or secrets.
- No account balances.
- No exchange account state.
- No order placement.
- No order cancellation.
- No order status fetching.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No ledger writes.
- No storage migrations.
- No replay changes.
- No paper lifecycle changes.
- No funding settlement verification.
- No ledger reconciliation.
- No route discovery, ranking, acceptance, eligibility mutation, or Capture state transitions.
- No changes to venue adapter behavior beyond instantiating the existing read-only public adapters from the manual CLI.
- No new adapter endpoints, private/account/auth endpoints, or network-dependent tests.
- No route evaluation logic changes.
- No snapshot assembly logic changes.
- No profitability, EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin changes.
- No new route statuses.
- No new reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative product hooks, runtime hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as the next ordinary non-dangerous product/runtime step toward live readiness, not as live trading.
- Implement only a manual CLI entry point for one explicit route supplied by the caller.
- Keep the CLI read-only public data only.
- Instantiate or use only the existing public read-only RiseX and Hyperliquid adapters.
- Delegate real-data snapshot creation and route evaluation to the existing one-route real-data research runner path.
- Require explicit CLI input for route identity, RiseX symbol, Hyperliquid symbol, opposing entry sides, target notional, evaluation mode, and timezone-aware assembly timestamp.
- Parse target notional as `Decimal` and fail closed on missing, non-numeric, non-finite, zero, or negative values.
- Reject malformed or non-timezone-aware timestamps before any adapter call.
- Reject missing or invalid mode, side, identity, venue, or symbol inputs before any adapter call.
- Do not silently convert unknown or malformed values to zero.
- Adapter or snapshot handoff failures must continue to fail closed through the existing real-data research runner behavior.
- Keep one route per invocation. Do not add multiple-route inputs, route scanning, discovery, ranking, watchlists, polling, loops, or refresh behavior.
- Keep tests deterministic with injected or monkeypatched adapters; do not require live network availability.
- Preserve RX-033 Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve reviewer acceptance as the only way to mark a task accepted.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Do not add new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts unless strictly necessary for the CLI entry point and immediately covered by focused tests.
- Worker policy: one supervised worker required because this task touches the CLI boundary for real public market data and the route evaluation handoff toward live readiness.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned CLI is one-route-only, read-only public-data-only, uses existing adapters/handoff/runner/evaluate path, excludes all hard-stop categories, fails closed on malformed input, preserves unknown values as unknown, avoids new owner paths, remains one-task/one-branch compliant, preserves reviewer acceptance, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if the required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Focused CLI tests under `tests/`
- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`
- Other governance docs only if strictly necessary.

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused CLI tests added or changed by this task
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
