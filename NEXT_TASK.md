# Next Task

## Task ID

RX-063 - Local Paper Session Display Payload Fixture Builder

## Objective

After RX-062 reviewer acceptance and finalization, add one local-only, manually invoked display payload fixture builder for paper session report display commands.

The builder must consume one explicit local session report JSON path intended for an already-written RX-057 report and one explicit local display payload JSON output path, then write a deterministic payload fixture accepted by the RX-062 display command payload parser. It must stay display-preparation only and must not add Telegram transport, network behavior, credentials, messaging, session execution, adapter construction, ledger writes, report/result mutation, execution automation, live/order/private/account scope, aggregate PnL calculation, or unknown-to-zero behavior.

## Starting baseline

Start from reviewer-accepted `main` after RX-062 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-063-local-paper-session-display-payload-fixture-builder`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-062 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, product/runtime testing-support only, local/manual/fake-money only, and grounded in the accepted RX-057 report export, RX-061 local display renderer, and RX-062 local display payload parser trail plus explicit Product Owner direction to continue implementing needed fake-money paper trader steps. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add one local/manual display payload fixture builder in the CLI app layer.
- Consume one explicit local session report JSON path and one explicit local display payload JSON output path.
- Write at most one explicit local display payload fixture artifact accepted by the RX-062 parser.
- Keep the payload shape minimal and exact: `schema_version=1` and `session_report_json_path`.
- Optionally validate the report shape before writing only by reusing the accepted RX-061 report-display validation path without printing display output.
- Validate malformed inputs before writing the payload artifact.
- Print deterministic local stdout summary values such as display payload path and session report path.
- Preserve RX-061/RX-062 report-display behavior: copied report values only if report validation is reused, string-or-null economics, `aggregate_paper_net_profit_usd=null`, no aggregate PnL calculation, and no unknown-to-zero behavior.
- Add focused tests for accepted fixture writing, malformed input rejection before artifact write, deterministic payload output, no session execution/adapters/ledger writes/report mutation, no Telegram/network/credentials/live/order/private/account/discovery/ranking/watchlists/polling/scheduling/alerts, no aggregate PnL calculation, and no unknown-to-zero behavior.
- Update source-of-truth docs for the outcome and next handoff.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.

## Forbidden scope

- No session execution.
- No adapter construction.
- No ledger instantiation or ledger event writes.
- No session report/history result writes or mutation.
- No product behavior outside the explicit local display payload fixture builder or manually invoked fixture command.
- No existing CLI output behavior changes except any new explicitly invoked command.
- No parser weakening for RX-055, RX-057, RX-058, RX-060, RX-061, or RX-062 boundaries.
- No Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No external network calls.
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
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second report path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Keep the builder local-only, manually invoked, deterministic, and fake-money paper testing-support only.
- Keep ownership in the CLI app layer unless existing local helpers clearly belong nearby.
- The builder must require explicit local input and output paths; it must not infer output destinations.
- The output payload must contain only `schema_version` and `session_report_json_path`.
- The output payload must not contain route lists, decisions, paper outcomes, economics, summaries, ledger events, aggregate PnL fields, transport fields, credentials, network destinations, private/account data, sendable requests, order payloads, or execution intent.
- If report validation is included, reuse the accepted RX-061 display validation path and do not print display output during fixture building.
- The builder must not recompute decisions, paper outcomes, economics, summary counts, ledger events, or aggregate PnL.
- Preserve unknown values exactly as `None`/`null`/missing display values rather than converting them to zero, success, or profitability.
- Preserve `aggregate_paper_net_profit_usd` as null/unknown; do not sum route PnL.
- Keep Telegram as later interface/display direction only. This task may prepare local payload fixtures suitable for later Telegram command adaptation, but it must not add real Telegram transport, bot tokens, credentials, webhooks, alerts, messaging behavior, or external network calls.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/manual/fake-money testing-support work grounded in repository docs plus explicit Product Owner direction.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task adds a local artifact-writing command boundary adjacent to paper-session display/report artifacts.
- At DESIGN CHECKPOINT, the worker must answer whether the proposed builder is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, consumes only explicit local report paths and output paths, writes only the RX-062 display payload fixture shape, avoids session execution, avoids adapter construction, avoids ledger writes, avoids report/history result writes or mutations, excludes Telegram token/network credentials and all hard-stop categories, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids execution automation/planning, avoids live/order/private/account scope, avoids ledger replay/reconciliation/storage migration, avoids new statuses/reasons and second owner paths, preserves unknown-as-missing/no-aggregate-PnL behavior, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

- Likely `apps/cli/main.py`
- Likely `apps/cli/paper_session_payloads.py` only if a tiny helper belongs beside existing payload helpers
- Likely `tests/unit/test_cli_main.py`
- Likely `tests/unit/test_paper_session_payloads.py` only if a helper is added or reused directly
- Likely `README.md`
- Likely `ARCHITECTURE.md`
- Likely `PRODUCT_INVARIANTS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `STATUS.md`
- Likely `DECISIONS.md`
- `NEXT_TASK.md`
- Other source-of-truth docs only if strictly necessary

## Required tests

- `python3 scripts/validate_next_task.py`
- Focused unit tests for the local paper session display payload fixture builder.
- Focused docs/search checks proving the local display payload fixture builder is the current next task and not a Product Owner/governance clarification gate.
- Focused docs/search checks proving no Telegram/live/order/private/account hard-stop scope was introduced.
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
