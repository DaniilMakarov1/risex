# Status

- Last accepted task: RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage
- Accepted RX-009 baseline HEAD: `f20b100de8ccc86306bede58702b53d535188ab4`
- Accepted baseline branch: `main`
- Current RX task: RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage
- Current RX task branch: `task/rx-010-fresh-captureplan-gate`
- Current RX task status: candidate pending review

The accepted RX-009 implementation remains the latest accepted baseline on `main` until RX-010 is reviewed and accepted.

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
- RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage

## Current architecture status

- Offline modular monolith.
- Capture-centric domain.
- One shared `evaluate_route()` decision path.
- One authoritative `assemble_route_snapshot()` path.
- One deterministic offline route-candidate orchestration path.
- Deterministic fake Broad Scan orchestration using `EvaluationMode.DISCOVERY`.
- Deterministic fake Focused Refresh orchestration using `EvaluationMode.ENTRY`.
- Deterministic fake paper lifecycle downstream of existing `DecisionResult` values.
- One fake paper `Capture` represents one funding settlement opportunity.
- Append-only ledger event contracts and helpers live in `core/accounting/ledger.py`.
- Deterministic offline funding settlement verifier lives in `core/monitoring/funding_settlement.py`.
- Deterministic offline ledger reconciliation lives in `core/accounting/reconciliation.py`.
- Ledger reconciliation records checked `event_count` and `last_sequence`, and `is_ledger_explicitly_reconciled(ledger.records())` returns true only for the exact current append-only history.
- Deterministic fake CapturePlan freshness evidence lives in `core/domain/contracts.py` as `CapturePlanFreshnessEvidence`.
- CapturePlan freshness gating lives in `core/risk/gates.py`.
- Missing, stale, duplicated, future-dated, cross-capture, cross-route, cross-settlement, malformed, or unknown-source fake plan evidence fails closed with `RejectReason.CAPTURE_PLAN_NOT_FRESH`.
- Future live gating now checks live trading switch, explicit ledger reconciliation, CapturePlan freshness evidence, and then the still-unimplemented live gates.
- `evaluate_route()` may receive fake freshness evidence but still does not read ledger/storage directly, create live `CapturePlan` objects, import execution/live runner modules, place orders, or return `LIVE_ELIGIBLE`.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No real adapters, orders, paper exchange simulation, live runner behavior, or live trading.

## Tests run for RX-010 candidate

- `python3 -m apps.cli.main`: exit 0
- `python3 -m pytest`: `198 passed in 0.28s`
- `python3 -m compileall apps core storage tests`: exit 0
- `python3 -c "import core.monitoring.funding_settlement; import core.accounting.reconciliation"`: exit 0
- `python3 -c "from core.monitoring.funding_settlement import replay_funding_settlement_verification; from core.accounting.reconciliation import replay_ledger_reconciliation"`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Funding settlement verifier, ledger reconciliation, and CapturePlan freshness remain deterministic fake offline replay scaffolding only.
- CapturePlan freshness evidence is not executable live order planning.
- No real RiseX/Hyperliquid adapters.
- No network calls.
- No orders.
- No live runner behavior.
- No live trading.
- No live `CapturePlan` creation.
- Fresh CapturePlan evidence is not permission to trade live by itself.

## Next recommended task

RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage.
