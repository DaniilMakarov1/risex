## Task ID

RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage

## Objective

Add deterministic offline fresh CapturePlan gate contracts and fake replay coverage that can later block any live Capture path unless a CapturePlan is explicitly fresh for exactly one Capture and one funding settlement opportunity.

## Allowed scope

- Define deterministic offline CapturePlan freshness gate contracts.
- Use fake deterministic inputs only.
- Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and ledger boundaries.
- Add tests proving missing, stale, duplicated, cross-capture, cross-route, or cross-settlement plan evidence fails closed.
- Keep live trading disabled.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place orders or enable live trading.
- Do not implement live runner behavior.
- Do not create executable live order plans.
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
