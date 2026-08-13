# Next Task

## Task ID

RX-073 - Local Paper Session Run Command Text Parser

## Objective

Add one local-only, manually invoked parser command for exact paper-session run command text after the run-command-text preview builder is reviewer-accepted and finalized.

The task should parse the same exact local `paper-session-run ...` command text accepted by the RX-072 preview builder, validate the referenced local paper-session command payload fixture through the accepted payload boundary, and write only the accepted package route-list and package-preview artifacts described by the command text. It must not run sessions, write session reports, render displays, send messages, call networks, add Telegram transport or credentials, automate execution, or enter live/order/private/account scope.

## Starting baseline

Start from reviewer-accepted `main` after the RX-072 finalization commit. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-073-local-paper-session-run-command-text-parser`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-072 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, local-only, manually invoked, fake-money testing-support work grounded in the accepted paper-session operator/display chain and the RX-072 preview-builder outcome. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, financially dangerous actions, Telegram transport, bot tokens, webhooks, alerts, messaging behavior, or external network behavior.

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

- Add one local/manual CLI command that reads an explicit local paper-session run command text fixture and writes only the accepted local package route-list and package-preview artifacts described by that command text.
- Reuse the accepted RX-072 exact command-text parser helper and the accepted RX-058 command payload route-list validation boundary.
- Reuse the accepted package preview shape and route-list artifact shape already produced by `build-paper-session-package`; do not create a second package artifact model.
- Add focused tests for accepted parser output, malformed command text, malformed referenced payload, explicit path requirements, collision/no-write behavior, forbidden runtime/transport/live/account/order scope, no aggregate PnL fields, and no unknown-to-zero placeholders.
- Update source-of-truth docs for the completed task and the next handoff.
- Keep `NEXT_TASK.md` to exactly one next task and keep `python3 scripts/validate_next_task.py` passing.

## Forbidden scope

- No session execution.
- No session report/history writes.
- No report rendering or display payload writes.
- No run-command-text preview artifact writes unless strictly reusing accepted package preview output described by the command text.
- No production route, decision, snapshot, economics, paper lifecycle, ledger, replay, reconciliation, funding verification, storage, adapter, execution, live-runner, approval-boundary, or order path changes.
- No parser weakening.
- No broad free-form command parsing.
- No inline route-list command text grammar.
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

- Keep all command-text parsing in the CLI app layer. Reuse the accepted `paper_session_package_command_paths_from_run_command_text()` helper.
- The parser command must be named `parse-paper-session-run-command-text`.
- The command must require explicit `--paper-session-run-command-text-path`.
- The command must read only the command text fixture and the referenced local paper-session command payload fixture.
- The command must validate the parsed command text before reading the referenced command payload fixture.
- The command must validate the referenced payload through the accepted `paper_session_route_list_from_command_payload()` boundary before writing any artifact.
- The command may write only the referenced route-list output path and referenced package-preview output path from the parsed command text.
- The command must not write the referenced session-report path.
- The command must reject local output path collisions before payload reading and before writing, including collisions among route-list output path, package-preview output path, and intended session-report path.
- The route-list artifact must contain only the accepted explicit route-list dictionaries returned by the payload parser.
- The package-preview artifact must preserve the accepted `build-paper-session-package` preview shape and manual `paper-trade-session --routes-json-path ... --session-report-json-path ...` command plan.
- Preserve accepted unknown/null and no-aggregate-PnL semantics by omission; do not add zero placeholders.
- Use focused tests in `tests/unit/test_cli_main.py` and smoke coverage in `tests/unit/test_cli_paper_session_smoke.py` only if the smoke coverage is needed to prove the local fail-closed boundary.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/manual/fake-money testing-support work grounded in source-of-truth repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, financially dangerous actions, Telegram transport, bot tokens, webhooks, alerts, messaging behavior, and external network behavior require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker/subagent required for design support because this is command-interface parsing adjacent to fake-money paper-session operator handoff boundaries.
- The worker must answer whether the parser command is grounded in the accepted preview-builder outcome, whether writing the accepted package artifacts can remain local-only and non-dangerous, whether any hard-stop category requires explicit user approval, and whether this risks duplicating existing package/session/report/display owner paths.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- If the worker continues beyond design support, it must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT before continuing to the next phase.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- apps/cli/main.py
- apps/cli/paper_session_payloads.py
- tests/unit/test_cli_main.py
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
