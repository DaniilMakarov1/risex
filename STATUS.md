# Status

- Last accepted task: RX-005 — Offline Scan Orchestration over Per-Venue Observations
- Accepted RX-005 implementation HEAD: `42858c5a4468145fff590e4277acb6868745323f`
- Accepted baseline branch: `main`
- Current RX task: RX-006 — Broad Scan and Focused Refresh Orchestration, implemented on review branch
- RX-006 starting baseline: `1aeae05a9f07965e5c02a816bc737628cba97715`
- RX-006 task branch: `task/rx-006-broad-focused-refresh`

The accepted RX-005 implementation remains the latest accepted baseline on `main`.
RX-006 is implemented on a task branch for review and has not been merged to `main`.

## Completed accepted tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004
- RX-005

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative `assemble_route_snapshot()` path.
- One deterministic offline route-candidate orchestration path.
- Deterministic fake Broad Scan orchestration using `EvaluationMode.DISCOVERY`.
- Deterministic fake Focused Refresh orchestration using `EvaluationMode.ENTRY`.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No live or paper execution from scan orchestration.

## Tests last reported for RX-006 branch

- `python3 -m apps.cli.main`:
  - `Broad Scan`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
  - `Focused Refresh`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
- `python3 -m pytest`: `131 passed in 0.13s`

## Known limitations

- Fake data only.
- Broad Scan and Focused Refresh are deterministic offline orchestration only.
- No persistent Watchlist storage.
- No real venue adapters.
- No persistent ledger or reconciliation.
- No paper runner.
- No funding settlement verifier.
- No live trading.

## Next recommended task

RX-007 — Paper Runner Lifecycle and Append-only Ledger Persistence.
