# Next Task

## Task ID

RX-070 - Local Paper Session Operator Display Fail-Closed Smoke Fixture Coverage

## Objective

After RX-069 finalization, add focused deterministic local smoke fixture coverage proving that malformed or unsafe local operator/display fixtures fail closed across the accepted local fake-money paper-session operator display command chain.

This is testability coverage only. It must reuse existing accepted commands and local fixtures, make no external network calls, and add no production behavior unless a tiny owner-path bug fix is strictly required by the smoke and stays inside the accepted owner path.

## Starting baseline

Start from reviewer-accepted `main` after RX-069 finalization. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-070-local-paper-session-operator-display-fail-closed-smoke-fixture-coverage`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-069 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

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

- Focused deterministic local fail-closed smoke test coverage for accepted local operator/display fixture boundaries.
- Prefer extending `tests/unit/test_cli_paper_session_smoke.py` or the nearest existing focused paper-session CLI smoke test file.
- Use existing accepted command paths only, such as `build-paper-session-package`, `build-paper-session-display-payload`, `build-paper-session-display-command-preview`, `build-paper-session-display-command-text-preview`, `parse-paper-session-display-command-text`, and `render-paper-session-report-from-payload`.
- Cover malformed or unsafe local command payload, display payload, display preview input, command text, command-text preview input, parsed payload, or payload-backed render input boundaries where they are relevant to later command-interface testing.
- Assert failures happen before unintended artifact writes, session execution, adapter construction, ledger instantiation/writes, report rendering, report mutation, external network calls, Telegram transport, credentials, live/order/private/account scope, aggregate PnL calculation, unknown-to-zero behavior, or second owner paths.
- Test-local fixtures/helpers are allowed only when local to tests, necessary, immediately used, and not product abstractions.
- Update source-of-truth docs for the task outcome and prepare `NEXT_TASK.md` with exactly one next task.
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

- Reuse existing accepted commands; do not manually implement a second fail-closed parser, package builder, session runner, display renderer, or command path.
- Keep all adapter behavior forbidden or deterministic through test doubles so the smoke makes no external network calls.
- For package-boundary cases, prove malformed local command payload fixtures fail before route-list or preview/manifest artifacts are written and before adapters, ledgers, sessions, or reports are touched.
- For display-boundary cases, prove malformed local display payloads, command text fixtures, or payload-backed render inputs fail before unintended payload/preview artifacts, report rendering, adapters, ledgers, or sessions are touched.
- Where command-text preview is covered, verify preview-only behavior still does not write the intended display payload artifact on failure.
- Assert local artifacts/stdout/stderr enough to prove the fail-closed boundary without locking tests to incidental formatting beyond accepted command contracts.
- Preserve the distinction between latest accepted baseline, current task branch state, and reviewer acceptance in docs.
- Do not describe implementation-complete work as reviewer-accepted.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.
- Use `docs/WORKFLOW.md` and `docs/templates/` for the handoff and final report.
- Control Tower autonomous selection is allowed only because this is non-dangerous test-only/local/manual/fake-money work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: workers optional because this is focused testability coverage using accepted local command paths and deterministic/forbidden doubles. Parent must classify worker usage before edits.
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
