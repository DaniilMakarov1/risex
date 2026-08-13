# Next Task

## Task ID

RX-066 - Local Paper Session Display Command Text Preview Manifest

## Objective

After RX-065 reviewer acceptance and finalization, add one local-only, manually invoked paper session display command text preview manifest builder for later Telegram-style command interface testing without real Telegram transport or credentials.

The preview builder should consume one explicit local display command text fixture path, one explicit intended local display payload JSON path, and one explicit local preview/manifest JSON output path. It should validate the command text through the accepted RX-065 parser, validate the generated display payload through the accepted RX-062 parser, then write at most one descriptive local preview/manifest artifact for the exact manual `parse-paper-session-display-command-text` command plan. It must not write the display payload artifact itself, read or render report JSON, execute sessions, construct adapters, instantiate ledgers, write ledger events, mutate reports, send messages, call networks, add Telegram transport, add credentials, add live/order/private/account scope, calculate aggregate PnL, or turn unknowns into zero.

## Starting baseline

Start from reviewer-accepted `main` after RX-065 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-066-local-paper-session-display-command-text-preview-manifest`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-065 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, product/runtime testing-support only, local/manual/fake-money only, and grounded in the accepted RX-061 local display renderer, RX-062 local display payload parser, RX-063 local display payload fixture builder, RX-064 local display command preview builder, and RX-065 local display command text parser trail plus explicit Product Owner direction to continue implementing needed fake-money paper trader steps toward serial testing and a later Telegram-ready local command interface. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Add one local/manual paper session display command text preview manifest builder in the CLI app layer.
- Consume one explicit local command text fixture path, one explicit intended local display payload JSON path, and one explicit local preview/manifest JSON output path.
- Validate the command text through the accepted RX-065 command text parser before artifact write.
- Validate the generated display payload through the accepted RX-062 parser before artifact write.
- Write at most one explicit local preview/manifest JSON artifact.
- The preview/manifest may contain only descriptive local testing fields: `schema_version=1`, the command text fixture path, the intended display payload path, the normalized session report path, and the exact manual `parse-paper-session-display-command-text --paper-session-display-command-text-path ... --display-payload-json-path ...` command plan as argv plus robustly quoted text.
- The command must not write the display payload artifact itself.
- Print deterministic local stdout summary values such as command text fixture path, intended display payload path, preview/manifest path, and session report path.
- Preserve RX-061/RX-062/RX-063/RX-064/RX-065 display behavior: copied report values only if a later explicit render command is run, string-or-null economics, `aggregate_paper_net_profit_usd=null`, no aggregate PnL calculation, and no unknown-to-zero behavior.
- Add focused tests for accepted command text preview manifest generation, quoted paths with spaces, malformed command rejection before artifact write, deterministic output, no display payload write, no report read/rendering, no session execution/adapters/ledger writes/report mutation, no Telegram/network/credentials/live/order/private/account/discovery/ranking/watchlists/polling/scheduling/alerts, no aggregate PnL calculation, and no unknown-to-zero behavior.
- Update source-of-truth docs for the outcome and next handoff.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.

## Forbidden scope

- No real Telegram transport.
- No Telegram bot tokens.
- No webhooks.
- No external network calls.
- No alerts or messaging behavior.
- No credentials.
- No API keys or secrets.
- No display payload artifact write by the preview command.
- No report rendering.
- No report JSON reading.
- No session execution.
- No adapter construction.
- No ledger instantiation or ledger event writes.
- No session report/history result writes or mutation.
- No product behavior outside the explicit local display command text preview manifest builder or manually invoked preview command.
- No existing CLI output behavior changes except any new explicitly invoked command.
- No parser weakening for RX-055, RX-057, RX-058, RX-060, RX-061, RX-062, RX-063, RX-064, or RX-065 boundaries.
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

- Keep the preview builder local-only, manually invoked, deterministic, and fake-money paper testing-support only.
- Keep ownership in the CLI app layer unless a tiny helper beside existing payload helpers is clearly cleaner and immediately used.
- The preview builder must require explicit local input and output paths; it must not infer output destinations.
- The command text validation must reuse the accepted RX-065 parser rather than duplicating or weakening its exact grammar.
- The generated display payload validation must reuse the accepted RX-062 parser before writing the preview/manifest.
- The preview/manifest must be descriptive only. It must not contain route lists, decisions, paper outcomes, economics, summaries, ledger events, aggregate PnL fields, Telegram/chat/user IDs, transport fields, credentials, network destinations, private/account data, sendable requests, order payloads, or execution intent.
- The preview builder must not read or validate the referenced report JSON.
- The preview builder must not call the RX-061 renderer, RX-062 render wrapper, RX-063 display payload builder, or RX-064 display command preview builder.
- The preview builder must not write the display payload artifact; it may only preview the later explicit parser command that would write that payload.
- The preview builder must not recompute decisions, paper outcomes, economics, summary counts, ledger events, or aggregate PnL.
- Preserve unknown values exactly as `None`/`null`/missing display values in existing report/display layers rather than converting them to zero, success, or profitability.
- Preserve `aggregate_paper_net_profit_usd` as null/unknown in report/display layers; do not sum route PnL.
- Keep Telegram as later interface/display direction only. This task may prepare local command-text previewing suitable for later Telegram command adaptation, but it must not add real Telegram transport, bot tokens, credentials, webhooks, alerts, messaging behavior, or external network calls.
- Control Tower autonomous selection is allowed only because this is non-dangerous local/manual/fake-money testing-support work grounded in repository docs plus explicit Product Owner direction.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task adds a local artifact-writing preview boundary adjacent to paper-session display command text artifacts.
- At DESIGN CHECKPOINT, the worker must answer whether the proposed preview builder is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, consumes only explicit local command text fixture paths, intended display payload output paths, and preview output paths, writes only a descriptive local preview/manifest artifact, avoids display payload writes, avoids report reading/rendering, avoids session execution, avoids adapter construction, avoids ledger writes, avoids report/history result writes or mutations, excludes Telegram token/network credentials and all hard-stop categories, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids execution automation/planning, avoids live/order/private/account scope, avoids ledger replay/reconciliation/storage migration, avoids new statuses/reasons and second owner paths, preserves unknown-as-missing/no-aggregate-PnL behavior, and preserves Parent ownership.
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
- Focused unit tests for the local paper session display command text preview manifest builder.
- Focused docs/search checks proving the local display command text preview manifest is the current next task and not a Product Owner/governance clarification gate.
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
