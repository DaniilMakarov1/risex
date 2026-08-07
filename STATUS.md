# Status

- Last accepted task: RX-006 — Broad Scan and Focused Refresh Orchestration
- Accepted RX-006 implementation HEAD: `b71a93c66370183454863ec3841d564cf53c083a`
- Accepted baseline branch: `main`
- Current RX task: none active

The accepted RX-006 implementation is the latest accepted baseline on `main`.

## Completed accepted tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004
- RX-005
- RX-006

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

## Tests last reported for accepted RX-006

- `python3 -m apps.cli.main`:
  - `Broad Scan`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
  - `Focused Refresh`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
- `python3 -m pytest`: `131 passed in 0.13s`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

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
