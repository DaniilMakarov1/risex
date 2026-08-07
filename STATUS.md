# Status

- Last accepted task: RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage
- Accepted RX-008 implementation HEAD: `c4c38424d420312a64730f44ffebb5de38b2af62`
- Accepted baseline branch: `main`
- Current RX task: RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage
- Current RX task branch: `task/rx-009-ledger-reconciliation-gate`
- Current RX task status: candidate fix pending review

The accepted RX-008 implementation is the latest accepted baseline on `main`.

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
- RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage

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
- Deterministic offline funding settlement verifier lives in `core/monitoring/funding_settlement.py`.
- Funding settlement verifier models required checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds.
- Funding checkpoint evidence, observed settlement evidence, and verification result history are written through append-only ledger helpers.
- Actual settlement funding and actual settlement notional evidence must use `ValueSource.OBSERVED`; user-configured, documented, estimated, unknown, missing, malformed, or non-positive notional actuals cannot verify settlement.
- Pre-settlement expected funding checkpoints remain source-aware expected inputs and are not restricted to `ValueSource.OBSERVED`.
- Funding settlement verifier replay compares fake expected funding/notional inputs against fake observed settlement records and fails closed on missing, unknown, unobserved, or inconsistent evidence.
- Deterministic offline ledger reconciliation lives in `core/accounting/reconciliation.py`.
- Ledger reconciliation replays append-only route decision, fake paper lifecycle, funding evidence, and funding settlement verification events for one Capture.
- Ledger reconciliation recomputes recorded funding settlement verification results through `core/monitoring/funding_settlement.py` and fails closed when raw checkpoint or settlement evidence contradicts the recorded verification event.
- Ledger reconciliation records results through `core/accounting/ledger.py` as `ledger_reconciliation_recorded`.
- Ledger reconciliation results record checked `event_count` and `last_sequence`.
- Ledger reconciliation validates supplied sequence order exactly; duplicate, missing, non-contiguous, or out-of-order sequences fail closed.
- Unknown event types, malformed known event payloads, stale reconciliation, or contradictory ledger evidence fail closed as unreconciled with explicit reconciliation reasons.
- Future live gating now requires `ledger_explicitly_reconciled=True` derived from `is_ledger_explicitly_reconciled(ledger.records())`; otherwise `RejectReason.LEDGER_NOT_RECONCILED` blocks the path before later live gates.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No real adapters, orders, paper exchange simulation, live runner behavior, or live trading.

## Tests last reported for RX-009 FIX 2 candidate

- `python3 -m apps.cli.main`:
  - `Broad Scan`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
  - `Focused Refresh`
  - `fake-risex-hl-btc: PAPER_ELIGIBLE net_profit_usd=1.50000000000000000000000000`
  - `fake-risex-hl-eth: REJECTED net_profit_usd=-0.2499625093726568357910522369`
- `python3 -m pytest`: `184 passed in 0.18s`
- `python3 -m compileall apps core storage tests`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Verifier remains deterministic fake offline replay scaffolding.
- No real RiseX/Hyperliquid adapters.
- No network calls.
- No orders.
- No live runner behavior.
- No live trading.
- No `CapturePlan` creation.
- Ledger reconciliation remains deterministic fake offline replay scaffolding.
- Ledger reconciliation is not permission to trade live by itself.

## Next recommended task

RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage, only after RX-009 is accepted.
