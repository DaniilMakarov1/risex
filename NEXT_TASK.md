# Next Task

## Task ID

RX-033 — Control Tower Autonomous Task Selection Governance

## Objective

Update repository workflow/governance docs only so Control Tower may autonomously select, create, run, review, fix, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task. Preserve explicit user approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions.

## Starting baseline

Start from reviewer-accepted `main` after the Product Owner roadmap authorization gate is finalized. Before edits, verify exact local `HEAD`, `main`, and `origin/main` values from git state instead of trusting chat memory.

## Branch

Create and work on `task/rx-033-control-tower-autonomous-task-selection-governance`. Do not implement on `main`.

## Before changing files

Run the repository preflight from `AGENTS.md`. Stop without edits if the worktree is dirty, remote is wrong, branch is wrong, `origin/HEAD` is not `origin/main`, `HEAD` does not match the accepted starting baseline, or unrelated branch work would be mixed into this task.

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

- Governance and workflow docs needed to define Control Tower autonomous task selection for future non-dangerous RX tasks.
- `AGENTS.md`
- `docs/WORKFLOW.md`
- `docs/templates/`
- `STATUS.md`
- `IMPLEMENTATION_PLAN.md`
- `DECISIONS.md`
- `NEXT_TASK.md`
- Other repository documentation only if strictly necessary to keep the workflow, authorization boundary, and hard-gate language consistent.

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

- Define the autonomous selection rule narrowly: Control Tower may choose future non-dangerous RX tasks from the source-of-truth repository docs without asking the user to name each next task.
- Define or document the hard-stop categories that still require explicit user approval: live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions.
- Preserve one RX task equals one clean executor task and one task branch.
- Preserve `NEXT_TASK.md` as exactly one next task and require the handoff validator to pass.
- Preserve source-of-truth repository docs as the basis for task selection, scope, branch discipline, validation, and final reports.
- Preserve reviewer acceptance as the only way to mark a task accepted.
- Preserve parent ownership of branch discipline, final diff review, validation, commit, push, and final report.
- Preserve worker/subagent checkpoint requirements for non-trivial architecture-sensitive work.
- Do not add product code, runtime code, tests for product behavior, or new abstractions.
- Worker policy: one supervised worker required for design support because this is non-trivial repository-governance work.
- The worker must stop at DESIGN CHECKPOINT before implementation edits and answer whether the proposed workflow wording preserves hard approval gates, one-task/one-branch discipline, source-of-truth docs, reviewer acceptance, and the exactly-one-task `NEXT_TASK.md` contract.
- The worker must wait for Parent approval or steering after DESIGN CHECKPOINT before any implementation edits continue.
- The worker must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT if it continues beyond design support.
- Parent owns steering, final diff review, validation, commit, push, and final report.
- The worker must not commit, push, merge, approve work, or start unrelated scope.
- Parent must stop before edits if the required worker is unavailable.

## Required files

- Likely `AGENTS.md`
- Likely `docs/WORKFLOW.md`
- Likely `docs/templates/RX_TASK_TEMPLATE.md`
- Likely `docs/templates/REVIEW_CHECKLIST.md`
- Likely `STATUS.md`
- Likely `IMPLEMENTATION_PLAN.md`
- Likely `DECISIONS.md`
- Likely `NEXT_TASK.md`
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
