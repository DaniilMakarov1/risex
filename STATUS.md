# Status

- Last accepted task: RX-004 — Per-Venue Observation and Route Snapshot Contracts
- Accepted RX-004 implementation HEAD: `371ef080435746adedf03ed7157bb2aabd835456`
- Accepted baseline branch: `main`
- Current RX task: RX-005 — Offline Scan Orchestration over Per-Venue Observations candidate ready for review
- RX-005 starting baseline: `607e38f7c83b8d5ca8ad24bea0bbf418e4cfea7c`
- RX-005 task branch: `task/rx-005-offline-scan-orchestration`

The accepted RX-004 implementation HEAD is `371ef080435746adedf03ed7157bb2aabd835456`.
The previous governance commit on `main` (`8817adb6f54d979a51161762449e958692316814`) was the starting baseline for RX-004.

## Completed tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004
- RX-005 candidate

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative offline `assemble_route_snapshot()` path.
- One deterministic offline route-candidate orchestration path.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No live or paper execution from offline orchestration.

## Tests last reported for RX-005 candidate

- `python3 -m apps.cli.main`:
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
- `python3 -m pytest`: `122 passed`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Fake data only.
- No Broad Scan.
- No Focused Refresh.
- No Watchlist.
- No real venue adapters.
- No persistent ledger or reconciliation.
- No paper runner.
- No funding settlement verifier.
- No live trading.

## Next recommended task

RX-006 — Broad Scan and Focused Refresh orchestration over the same offline observation, snapshot assembly, and `evaluate_route()` path.
