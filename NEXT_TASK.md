## Task ID

RX-006 — Broad Scan and Focused Refresh Orchestration

## Objective

Add explicit Broad Scan and Focused Refresh orchestration over the existing offline `VenueObservation`, `assemble_route_snapshot()`, and `evaluate_route(route, snapshot, mode)` path without introducing a second route decision function.

## Allowed scope

- Define deterministic fake Broad Scan and Focused Refresh orchestration inputs.
- Reuse the RX-005 offline candidate orchestration path.
- Reuse `assemble_route_snapshot()` for every route snapshot.
- Reuse `evaluate_route()` for every route decision.
- Keep behavior offline, fake-data-only, read-only, and non-trading.
- Add focused tests for scan mode boundaries, focused refresh boundaries, and single-path reuse.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network, API, authentication, or production adapters.
- Do not implement order placement, paper execution lifecycle, persistent ledger storage, migrations, dashboard code, or live trading.
- Do not create live `CapturePlan` objects.
- Do not add a second route model, second EV path, second route decision function, canary architecture, hold-next-cycle logic, artificial filters, secrets, or production credentials.
- Do not let Focused Refresh create a live `CapturePlan` until future tasks implement fresh plan checks, reconciled ledger state, live gates, funding settlement verification, and execution capability.

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
