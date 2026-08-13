# RX Review Checklist

## Scope

- Task branch matches the assigned RX task.
- Starting baseline matches the task prompt.
- Changed files are inside allowed scope.
- No product behavior, trading, adapter, network, secret, route-status, reject-reason, or architecture changes are present unless explicitly required.

## Architecture

- Single owner modules are preserved.
- No second route model, EV path, decision path, snapshot assembly path, VWAP path, ledger-write path, or live execution path was introduced.
- Live trading remains disabled by default.
- Unknown values do not silently become zero.
- No canary architecture, hold-next-cycle logic, expected basis forecast, or artificial standalone filters were introduced.

## Abstractions

- Every new function, class, contract, enum, module, or config value is necessary for the current task.
- Every new abstraction is used immediately.
- Every new abstraction is covered by focused tests.
- No future hooks, placeholder interfaces, wrappers around one call, or speculative trace fields were added.

## Workflow

- If Control Tower selected the task autonomously, selection is grounded in source-of-truth repository docs and the task is non-dangerous.
- Explicit user approval is present for any live trading, order placement, sendable exchange request, private endpoint, credential, account balances/state, destructive reset, unsafe scope, or financially dangerous action; otherwise those categories are absent from scope.
- Control Tower did not treat implementation completion, self-review, or fix coordination as reviewer acceptance.
- `STATUS.md` separates the accepted baseline from current task completion/review state.
- `DECISIONS.md` records only decisions actually made by the task.
- `NEXT_TASK.md` contains exactly one next task and passes `python scripts/validate_next_task.py`.
- Worker usage was classified before edits.
- Required worker/subagent support was used for non-trivial architecture-sensitive tasks.
- Worker checkpoints are present when workers were used, including DESIGN CHECKPOINT before implementation edits.
- Parent approval or steering after worker checkpoints is documented in the orchestration log.
- Worker did not commit, push, merge, approve work, or start unrelated scope.
- Parent reviewed worker output during the task when a worker was used.
- Parent reviewed the final diff before commit and push.

## Validation

- `python scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- `git status --short`

## Outcome

- Accepted.
- Rejected.
- Fix requested in same branch.
