# Next Task

## Task ID

RX-047 - Product Owner Post-RX-045 Public Runtime Direction Gate

## Objective

After RX-046 is reviewer-accepted, record explicit Product Owner direction supplied through Control Tower or source-of-truth repository docs for exactly one next non-dangerous public/read-only/non-trading live-readiness handoff after the accepted RX-045 manual public readiness report. If explicit direction is absent, ambiguous, unsafe, or reaches hard-stop scope, record that no clarified runtime handoff is available and prepare one narrow clarification handoff instead of inventing route discovery, polling, adapter endpoint changes, private/account endpoints, credentials, account state, orders, sendable exchange request construction, execution automation, or live trading.

## Starting baseline

Start from reviewer-accepted `main` after RX-046 is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-047-product-owner-post-rx-045-public-runtime-direction-gate`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, RX-046 is not explicitly reviewer-accepted and finalized on `main`, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous: source-of-truth clarification only, with no live trading, private/account endpoints, credentials, orders, sendable exchange request construction, automation, account-state access, destructive reset, unsafe scope, or financially dangerous action. Stop before edits unless explicit user approval exists for any hard-stop category.

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

- Inspect the accepted RX-046 outcome, accepted RX-045 public readiness report outcome, current source-of-truth docs, and any explicit Product Owner direction supplied through Control Tower or source-of-truth docs.
- Update only source-of-truth docs needed to record whether exactly one concrete safe public/read-only/non-trading live-readiness handoff is clarified.
- If explicit Product Owner direction clearly identifies one concrete safe later task, prepare exactly that one later task in `NEXT_TASK.md`.
- If Product Owner direction is absent, ambiguous, unsafe, or reaches hard-stop scope, record that conclusion and prepare exactly one narrow clarification handoff in `NEXT_TASK.md`.
- Preserve the latest accepted product baseline separately from pending or current branch work.

## Forbidden scope

- No product/runtime behavior changes.
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

- Treat this as a source-of-truth clarification task, not as authorization for live trading, private/account endpoints, credentials, account state, orders, sendable exchange requests, execution automation, or financially dangerous actions.
- Use repository docs and explicit Product Owner or reviewer evidence only; do not rely on chat memory or broad roadmap implication.
- Preserve reviewer-only acceptance. Do not mark this task or any later task accepted unless explicit reviewer acceptance exists.
- Preserve RX-045 as the latest accepted product baseline unless a later reviewer-accepted product task exists.
- Preserve RX-046 as pending or accepted according to explicit reviewer evidence.
- Keep `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve Control Tower autonomy for ordinary non-dangerous tasks grounded in source-of-truth repository docs.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Worker policy: one supervised worker required because this is repository-governance/source-of-truth work.
- The worker is required for design support before implementation edits and may continue only if Parent explicitly asks for implementation support.
- At DESIGN CHECKPOINT, the worker must answer whether the planned clarification is docs/source-of-truth only, non-dangerous, source-grounded, one-task/one-branch compliant, preserves accepted baseline versus pending review state, keeps `NEXT_TASK.md` to exactly one task, preserves reviewer acceptance, excludes all hard-stop categories, avoids invented runtime scope, and preserves Parent ownership.
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
- Likely `NEXT_TASK.md`

## Required tests

- `python3 scripts/validate_next_task.py`
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
