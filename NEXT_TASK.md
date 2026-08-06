## Task ID

RX-005 — Offline Scan Orchestration over Per-Venue Observations

## Objective

Add deterministic offline orchestration that evaluates multiple fake route candidates through the RX-004 `VenueObservation` and `assemble_route_snapshot()` contracts, while preserving the single `evaluate_route(route, snapshot, mode)` decision path.

## Allowed scope

- Add offline fake route candidate orchestration over normalized `VenueObservation` inputs.
- Reuse `assemble_route_snapshot()` for every candidate.
- Reuse `evaluate_route()` for every route decision.
- Keep all behavior deterministic, offline, read-only, and non-trading.
- Add focused unit and invariant tests for route iteration, missing observations, and single-path evaluation.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network, API, authentication, or production adapters.
- Do not implement order placement, paper execution lifecycle, persistent ledger storage, migrations, dashboard code, or live trading.
- Do not create `CapturePlan` objects.
- Do not add a second route model, second EV path, second route decision function, canary architecture, hold-next-cycle logic, artificial filters, secrets, or production credentials.

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
