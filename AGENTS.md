# AGENTS.md

This repository is the source of truth for RiseX Points Farmer implementation work.

## Operating rules

- One Codex session equals one RX task.
- Work only on the task branch requested for that RX task.
- Before changing files, check repository, branch, HEAD, and git status.
- Do not overwrite uncommitted user changes.
- Read this file plus `README.md`, `ARCHITECTURE.md`, `PRODUCT_INVARIANTS.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, and `NEXT_TASK.md` before implementing.
- Update `STATUS.md` and `NEXT_TASK.md` at the end of each task. `NEXT_TASK.md` must contain exactly one next task and pass `python scripts/validate_next_task.py`.
- Update `DECISIONS.md` when the task makes or changes an architectural or repository-governance decision.
- Use `docs/WORKFLOW.md` and the templates in `docs/templates/` when preparing task prompts, worker checkpoints, reports, and review checklists.
- Treat accepted offline safety-hardening work as guardrail evidence, not as a product strategy change or permission to keep adding speculative scaffolding. Future tasks must follow the single task in `NEXT_TASK.md`, return to the intended product roadmap after the current handoff, and avoid "while here" abstractions.

## Control Tower autonomous task selection

- After RX-033 is reviewer-accepted, Control Tower may autonomously select, create, run, coordinate review/fixes for, and finalize future non-dangerous RX tasks from the source-of-truth repository docs without asking the user to name each next task.
- Autonomous selection must use the repository docs, especially `NEXT_TASK.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, this file, and `docs/WORKFLOW.md`; do not rely on chat memory or broad roadmap implication.
- Autonomy is limited to one RX task at a time, one clean Codex executor task, and one task branch. It does not authorize batched work, continuous unattended task chains, or starting the next RX task before the current task is finalized under this workflow.
- Control Tower may coordinate review and fixes, but reviewer acceptance remains explicit and separate. Implementation-complete work on a task branch is not accepted until a reviewer accepts it.
- Parent Codex still owns task scope, branch discipline, worker steering, final diff review, validation, commit, push, and final report for each executor task.
- Hard stop: Control Tower must obtain explicit user approval before selecting, creating, running, fixing, or finalizing any task involving live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions. Ordinary non-dangerous RX work may continue autonomously when grounded in repository docs; ask the user only when the candidate reaches a hard-stop category, unsafe scope, financially dangerous action, destructive reset, or genuine product/architecture fork that cannot be resolved from the docs.

## Parent, worker, and reviewer boundaries

- Parent Codex owns task scope, branch discipline, architecture checks, final diff review, validation, commit, push, and final report.
- Parent Codex must classify worker usage before edits. A supervised worker/subagent is required for non-trivial architecture-sensitive tasks, including live-gate, accounting, reconciliation, execution-boundary, ledger, safety-critical, broad contract, owner-boundary, or repository-governance tasks.
- Worker use is optional for docs-only, metadata-only, tiny fix, or mechanical validation tasks when they are not non-trivial architecture-sensitive work.
- If a worker is required but unavailable, Parent Codex must stop before edits and report the blocker.
- Workers may be used only under Parent supervision. They must not commit, push, merge, approve work, or start unrelated scope.
- Workers must stop at DESIGN CHECKPOINT before any implementation edits. Parent Codex must read the checkpoint and either approve the direction or steer before implementation continues.
- Workers must also stop at CODE CHECKPOINT, TEST CHECKPOINT, and VALIDATION CHECKPOINT before continuing to the next phase. Parent Codex must review worker output during the task, not only in the final report.
- If a worker skips required checkpoints, continues after being stopped, or drifts into forbidden scope, Parent Codex must stop or steer before accepting any worker output.
- Reviewers accept or reject task branches. A task is not accepted until reviewer acceptance is explicit.
- `STATUS.md` must keep the last accepted baseline separate from the current task branch and current task review state.

## No unnecessary abstractions

- Do not add new functions, classes, dataclasses, enums, statuses, modules, wrappers, config values, trace fields, future hooks, or contracts unless the current RX task explicitly requires them or they are strictly necessary to complete it.
- Any new abstraction must belong to the authoritative owner module, be used immediately, and be covered by focused tests.
- Never create a second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, or live execution path.
- Roadmap stages are gated handoffs, not standing permission to implement later live trading, adapters, execution planning, dashboards, monitoring, or additional offline scaffolding ahead of the exact current task.
- Final reports must state every new function, class, or contract added and why each was necessary. If none were added, state `No new abstractions added.`

## Hard prohibitions

- Do not add real API keys, secrets, or production credentials.
- Do not enable live trading by default.
- Do not place live orders unless a future task explicitly enables a safe live path.
- Do not create `CANARY_ELIGIBLE` or a separate `canary_runner` architecture.
- Do not use `expected_basis_change` as a future basis prediction.
- Do not add arbitrary max spread, max price impact, max levels consumed, hidden conservative buffers, or hidden safety margins.

## Architecture boundaries

- Modular monolith only, not microservices.
- Capture-centric and contract-centric architecture.
- One `Capture` represents one funding settlement opportunity.
- One shared route decision pipeline: `core/pipeline/evaluate.py`.
- Fees logic belongs only in `core/economics/fees.py`.
- Funding logic belongs only in `core/economics/funding.py`.
- Liquidity/VWAP logic belongs only in `core/economics/liquidity.py`.
- Basis/unwind tracking belongs only in `core/economics/basis.py`.
- EV logic belongs only in `core/economics/ev.py`.
- Risk gates belong only in `core/risk/gates.py`.
- Order sending belongs only in `core/execution/`.
- Ledger writes belong only in `core/accounting/ledger.py`.
- Venue adapters may fetch and normalize data only.

## Required report format

Return final RX task reports in one fenced Markdown code block for one-click copy.
The report must have no extra prose outside the code block.

End every RX task with:

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
- Orchestration log, if workers were used
- Next suggested task
