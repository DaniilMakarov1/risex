# Next Task

## Task ID

RX-069 - Local Paper Session End-To-End Operator Display Smoke Fixture Coverage

## Objective

After RX-068 finalization, add focused deterministic local smoke fixture coverage proving that the accepted local operator package, serial paper-session runtime, explicit report export, display payload, display preview, command-text preview/parser, and payload-backed report renderer can operate as one end-to-end fake-money operator display path.

This is testability coverage only. It must use existing accepted commands and deterministic public-adapter doubles, stay local/manual/fake-money, make no external network calls, and add no production behavior unless a tiny bug fix is strictly required by the smoke and stays inside the accepted owner path.

## Starting baseline

Start from reviewer-accepted `main` after RX-068 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-069-local-paper-session-end-to-end-operator-display-smoke-fixture-coverage`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-068 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, test-only/local/manual/fake-money, and grounded in the accepted fake-money paper trader artifact chain. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Focused deterministic local smoke test coverage proving the accepted local operator/display artifact chain end-to-end.
- Use the existing `build-paper-session-package` command path to create a route-list artifact and package preview/manifest from an explicit local command payload fixture.
- Use the generated route-list artifact through the existing `paper-trade-session --routes-json-path ... --session-report-json-path ...` command path with an explicit local SQLite ledger path and injected deterministic public-adapter doubles.
- Use the existing `build-paper-session-display-payload` command path to create the minimal display payload from the explicit report export.
- Use the existing `build-paper-session-display-command-preview` command path to preview the accepted payload-backed display command.
- Use a local command text fixture plus the existing `build-paper-session-display-command-text-preview` command path to preview the accepted parser command.
- Use the existing `parse-paper-session-display-command-text` command path to create a display payload from exact local command text.
- Use the existing `render-paper-session-report-from-payload` command path to render the report through the accepted payload-backed display path.
- Exercise at least two explicit valid `ENTRY` routes through the generated route-list artifact and accepted serial session flow.
- Cover explicit local package, route-list, preview/manifest, ledger, report, display-payload, display-preview, command-text, command-text-preview, parsed-payload, and payload-backed render artifacts or stdout where applicable.
- Verify deterministic package preview/manifest values, accepted route-list output shape, existing fake paper lifecycle handling, existing ledger ownership, deterministic runtime stdout, and explicit local report export.
- Verify string-or-null economics, known/unknown count semantics, and `aggregate_paper_net_profit_usd=null`.
- Verify no aggregate paper PnL calculation and no unknown-to-zero behavior.
- Test-only fixtures/helpers are allowed only when local to tests, necessary, immediately used, and not product abstractions.
- Update source-of-truth docs for the RX-069 outcome and prepare `NEXT_TASK.md` with exactly one next task.
- Keep `python3 scripts/validate_next_task.py` passing.

## Forbidden scope

- No new user-facing CLI command.
- No behavior changes to existing CLI output outside tests.
- No production route, session, decision, snapshot, economics, paper lifecycle, ledger, report, display, parser, or command path changes unless a tiny bug fix is strictly required by the smoke coverage and stays inside the accepted owner path.
- No parser weakening for accepted boundaries.
- No real Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No alerts or messaging behavior.
- No external network calls.
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

- Reuse the existing accepted commands; do not manually write route lists, run a second session runner, duplicate display behavior, or add new command paths.
- Keep all adapter behavior deterministic through injected public-adapter test doubles so the smoke makes no external network calls.
- Start from an explicit command payload fixture, let `build-paper-session-package` produce the route-list artifact, and feed only that generated route-list artifact to `paper-trade-session`.
- Run `paper-trade-session` with both `--routes-json-path` and `--session-report-json-path`, plus an explicit local SQLite ledger path.
- Build the display payload from the produced report with `build-paper-session-display-payload`.
- Preview the payload-backed display command with `build-paper-session-display-command-preview`.
- Build a command-text preview from an exact local command text fixture with `build-paper-session-display-command-text-preview`.
- Parse that same exact command text into a display payload with `parse-paper-session-display-command-text`.
- Render through `render-paper-session-report-from-payload` using the parsed display payload.
- Assert the generated artifacts and stdout are deterministic enough to prove the accepted operator/display path without locking tests to incidental formatting beyond the accepted command contracts.
- Preserve the distinction between latest accepted baseline, current task branch state, and reviewer acceptance in docs.
- Do not describe RX-069 implementation-complete work as reviewer-accepted.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.
- Use `docs/WORKFLOW.md` and `docs/templates/` for the handoff and final report.
- Control Tower autonomous selection is allowed only because this is non-dangerous test-only/local/manual/fake-money work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: workers optional because this is focused testability coverage using accepted local command paths and deterministic doubles. Parent must classify worker usage before edits.
- Require one supervised worker/subagent if implementation unexpectedly becomes non-trivial architecture-sensitive work, including live-gate, accounting, reconciliation, execution-boundary, ledger contract, safety-critical, broad contract, owner-boundary, or repository-governance changes.
- If a worker is used, the worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- If a worker is used, the worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT before continuing to the next phase.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- `tests/unit/test_cli_paper_session_smoke.py` or the nearest existing focused paper-session CLI smoke test file
- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `IMPLEMENTATION_PLAN.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused new smoke test(s)
- `python3 -m pytest tests/invariant -q`
- `python3 -m pytest -q`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- Focused stale cross-project instruction search
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
