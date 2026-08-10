# RX Task

## Summary

- Task ID:
- Branch:
- Starting HEAD:
- Final HEAD:

## Scope

- [ ] Changes are limited to the task's allowed scope.
- [ ] No product behavior, trading, adapter, network, secret, route-status, reject-reason, or architecture changes are included unless explicitly required.
- [ ] No speculative helpers, future hooks, broad refactors, or unnecessary abstractions were added.

## Governance

- [ ] `STATUS.md` separates accepted baseline from current task completion/review state.
- [ ] `DECISIONS.md` records only decisions made by this task, if any.
- [ ] `NEXT_TASK.md` contains exactly one next task.
- [ ] `python scripts/validate_next_task.py` passes.

## Worker Orchestration

- [ ] Worker used: yes/no.
- [ ] Checkpoints reviewed by Parent when workers were used.
- [ ] Parent reviewed final diff.
- [ ] Parent committed and pushed.

## Validation

- [ ] `python scripts/validate_next_task.py`
- [ ] `python3 -m pytest tests/invariant`
- [ ] `python3 -m pytest`
- [ ] `python3 -m compileall apps core storage tests scripts`
- [ ] `python3 -m apps.cli.main`
- [ ] `git diff --check`
- [ ] `git diff --cached --check`
- [ ] `git status --short`

## Reviewer Outcome

- [ ] Accepted
- [ ] Rejected
- [ ] Fix requested in same branch
