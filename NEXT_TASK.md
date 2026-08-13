# Next Task

## Task ID

RX-048 - Structured JSON Stdout Public Readiness Report Output

## Objective

Add one opt-in structured JSON stdout output mode for the existing manual one-route public readiness report on the existing `real-data-route` CLI flow. The JSON mode must serialize the same public/read-only report evidence already available to the accepted manual report for one explicitly supplied RiseX plus Hyperliquid route, while preserving existing text output and without adding file writes, ledger writes, storage, route discovery, polling, adapter endpoint changes, private/account endpoints, credentials, account state, orders, sendable exchange request construction, execution automation, or live trading.

## Starting baseline

Start from reviewer-accepted `main` after RX-047 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-048-structured-json-stdout-public-readiness-report-output`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-047 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: opt-in public/read-only stdout formatting only, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, execution automation, account-state access, destructive reset, unsafe scope, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

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

- Inspect the accepted manual public readiness report outcome, current source-of-truth docs, and explicit Product Owner and Control Tower direction recorded by RX-047.
- Add one opt-in JSON stdout mode for the existing `real-data-route` manual public readiness report path, using the existing explicit one-route CLI inputs.
- Preserve the existing default `real-data-route` one-decision text output and existing `--public-readiness-report` text output unless JSON output is explicitly requested.
- Reuse the existing public read-only `RiseXObservationAdapter` and `HyperliquidObservationAdapter`, existing one-route adapter handoff, existing retained snapshot/report helper, existing source-aware public fee/funding completion, and existing `evaluate_route(route, snapshot, mode)` path.
- Serialize only existing report evidence already available to the manual report: route identity, decision status/reasons, Entry EV fields, source-aware public funding and fee evidence, deterministic unknown components, and the display-only public-readiness conclusion.
- Preserve unknown values as unknown or null with source/metadata context; do not convert unknown fee, funding, or Entry EV values into zero or success.
- Add focused tests for the JSON output mode and preservation of existing text output.
- Update source-of-truth docs and `NEXT_TASK.md` for the next single task after completion.

## Forbidden scope

- No file writes from the report output.
- No product decision changes.
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

- Treat this as a narrow public/read-only reporting-output task, not as authorization for live trading, private/account endpoints, credentials, account state, orders, sendable exchange requests, execution automation, or financially dangerous actions.
- Use repository docs, accepted code paths, and explicit Product Owner or reviewer evidence only; do not rely on chat memory or broad roadmap implication.
- Keep JSON output downstream of existing report evidence and existing `DecisionResult`/retained snapshot values.
- Keep JSON deterministic enough for tests, including stable keys and deterministic serialization of decimals, timestamps, enums/statuses/reasons, unknown values, and metadata.
- Emit JSON to stdout only. Do not create files, write ledgers, persist storage state, or mutate domain/runtime state.
- Preserve reviewer-only acceptance. Do not mark this task or any later task accepted unless explicit reviewer acceptance exists.
- Preserve the latest accepted product baseline separately from current branch work.
- Keep `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Worker policy: one supervised worker required because this task touches a live-readiness reporting boundary and must preserve one-route/report ownership.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned JSON output is opt-in, stdout-only, public/read-only, one-route-only, source-grounded in the accepted manual report, downstream of existing report evidence, preserves existing text output, keeps unknowns from becoming zero/success, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer acceptance, excludes all hard-stop categories, avoids invented runtime scope, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `tests/unit/test_cli_main.py`
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/unit/test_cli_main.py`
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
