# Next Task

## Task ID

RX-068 - Local Paper Session Package-To-Runtime Smoke Fixture Coverage

## Objective

After RX-067 reviewer acceptance and finalization, add focused deterministic local smoke fixture coverage proving that the accepted local operator-package builder output can feed the accepted `paper-trade-session` fake-money runtime and report/display path.

The coverage should exercise only existing local/manual commands and owner paths: build a route-list artifact through the accepted `build-paper-session-package` command, run that generated route-list through the accepted `paper-trade-session --routes-json-path ... --session-report-json-path ...` command under injected deterministic public-adapter doubles, and validate the resulting report through the accepted report display path if useful. This is testability coverage only: it should not add a new user-facing command, change existing CLI behavior, or add product behavior outside tests and source-of-truth docs.

## Starting baseline

Start from reviewer-accepted `main` after RX-067 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-068-local-paper-session-package-to-runtime-smoke-fixture-coverage`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-067 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, testability only, local/manual/fake-money only, and grounded in the accepted paper-session operator-package, runtime, report, and display paths. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add focused local smoke fixture coverage connecting existing `build-paper-session-package` output to the existing `paper-trade-session` command path.
- Use injected deterministic public-adapter behavior or test doubles to avoid external network calls during smoke coverage.
- Exercise at least two explicit valid `ENTRY` routes through the generated route-list artifact and accepted serial session flow.
- Cover explicit local package artifacts, deterministic package preview/manifest values, accepted route-list output shape, existing fake paper lifecycle handling, existing ledger ownership, deterministic runtime stdout, and explicit local report export through `--session-report-json-path`.
- Optionally validate the produced report through the accepted `render-paper-session-report` or payload-backed display path if this stays focused and does not duplicate display behavior.
- Verify string-or-null economics, known/unknown count semantics, and `aggregate_paper_net_profit_usd=null`.
- Verify no aggregate paper PnL calculation and no unknown-to-zero behavior.
- Add test-only fixtures/helpers only when they are local to tests, necessary for the smoke coverage, immediately used, and not product abstractions.
- Update source-of-truth docs for the outcome and next handoff.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.

## Forbidden scope

- No new user-facing CLI command.
- No behavior changes to existing CLI output outside tests.
- No production route/session/decision/snapshot/economics/paper lifecycle/ledger/report/display path changes unless a tiny bug fix is strictly required by the smoke coverage and stays inside the accepted owner path.
- No parser weakening for accepted paper-session route-list, command payload, report, display payload, command preview, command text, or command-text preview boundaries.
- No real Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No external network calls in the new smoke coverage.
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
- No aggregate PnL invention or calculation.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second report path, second display path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Keep the task as local deterministic testability coverage for existing fake-money paper session operator-package and runtime commands.
- Prefer test-only monkeypatching or injected deterministic adapter doubles over production code changes.
- If a production bug is revealed, keep the fix narrow, inside the accepted owner path, and cover it with a focused test; do not broaden the task into feature work.
- The smoke coverage must not call real networks or depend on external venue availability.
- The smoke coverage must use explicit local command-payload, generated route-list, preview/manifest, ledger, report, and any display payload paths.
- The tested package step must reuse the accepted `build-paper-session-package` command path rather than writing route lists directly.
- The tested runtime step must reuse the accepted `paper-trade-session` command path rather than creating a second session runner.
- The tested decision path must remain the accepted one-route public decision/evaluate path as reached by the current session implementation; do not add a second decision path.
- The tested fake paper handling must remain downstream of existing `run_paper_lifecycle()` behavior; do not add a second paper lifecycle path.
- Ledger evidence must remain behind existing `core/accounting/ledger.py` ownership and optional SQLite persistence must remain through the existing storage contract.
- Preserve unknown values exactly as `None`/`null`/missing display values in existing report/display layers rather than converting them to zero, success, or profitability.
- Preserve `aggregate_paper_net_profit_usd` as null/unknown in report/display layers; do not sum route PnL.
- Keep Telegram as later interface/display direction only. This task must not add real Telegram transport, bot tokens, credentials, webhooks, alerts, messaging behavior, or external network calls.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/fake-money testability work grounded in repository docs plus explicit Product Owner direction.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: workers optional.
- Parent owns scope, final diff review, validation, commit, push, and final report.
- If a worker is used, it must not commit, push, merge, approve work, or start unrelated scope, and Parent must review its output before accepting it.

## Required files

- Likely `tests/unit/test_cli_main.py` or an appropriately scoped existing/new test file for CLI smoke coverage.
- Likely source-of-truth docs: `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Production files only if a narrow bug fix is strictly required by the smoke coverage and remains inside the accepted owner path.

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused smoke test for the accepted `build-paper-session-package` output feeding the existing `paper-trade-session` command with multiple explicit routes and deterministic injected public-adapter observations.
- Focused assertions for generated route-list shape, package preview/manifest values, deterministic runtime stdout, explicit local report export, existing ledger event counts/types, known/unknown count semantics, string-or-null economics, `aggregate_paper_net_profit_usd=null`, no aggregate PnL calculation, and no unknown-to-zero behavior.
- Focused assertions that the smoke coverage performs no external network calls and introduces no Telegram/live/order/private/account/discovery/ranking/watchlists/polling/scheduling/alerts scope.
- Focused docs/search checks proving the local package-to-runtime smoke fixture coverage is the current next task and not another display-only or governance clarification gate.
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
