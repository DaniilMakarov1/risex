## Task ID

RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage

## Objective

Add deterministic offline funding settlement verifier contracts and fake replay coverage that can later prove settlement-time capture inputs before any live trading path exists.

## Allowed scope

- Define verifier contracts for required pre-settlement snapshots such as T-20m, T-60s, T-10s, and T-5s.
- Use fake deterministic observations and append-only ledger events only.
- Keep verifier behavior downstream of existing route decisions, snapshots, Capture lifecycle, and ledger boundaries.
- Add replay tests that compare expected funding inputs with observed fake settlement records.
- Keep live trading disabled and require ledger history for any future live eligibility.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place orders or enable live trading.
- Do not implement live runner behavior.
- Do not create live `CapturePlan` objects.
- Do not add canary architecture, `CANARY_ELIGIBLE`, or `canary_runner`.
- Do not add hold-next-cycle logic.
- Do not add artificial filters or hidden buffers.
- Do not add a second route model, EV path, route decision function, or snapshot assembly function.

## Required report format

- Task ID
- Repository path
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- Tests run
- Exact test results
- Working-tree status
- Known limitations
- Risk impact
- Next suggested task
