# Status

- Last accepted task: RX-004 — Per-Venue Observation and Route Snapshot Contracts
- Accepted RX-004 implementation HEAD: `371ef080435746adedf03ed7157bb2aabd835456`
- Accepted baseline branch: `main`
- Current RX task: none active

The accepted RX-004 implementation HEAD is `371ef080435746adedf03ed7157bb2aabd835456`.
The previous governance commit on `main` (`8817adb6f54d979a51161762449e958692316814`) was the starting baseline for RX-004.

## Completed tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative offline `assemble_route_snapshot()` path.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.

## Tests last reported for accepted RX-004

- `python3 -m apps.cli.main`: `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
- `python3 -m pytest`: `115 passed in 0.11s`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0

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

RX-005 — Offline Scan Orchestration over Per-Venue Observations
