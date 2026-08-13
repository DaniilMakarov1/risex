# Next Task

## Task ID

RX-053 - Manual One-Route Public Paper Trader Bridge

## Objective

After RX-052 reviewer acceptance and finalization, add one explicit manual operator command or app-layer runner that connects one existing public one-route real-data ENTRY decision to the existing fake paper lifecycle and append-only ledger, then prints a deterministic stdout summary. This is a fake-money paper-trader bridge only. It must not implement live trading, real exchange orders, private/account endpoints, credentials, exchange account state, account balances, sendable exchange requests, order payload construction, execution automation, execution planning, polling, ranking, discovery, or any financially dangerous action.

## Starting baseline

Start from reviewer-accepted `main` after RX-052 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-053-manual-one-route-public-paper-trader-bridge`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-052 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous fake-money paper-trading runtime work only. Stop before edits unless explicit user approval exists for any task involving live trading, real order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add one explicit manual operator command or app-layer runner for one manually supplied RiseX plus Hyperliquid route.
- Reuse the existing manual public route input requirements: route id, capture id, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, positive finite target notional, `EvaluationMode.ENTRY`, and timezone-aware assembly timestamp.
- Reuse the existing read-only public `RiseXObservationAdapter` and `HyperliquidObservationAdapter` construction boundaries after input validation.
- Reuse the existing one-route real-data runner and the single `evaluate_route(route, snapshot, mode)` decision path.
- Delegate fake paper execution to the existing `run_paper_lifecycle()` behavior in `apps/paper_runner/lifecycle.py`.
- Write fake paper ledger events only through the existing `core/accounting/ledger.py` ownership boundary.
- Optionally support one explicit local SQLite ledger path if implemented through the existing `storage/sqlite/ledger.py` contract and explicit operator input.
- Print a deterministic stdout summary covering route id, decision mode/status/reasons, fake paper started/not-started state, paper start blockers, ledger event count/sequences/types, and existing PnL explanation values without recalculating profitability.
- Add focused tests for started fake paper behavior, non-started fake paper rejection behavior, malformed operator input fail-closed before adapter construction, optional SQLite path behavior if implemented, and preservation of unknown economics as missing rather than zero.
- Update source-of-truth docs to record the accepted bridge behavior and next handoff.

## Forbidden scope

- No live trading.
- No live trading by default.
- No real exchange order placement.
- No order cancellation.
- No order status fetching.
- No private endpoints.
- No account endpoints.
- No credentials.
- No API keys or secrets.
- No exchange account state.
- No account balances.
- No account-tier assumptions.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No automatic polling.
- No background loops.
- No scheduling.
- No alerts.
- No automatic refresh.
- No route discovery.
- No route ranking.
- No watchlists.
- No adapter endpoint changes.
- No fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin rule changes.
- No funding settlement verification changes.
- No ledger reconciliation changes.
- No replay changes.
- No storage migrations.
- No route eligibility mutation.
- No Capture state transition changes.
- No route statuses.
- No reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No unknown-to-zero behavior.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as the smallest manual fake-money paper-trader bridge. It is runtime work, but it is not live trading and not exchange execution.
- The bridge must require `EvaluationMode.ENTRY`; discovery-mode decisions must not start fake paper.
- Public data flow must remain one-route-at-a-time and manually invoked. Do not add discovery, ranking, polling, watchlists, loops, scheduling, alerts, or auto-refresh.
- Decision creation must remain downstream of the existing one-route real-data runner and `evaluate_route(route, snapshot, mode)`.
- Paper lifecycle behavior must remain owned by `apps/paper_runner/lifecycle.py`; do not duplicate paper start predicates, state transitions, PnL attribution, or ledger event construction outside the existing owner path.
- Ledger writes must remain owned by `core/accounting/ledger.py`; any SQLite persistence must use only the existing `SQLiteLedger` implementation and an explicit local path supplied by the operator.
- Missing funding, fee, snapshot, Entry EV, or net profit values must stay missing/unknown in stdout and ledger-derived paper explanation. They must not become zero, success, or profitability.
- The stdout summary must be deterministic and suitable for tests.
- Preserve existing no-argument fake CLI behavior, existing `real-data-route` default output, existing public-readiness report text output, and existing public-readiness JSON output unless the new manual bridge command is explicitly invoked.
- Preserve RX-048 as the latest accepted product/reporting baseline until this task is reviewer-accepted as a later product/runtime task.
- Preserve RX-052 as pending or accepted according to explicit reviewer evidence.
- Preserve reviewer-only acceptance; implementation-complete branch work is not accepted until an explicit reviewer accepts it.
- Control Tower autonomous selection is allowed only because this is a non-dangerous fake-money paper runtime task grounded in source-of-truth repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this bridge touches app/runtime, paper lifecycle, ledger ownership, and operator boundaries.
- At DESIGN CHECKPOINT, the worker must answer whether the bridge is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, uses the existing one-route public decision path, uses the existing fake paper lifecycle, keeps ledger writes inside accounting ownership, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, excludes all hard-stop categories, avoids invented live/order/private scope, avoids discovery/ranking/polling, preserves unknown-as-missing behavior, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `apps/paper_runner/lifecycle.py` only if a strictly necessary owner-local adjustment is discovered
- Likely `apps/paper_runner/__init__.py` only if a new app-layer bridge export is necessary
- Likely `tests/unit/test_cli_main.py`
- Likely focused paper bridge tests under `tests/unit/`
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`

## Required tests

- Focused tests for the new manual bridge behavior
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
