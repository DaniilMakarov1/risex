## Task ID

RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage

## Objective

Add deterministic offline ledger reconciliation contracts and fake replay coverage that can later block any live Capture path unless append-only ledger history is internally consistent and explicitly reconciled.

## Allowed scope

- Define deterministic offline ledger reconciliation contracts.
- Use fake deterministic ledger events only.
- Keep reconciliation downstream of existing route decisions, Capture lifecycle, paper history, funding settlement verification, and ledger boundaries.
- Add replay tests proving reconciled and unreconciled ledger histories are deterministic.
- Add tests proving missing, duplicated, out-of-order, or contradictory ledger evidence fails closed.
- Keep live trading disabled and do not create live `CapturePlan` objects.

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
