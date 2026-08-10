# RX Report Template

Return the report as one fenced Markdown code block with no prose outside.

```markdown
# RX Task Report

## Task ID

RX-000 - Short task name

## Repository path

`/Users/daniilmakarov/Desktop/risex-main`

## Branch

`task/rx-000-short-name`

## Starting HEAD

`<starting_commit_sha>`

## Final HEAD

`<final_commit_sha>`

## Changed files

- `path/to/file`

## What was implemented

- Describe the completed implementation.

## New functions/classes/contracts added and why each was necessary

- `name`: why it was necessary.
- Or state: No new abstractions added.

## Tests run

- `python scripts/validate_next_task.py`
- `python3 -m pytest tests/invariant`
- `python3 -m pytest`
- `python3 -m compileall apps core storage tests scripts`
- `python3 -m apps.cli.main`
- `git diff --check`
- `git diff --cached --check`
- `git status --short`

## Exact test results

- `<command>`: `<exact result>`

## Working-tree status

`git status --short`: `<exact output or empty>`

## Known limitations

- List limitations, or state none for the task scope.

## Risk impact

- Explain product, trading, architecture, and operational risk impact.

## Orchestration log

- Worker used: yes/no.
- Worker prompt summary: none if no worker was used.
- Checkpoints received: none if no worker was used.
- Steers sent: none if no worker was used.
- Completed / blocked / stopped: completed/blocked/stopped.
- Who committed/pushed: Parent Codex.
- Parent reviewed final diff: yes/no.

## Next suggested task

RX-000 - Short task name
```
