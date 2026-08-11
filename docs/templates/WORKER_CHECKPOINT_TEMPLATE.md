# Worker Checkpoint Template

Workers must stop and wait for Parent review at each checkpoint. Parent must approve the direction or steer before the worker continues to the next phase. Workers must not commit, push, merge, approve, or broaden scope.

## DESIGN CHECKPOINT

Stop here before any implementation edits.

- Files to change:
- Contracts/functions to change:
- Tests expected:
- Forbidden scope avoided:
- Questions or blockers:
- Waiting for Parent approval or steering: yes

## CODE CHECKPOINT

Stop here after implementation and before tests or validation continue.

- Files changed:
- New/changed contracts:
- Why each change was necessary:
- Forbidden scope avoided:
- Partial diff summary:
- Questions or blockers:
- Waiting for Parent approval or steering: yes

## TEST CHECKPOINT

Stop here after tests are added or changed and before validation continues.

- Test files changed:
- Positive cases:
- Negative/fail-closed cases:
- Gaps:
- Commands run:
- Waiting for Parent approval or steering: yes

## VALIDATION CHECKPOINT

Stop here after validation commands and before Parent final diff review.

- Commands run:
- Exact results:
- Git status:
- Limitations:
- Ready for Parent final diff review: yes/no
