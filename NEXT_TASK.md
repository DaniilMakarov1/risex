# Next Task

## Task ID

RX-035 - Post-RX-034 Roadmap Handoff Cleanup

## Objective

After `RX-034` reviewer acceptance, record the roadmap selection audit outcome and prepare exactly one next RX handoff without inventing product or runtime scope. If source-of-truth repository docs still do not clearly ground a concrete non-dangerous product task, keep the work metadata-only and prepare one roadmap cleanup or clarification handoff rather than promoting inferred product work.

## Starting baseline

Start from reviewer-accepted `main` after `RX-034` is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-035-post-rx-034-roadmap-handoff-cleanup`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

If Control Tower selected this task autonomously, verify from the source-of-truth repository docs that the task is non-dangerous. Stop before edits unless explicit user approval exists for any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.

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

- Repository governance and handoff metadata needed to record the RX-034 audit outcome and preserve exactly one next RX task.
- `STATUS.md`
- `IMPLEMENTATION_PLAN.md`
- `DECISIONS.md`
- `NEXT_TASK.md`
- `AGENTS.md`, `docs/WORKFLOW.md`, or `docs/templates/` only if strictly necessary to keep workflow language consistent.

## Forbidden scope

- No product behavior changes.
- No dashboard behavior changes.
- No route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, or auto-refresh.
- No venue adapters, market-data calls, private endpoints, credentials, account balances, exchange account state, or network-dependent tests.
- No order placement, sendable exchange request construction, order cancellation, order status fetching, or execution automation.
- No route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate bundle checking, execution planning, guarded live runner execution, or approval-boundary execution.
- No ledger writes, storage migrations, replay changes, paper lifecycle changes, route eligibility mutation, or Capture state transitions.
- No EV, fee, funding, VWAP/liquidity, basis, spread, price-impact, slippage, max-level, hidden-buffer, or safety-margin filters.
- No new route statuses, reject reasons, canary architecture, hold-next-cycle logic, or live trading by default.
- No new functions, classes, dataclasses, enums, modules, wrappers, config values, trace fields, future hooks, or contracts.
- No weakening, bypassing, or removal of explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- No speculative product hooks, runtime hooks, placeholder live paths, or broad refactors.

## Implementation requirements

- Treat this as a governance/metadata-only post-audit handoff cleanup.
- Use only source-of-truth repository docs for task selection and handoff cleanup: `NEXT_TASK.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, `AGENTS.md`, `docs/WORKFLOW.md`, and required templates.
- Control Tower selected this task autonomously through the RX-034 fallback path because the source-of-truth docs did not clearly ground a concrete post-RX-034 product/runtime task.
- Do not ask the user to name or authorize ordinary safe metadata-only cleanup work.
- Stop for explicit user approval before selecting, creating, running, fixing, or finalizing any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions.
- Ask the user only if candidate selection reaches a hard-stop category, unsafe scope, financially dangerous action, destructive reset, or genuine product/architecture fork that cannot be resolved from repository docs.
- If candidate tasks are still not clearly grounded in source-of-truth docs, prepare exactly one non-product roadmap audit, cleanup, or clarification handoff rather than inventing product scope.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve reviewer acceptance as the only way to mark a task accepted.
- Preserve Parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Preserve worker/subagent checkpoint requirements for non-trivial architecture-sensitive work.
- Do not add product code, runtime code, tests for product behavior, or new abstractions.
- Worker policy: one supervised worker required for design support because this is repository-governance work.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and answer whether the planned handoff cleanup is source-of-truth grounded, non-dangerous or explicitly approval-gated, one-task/one-branch compliant, reviewer-acceptance compliant, Parent-owned, and exactly-one-task valid.
- The worker must wait for Parent approval or steering after DESIGN CHECKPOINT before any implementation edits continue.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if the required worker is unavailable.

## Required files

- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`
- Other governance docs only if strictly necessary.
- Do not touch product code.

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
