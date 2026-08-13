# Next Task

## Task ID

RX-057 - Manual Paper Session Report History Export

## Objective

After RX-056 reviewer acceptance and finalization, add an explicit, manually invoked local JSON report/history export for `paper-trade-session` session results.

The export must use explicit local output paths only and may use only the existing session outcomes and paper ledger events already produced through the RX-055 manual serial paper session owner paths. It must provide a deterministic JSON schema suitable for later Telegram command/display adapter work, but it must not add Telegram transport, bot tokens, webhooks, messaging, alerts, credentials, or network behavior.

The task must preserve the RX-055 route-list cap of 25 exact explicit `ENTRY` routes, preserve known/unknown/null semantics and count-only summary fields, keep unknown values from becoming zero, and avoid inventing aggregate paper PnL.

## Starting baseline

Start from reviewer-accepted `main` after RX-056 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-057-manual-paper-session-report-history-export`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-056 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, manual, fake-money paper-trader product/runtime work only. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add an explicit, manually invoked local JSON report/history export for `paper-trade-session` session results.
- Require explicit local output path input for any report/history artifact write.
- Use only existing `paper-trade-session` route inputs, session outcomes, and paper ledger events already produced through RX-055 owner paths.
- Produce a deterministic JSON schema suitable for later Telegram command/display adapter consumption without implementing Telegram transport, credentials, messaging, alerts, webhooks, or network calls.
- Preserve the RX-055 route-list cap of 25 exact explicit `ENTRY` routes.
- Preserve known/unknown/null semantics for Entry EV, paper expected funding, paper total fees, decision net profit, and paper net profit.
- Preserve count-only known/unknown summary fields.
- Keep unknown values unknown/null rather than zero.
- Keep aggregate paper PnL absent or explicit `None`; do not infer aggregate profitability.
- Reuse the existing decision, snapshot, economics, fake paper lifecycle, ledger, and optional explicit local SQLite ownership boundaries.
- Add focused tests and source-of-truth documentation updates for the report/history export.

## Forbidden scope

- No Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No external Telegram network calls.
- No alerts or messaging behavior.
- No credentials.
- No API keys or secrets.
- No live trading.
- No live trading by default.
- No real exchange order placement.
- No order cancellation.
- No order status fetching.
- No private endpoints.
- No account endpoints.
- No exchange account state.
- No account balances.
- No account-tier assumptions.
- No sendable exchange request construction.
- No order payload construction.
- No execution automation.
- No execution planning.
- No guarded live runner execution.
- No approval-boundary execution.
- No route discovery.
- No route ranking.
- No watchlists.
- No polling.
- No background loops.
- No scheduling.
- No alerts.
- No automatic refresh.
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
- No aggregate PnL invention.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat the task as the single next product/runtime task.
- Preserve reviewer-only acceptance: RX-056 branch work is not accepted until explicit reviewer acceptance and finalization on `main`.
- Use the accepted RX-056 outcome, accepted RX-055 baseline, current source-of-truth docs, and Product Owner/Control Tower direction recorded in the repository trail rather than chat memory.
- Keep the export manual and explicit-local-path-only; no artifact should be written when the operator does not provide an output path.
- Keep the report/history layer downstream of the existing serial session data. Do not create a second session runner, second route model, second decision path, second snapshot path, second EV path, second economics path, second paper lifecycle path, second ledger-write path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.
- Keep JSON output deterministic across repeated runs with the same inputs, session outcomes, and ledger events.
- Preserve Entry EV, paper expected funding, paper total fees, decision net profit, and paper net profit as known/unknown/null fields. Unknowns must not become zero, `0`, `"0"`, success, profitability, or implied PnL.
- Preserve count-only summary semantics from RX-055, including known/unknown counts.
- Keep aggregate paper PnL absent or explicit `None`; do not add summed paper PnL.
- Keep Telegram as later interface direction only. The JSON schema may be suitable for later command/display adaptation, but this task must not add transport, tokens, credentials, network, webhooks, alerts, or messaging.
- Control Tower autonomous selection is allowed only because this is non-dangerous fake-money paper-trader product/runtime work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker is required.
- The worker is required for design support before implementation edits because this task touches product/runtime CLI/reporting behavior downstream of session outcomes and ledger events.
- At DESIGN CHECKPOINT, the worker must answer whether the report/history export direction is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, uses explicit local output paths only, uses existing session outcomes and paper ledger events only, preserves the RX-055 25-route explicit `ENTRY` cap, preserves known/unknown/null and count-only semantics, avoids aggregate PnL invention, excludes Telegram token/network credentials and all hard-stop categories, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
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
- `NEXT_TASK.md`
- Other files only if strictly necessary for the explicit local JSON report/history export

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused tests covering deterministic JSON report/history output.
- Focused tests covering explicit output path behavior.
- Focused tests proving no output artifact is written when the output path is absent.
- Focused tests preserving RX-055 count-only known/unknown summary fields.
- Focused tests proving unknown/null values do not become zero.
- Focused tests proving aggregate paper PnL is not invented.
- Focused doc/search checks proving no Telegram/live/order/private/account hard-stop scope was introduced.
- Focused search checks proving no route discovery, ranking, watchlists, polling, background loops, scheduling, alerts, storage migration, replay, reconciliation, or second owner path was introduced.
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
