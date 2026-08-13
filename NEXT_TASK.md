# Next Task

## Task ID

RX-039 - Public One-Route Economics Source Completion

## Objective

After the manual one-route real-data CLI task is reviewer-accepted, add the narrowest source-aware public-data-only economics completion needed for one explicit RiseX plus Hyperliquid research route. The work should let the existing real-data research path use public, explicit, route-notional-aware economics values when they are actually available, while preserving unknown or missing public inputs as unknown and fail-closed. Keep the work read-only, public-data-only, one-route-at-a-time, deterministic in tests, and non-trading.

## Starting baseline

Start from reviewer-accepted `main` after the manual one-route real-data CLI task is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-039-public-one-route-economics-source-completion`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: one source-aware public-data-only economics completion step for one explicit route, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, automation, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

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

- Add or adjust the smallest source-aware public-data-only economics completion for one explicitly supplied RiseX plus Hyperliquid route.
- Use the existing `RouteCandidate`, `VenueObservation`, `EstimatedValue`, `FeeModel`, `FundingSnapshot`, `DecisionResult`, and `EvaluationMode` contracts unless a tiny contract extension is strictly necessary and immediately covered by focused tests.
- Use existing read-only public RiseX and Hyperliquid adapter data only.
- Preserve public funding-rate or fee-source metadata from existing public responses only when needed for source-aware completion.
- Convert public economics inputs to USD cash values only when the source is explicit, public, route-notional-aware, and mathematically grounded by the existing one-route target notional.
- Keep unknown, missing, malformed, ungrounded, or account-tier-dependent economics unknown; they must not become zero or default economics.
- Keep the existing one-route real-data research runner and existing `evaluate_route(route, snapshot, mode)` decision path.
- Keep the manual real-data CLI one-route-at-a-time and deterministic in output format.
- Add focused deterministic tests with monkeypatched or injected public data; no network-dependent tests.
- Update governance/source-of-truth docs needed to record the completed handoff and next task.

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
- No private/account/auth adapter endpoints, and no network-dependent tests.
- No route evaluation logic changes except the minimum required to consume already-source-aware completed economics if existing contracts require it.
- No profitability, EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin rule changes.
- No new route statuses.
- No new reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative product hooks, runtime hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as the next ordinary non-dangerous product/runtime step toward live readiness, not as live trading.
- Complete only the public-data economics sources needed by one explicit RiseX plus Hyperliquid real-data research route.
- Keep the work source-aware: every completed economics value must carry an explicit non-`UNKNOWN` source that truthfully reflects the public input used.
- Do not convert missing, unknown, malformed, account-specific, or ungrounded economics to zero.
- Do not use credentials, private/account endpoints, account balances/state, or account-tier assumptions.
- Keep adapters read-only and public-data-only; adapters may fetch and normalize public data only and must not evaluate routes, calculate EV, send orders, write ledgers, or assemble cross-venue snapshots.
- Keep route decisions flowing through the existing real-data research runner and the existing `evaluate_route(route, snapshot, mode)` path.
- Keep one route per invocation. Do not add multiple-route inputs, route scanning, discovery, ranking, watchlists, polling, loops, or refresh behavior.
- Preserve existing no-argument fake CLI behavior.
- Preserve manual one-route real-data CLI fail-closed input validation.
- Keep tests deterministic with injected or monkeypatched public responses; do not require live network availability.
- Preserve RX-033 Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve reviewer acceptance as the only way to mark a task accepted.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Do not add new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts unless strictly necessary for this one-route source-aware economics completion and immediately covered by focused tests.
- Worker policy: one supervised worker required because this task touches public market-data normalization and source-aware economics toward live readiness.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned economics completion is one-route-only, read-only public-data-only, source-aware, uses existing route/observation/runner/evaluate contracts, excludes all hard-stop categories, preserves unknown values as unknown, avoids new owner paths and second economics/decision/snapshot paths, remains one-task/one-branch compliant, preserves reviewer acceptance, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if the required worker is unavailable.

## Required files

- Likely `core/venues/risex.py`
- Likely `core/venues/hyperliquid.py`
- Likely `apps/research_runner/real_data.py`
- Likely `apps/cli/main.py`
- Focused tests under `tests/`
- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`
- Other source-of-truth docs only if strictly necessary.

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused tests added or changed by this task
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
