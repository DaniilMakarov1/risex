# Next Task

## Task ID

RX-059 - Post-Local Paper Session Payload Parser Handoff Clarification

## Objective

After RX-058 reviewer acceptance and finalization, inspect the accepted local paper session command payload parser outcome and current source-of-truth docs to identify exactly one next non-dangerous fake-money paper-trader handoff if one is clearly grounded.

If no concrete safe next handoff is grounded, record that conclusion and prepare one narrow Product Owner clarification gate instead of inventing runtime, transport, automation, live, order, private/account, credential, ledger replay/reconciliation, storage migration, or second-owner-path scope.

## Starting baseline

Start from reviewer-accepted `main` after RX-058 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-059-post-local-paper-session-payload-parser-handoff-clarification`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, the remote is wrong, the branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-058 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous, governance/source-of-truth only, and grounded in the accepted fake-money paper-trader testing-support trail. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Inspect the accepted RX-058 parser outcome and current source-of-truth docs.
- Record whether exactly one next non-dangerous fake-money paper-trader handoff is clearly grounded.
- Prepare exactly one next task in `NEXT_TASK.md`.
- Update source-of-truth docs only as needed: likely `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md`.
- Keep RX-058 accepted versus pending state accurate according to explicit reviewer evidence.

## Forbidden scope

- No product/runtime behavior changes.
- No CLI output behavior changes.
- No parser behavior changes.
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
- No aggregate PnL invention.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative live hooks, placeholder live paths, broad refactors, second route model, second session runner, second decision path, second snapshot assembly path, second EV path, second VWAP path, second fee/funding path, second paper lifecycle path, second ledger-write path, second replay path, second reconciliation path, second execution-planning path, or second live execution path.

## Implementation requirements

- Treat the task as governance/source-of-truth only.
- Preserve reviewer-only acceptance: RX-058 branch work is not accepted until explicit reviewer acceptance and finalization on `main`.
- Use the accepted RX-058 outcome, accepted RX-055 through RX-057 baselines, current source-of-truth docs, and Product Owner/Control Tower direction recorded in the repository trail rather than chat memory.
- If exactly one concrete safe next fake-money paper-trader handoff is grounded, prepare that one handoff in `NEXT_TASK.md`.
- If no such handoff is grounded, prepare one narrow Product Owner clarification gate.
- Keep Telegram as later interface direction only unless an exact future task is explicitly approved through the repository gates. Do not add transport, tokens, credentials, network, webhooks, alerts, or messaging.
- Keep `NEXT_TASK.md` to exactly one task and require `python3 scripts/validate_next_task.py` to pass.
- Control Tower autonomous selection is allowed only because this is non-dangerous governance/source-of-truth work grounded in repository docs.
- Live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions require explicit user approval before task selection, creation, execution, fixing, or finalization.
- Worker policy: one supervised worker required.
- The worker is required for design support before implementation edits because this task changes repository-governance handoff state after a product/runtime testing-support task.
- At DESIGN CHECKPOINT, the worker must answer whether the proposed handoff is source-grounded, non-dangerous, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer-only acceptance, avoids runtime behavior changes, excludes Telegram token/network credentials and all hard-stop categories, avoids discovery/ranking/watchlists/polling/background loops/scheduling/alerts, avoids execution automation/planning, avoids live/order/private/account scope, avoids ledger replay/reconciliation/storage migration, avoids new statuses/reasons and second owner paths, and preserves Parent ownership.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and wait for Parent approval or steering before continuing.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if a required worker is unavailable.

## Required files

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
