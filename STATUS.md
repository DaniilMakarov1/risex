# Status

- Last accepted task: RX-007 — Paper Runner Lifecycle and Append-only Ledger Persistence
- Accepted RX-007 implementation HEAD: `27b4251cf2f0c7c5b831d325b16a621d322ecc70`
- Accepted baseline branch: `main`
- Current RX task: none active

The accepted RX-007 implementation is the latest accepted baseline on `main`.

## Completed accepted tasks

- RX-000
- RX-001
- RX-002
- RX-002A
- RX-003
- RX-004
- RX-005
- RX-006
- RX-007

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative `assemble_route_snapshot()` path.
- One deterministic offline route-candidate orchestration path.
- Deterministic fake Broad Scan orchestration using `EvaluationMode.DISCOVERY`.
- Deterministic fake Focused Refresh orchestration using `EvaluationMode.ENTRY`.
- Deterministic fake paper lifecycle downstream of existing `DecisionResult` values.
- Paper lifecycle starts only from `PAPER_ELIGIBLE` input decisions in `EvaluationMode.ENTRY`.
- Broad Scan `PAPER_ELIGIBLE` decisions remain non-starting discovery signals.
- Paper lifecycle uses the single Capture state machine.
- One fake paper `Capture` represents one funding settlement opportunity.
- Append-only ledger event contracts and helpers live in `core/accounting/ledger.py`.
- Minimal SQLite append-only persistence scaffolding lives in `storage/sqlite/ledger.py`.
- Deterministic paper replay reconstructs final `Capture` states from ledger events.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No real adapters, orders, paper exchange simulation, live runner behavior, or live trading.

## Tests last reported for accepted RX-007

- `python3 -m apps.cli.main`:
  - `Broad Scan`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
  - `Focused Refresh`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
- `python3 -m pytest`: `144 passed in 0.13s`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Fake data only.
- Paper lifecycle is deterministic offline scaffolding, not an exchange simulator.
- No persistent Watchlist storage.
- No real venue adapters.
- No ledger reconciliation.
- No funding settlement verifier.
- No dashboard behavior.
- No order placement.
- No live trading.

## Next recommended task

RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage.
