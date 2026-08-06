# Status

- Last accepted task: RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
- Accepted RX-003 implementation HEAD: `05ecdc4bf146f1c436a7c888f82117772419d743`
- Accepted baseline branch: `main`
- Current RX task: RX-004 — Per-Venue Observation and Route Snapshot Contracts implemented on `task/rx-004-per-venue-observation`, pending review

The accepted implementation HEAD is `05ecdc4bf146f1c436a7c888f82117772419d743`.
The later governance commit on `main` (`8817adb6f54d979a51161762449e958692316814`) is the starting baseline for RX-004.

## Completed tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004 implemented pending review

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

## Tests last reported for RX-004

- `python3 -m apps.cli.main`: `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
- `python3 -m pytest`: `111 passed`
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
