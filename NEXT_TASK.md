# Next Task

## Task ID

RX-075 - Local Paper Session Run Command Text Preview-To-Runtime Smoke Fixture Coverage

## Objective

Add focused deterministic smoke coverage after the parser-to-runtime smoke task is reviewer-accepted and finalized.

The task should prove that exact local `paper-session-run ...` command text can first be previewed through the accepted `build-paper-session-run-command-text-preview` command without writing package/runtime artifacts, then parsed through the accepted `parse-paper-session-run-command-text` command into the accepted package route-list and package-preview artifacts, and finally run through the accepted `paper-trade-session` runtime/report/display path under deterministic public-adapter doubles. It must be test-only and must not add production behavior, new commands, session automation, Telegram transport, credentials, external network behavior, live/order/private/account scope, aggregate PnL calculation, unknown-to-zero behavior, or second owner paths.

## Starting baseline

Start from reviewer-accepted `main` after the parser-to-runtime smoke task finalization commit. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-075-local-paper-session-run-command-text-preview-to-runtime-smoke-fixture-coverage`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, the parser-to-runtime smoke task is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, test-only, local/manual/fake-money coverage grounded in the accepted paper-session operator/display chain, run-command-text preview builder, run-command-text parser, and parser-to-runtime smoke outcome. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, financially dangerous actions, Telegram transport, bot tokens, webhooks, alerts, messaging behavior, or external network behavior.

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

- Add focused deterministic smoke coverage for the accepted `build-paper-session-run-command-text-preview` command output feeding the accepted `parse-paper-session-run-command-text` parser output and the accepted `paper-trade-session` runtime/report/display path.
- Use injected deterministic public-adapter doubles; do not construct real public adapters or call external networks in the new smoke.
- Reuse accepted command paths only: `build-paper-session-run-command-text-preview`, `parse-paper-session-run-command-text`, `paper-trade-session`, and, if useful for report validation, accepted display/report commands.
- Assert accepted run-command preview shape, accepted route-list shape, accepted package-preview shape, deterministic stdout/artifacts, no package route-list/package-preview/session-report/ledger/runtime writes during previewing, no session-report write during parsing, runtime-owned fake paper lifecycle/ledger behavior only during `paper-trade-session`, string-or-null economics, known/unknown count semantics, `aggregate_paper_net_profit_usd=null`, no aggregate paper PnL calculation, and no unknown-to-zero behavior.
- Update source-of-truth docs for the completed task and the next handoff.
- Keep `NEXT_TASK.md` to exactly one next task and keep `python3 scripts/validate_next_task.py` passing.

## Forbidden scope

- No production code changes.
- No new user-facing CLI command.
- No CLI behavior changes outside test coverage.
- No session execution outside the accepted `paper-trade-session` runtime path under deterministic test doubles.
- No session report/history writes outside the accepted explicit `paper-trade-session --session-report-json-path` path in the smoke.
- No report rendering or display payload writes unless using already accepted display/report commands for validation.
- No parser weakening.
- No broad free-form command parsing.
- No inline route-list command text grammar.
- No production route, decision, snapshot, economics, paper lifecycle, ledger, replay, reconciliation, funding verification, storage, adapter, execution, live-runner, approval-boundary, or order path changes.
- No new route statuses.
- No new reject reasons.
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
- No aggregate PnL invention or calculation.
- No unknown-to-zero behavior.
- No canary architecture.
- No hold-next-cycle logic.
- No weakening, bypassing, or removal of explicit user approval gates.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second report path, second display path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Keep this task test-only unless the accepted docs and reviewer direction explicitly require otherwise.
- Add or update smoke coverage in `tests/unit/test_cli_paper_session_smoke.py`.
- Start from an explicit local command payload fixture and exact local `paper-session-run ...` command text.
- Use `build-paper-session-run-command-text-preview` to write the accepted run-command preview artifact from the command text.
- Verify previewing reads/writes only the accepted local artifacts for that preview boundary and does not write the intended route-list path, package-preview path, session-report path, ledger path, display payload path, or runtime artifacts.
- Use `parse-paper-session-run-command-text` to write the accepted package route-list and package-preview artifacts from the same command text.
- Verify parsing reads/writes only the accepted local artifacts for that parser boundary and does not write the intended session-report path.
- Feed only the generated route-list artifact into `paper-trade-session --routes-json-path ... --session-report-json-path ...` under deterministic public-adapter doubles and an explicit local SQLite ledger path.
- Verify the runtime path still uses accepted decision, paper lifecycle, ledger, report, and optional display owner paths.
- Preserve accepted unknown/null and no-aggregate-PnL semantics; do not add zero placeholders.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/manual/fake-money test coverage grounded in source-of-truth repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, financially dangerous actions, Telegram transport, bot tokens, webhooks, alerts, messaging behavior, and external network behavior require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: workers optional. This is test-only smoke coverage and should not require a worker unless Parent identifies non-trivial architecture-sensitive scope.
- Parent owns final diff review, validation, commit, push, and final report.
- Workers, if used, must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- Workers, if used, must not commit, push, merge, approve work, or start unrelated scope.

## Required files

- tests/unit/test_cli_paper_session_smoke.py
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md

## Required tests

- `python3 scripts/validate_next_task.py`
- `python3 -m pytest tests/unit/test_cli_main.py -q`
- `python3 -m pytest tests/unit/test_cli_paper_session_smoke.py -q`
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
