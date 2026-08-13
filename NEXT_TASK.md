# Next Task

## Task ID

RX-045 - Manual One-Route Public Readiness Report

## Objective

After RX-044 is reviewer-accepted, add one manual, one-route, public/read-only, non-trading readiness report for an explicitly supplied RiseX plus Hyperliquid route. The report should expand the existing one-route CLI/reporting surface so an operator can see which public fee, funding, and economics evidence was applied, what remains `UNKNOWN`, and why the route is or is not ready for later fail-closed live-readiness stages. Keep all underlying route evaluation, snapshot assembly, public adapter behavior, source-aware fee/funding completion, and fail-closed unknown handling on the existing owner paths.

## Starting baseline

Start from reviewer-accepted `main` after RX-044 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-045-manual-one-route-public-readiness-report`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-044 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: manual one-route public/read-only reporting only, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, automation, account-state access, destructive reset, unsafe scope, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

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

- Add one manual readiness-report mode to the existing one-route public CLI/reporting surface, preferably as an opt-in flag on the existing `real-data-route` command while preserving existing no-argument fake CLI behavior and existing default `real-data-route` output.
- Use one explicitly supplied route only: caller-provided route id, capture id, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, target notional, evaluation mode, and timezone-aware assembly timestamp.
- Use the existing read-only public `RiseXObservationAdapter` and `HyperliquidObservationAdapter`.
- Use the existing one-route real-data adapter handoff, existing `assemble_route_snapshot()` path, existing source-aware public fee/funding completion, and existing `evaluate_route(route, snapshot, mode)` decision path.
- Report the public evidence used for the one route, including fee cash/source metadata, funding cash/source metadata, existing Entry EV fields, decision status/reasons, and any components that remain `UNKNOWN`.
- Report a deterministic explanation of why the route is or is not publicly ready for later fail-closed live-readiness stages, without adding or mutating route statuses, reject reasons, eligibility, Capture state, ledger state, or live gates.
- Add focused tests for the new report output and fail-closed unknown handling using deterministic injected data or fixtures.
- Update only the source-of-truth docs needed to record the outcome and next handoff.

## Forbidden scope

- No route discovery.
- No route ranking.
- No watchlists.
- No background loops.
- No polling.
- No scheduling.
- No alerts.
- No automatic refresh.
- No adapters or adapter endpoint changes.
- No private endpoints.
- No credentials.
- No API keys or secrets.
- No account balances.
- No exchange account state.
- No account-tier assumptions.
- No fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin rule changes.
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
- No route eligibility mutation.
- No Capture state transitions.
- No route statuses.
- No reject reasons.
- No canary architecture.
- No hold-next-cycle logic.
- No live trading.
- No live trading by default.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second ledger-write path, second replay path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat this as a concrete safe product/runtime reporting task, not as authorization for live trading, private/account endpoints, credentials, account state, orders, sendable exchange requests, execution automation, or financially dangerous actions.
- Keep the report manual and one-route-at-a-time; require explicit route inputs before any public adapter construction.
- Preserve the existing public/read-only adapter boundary. The task may use only the one-shot public observations already required by the existing one-route real-data route flow.
- Preserve the existing single snapshot and decision paths. If a report helper is necessary to retain the assembled snapshot for display, keep it app-layer/reporting-only, delegate through the existing adapter handoff and `evaluate_route()` path, and cover it with focused tests.
- Preserve existing fee and funding owner logic. The report may display source-aware fee/funding values and metadata that already emerge from the existing snapshot path, but it must not add fee/funding cash rules, defaults, account-tier assumptions, or zero fallbacks.
- Preserve missing economics as `UNKNOWN` or `None` display values. Do not turn unknown fee, funding, EV, or readiness evidence into zero or success.
- The readiness conclusion is report-only operator context. It must not add a domain status, mutate `DecisionResult`, change `RouteStatus`, change `RejectReason`, write ledger events, start paper lifecycle, verify funding settlement, reconcile ledgers, plan execution, run guarded live readiness, call approval-boundary execution, or enable live trading.
- Preserve the latest accepted product baseline separately from any current task branch or pending review state.
- Do not mark any task accepted unless explicit reviewer acceptance exists.
- Keep `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Worker policy: one supervised worker required because this is product/runtime reporting work touching a live-readiness-facing operator surface.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned report design is manual, one-route-only, public/read-only, non-trading, source-grounded, one-task/one-branch compliant, preserves existing adapter/snapshot/evaluate/fee/funding owner paths, avoids route discovery/ranking/polling/automation, excludes all hard-stop categories, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer acceptance, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `apps/research_runner/real_data.py` only if a narrow app-layer report helper is necessary to expose the existing assembled snapshot evidence for display.
- Likely `tests/unit/test_cli_main.py`
- Likely `tests/unit/test_real_data_research_runner.py` only if an app-layer report helper is added there.
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused report tests, likely `python3 -m pytest tests/unit/test_cli_main.py tests/unit/test_real_data_research_runner.py`
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
