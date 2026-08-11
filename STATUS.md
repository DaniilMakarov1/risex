# Status

- Last accepted task: RX-Q001 — Repository Workflow and Quality Guardrails
- Accepted RX-Q001 implementation HEAD: `74ded8e38e324fcf550c1e6946376067dbe08e55`
- Previous accepted product task: RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage
- Accepted RX-011 implementation HEAD: `317d3913ad02082f3d17a228b40da8abee729343`
- Accepted baseline branch: `main`
- Current RX task: RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage
- Current RX task branch: `task/rx-012-offline-live-gate-evidence-bundle`
- Current RX task status: implemented on task branch; pending reviewer acceptance and merge

The accepted RX-Q001 implementation is the latest accepted baseline on `main`.
RX-011 remains the previous accepted product implementation baseline.
RX-012 is not accepted until reviewer acceptance is explicit.

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
- RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage
- RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage
- RX-Q001 — Repository Workflow and Quality Guardrails

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
- Deterministic fake execution capability evidence lives in `core/domain/contracts.py` as `ExecutionCapabilityEvidence`.
- CapturePlan freshness gating lives in `core/risk/gates.py`.
- Missing, stale, duplicated, future-dated, cross-capture, cross-route, cross-settlement, malformed, or unknown-source fake plan evidence fails closed with `RejectReason.CAPTURE_PLAN_NOT_FRESH`.
- Execution capability gating lives in `core/risk/gates.py`.
- Missing, stale, future-dated, cross-capture, cross-route, cross-settlement, malformed, non-orderbook-source, missing-side, wrong-side, wrong-target-notional, partial-fill, or contradictory fake execution capability evidence fails closed through existing centralized reject reasons.
- Deterministic fake live gate evidence bundle lives in `core/domain/contracts.py` as `LiveGateEvidenceBundle`.
- Live gate evidence bundle checking lives in `core/risk/gates.py`.
- Missing, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale/missing CapturePlan evidence, or stale/missing/non-executable execution evidence in a fake bundle fails closed through existing centralized reject reasons.
- Future live gating now checks live trading switch, explicit ledger reconciliation, verified funding settlement, CapturePlan freshness evidence, execution capability evidence, and then the still-unimplemented live gates when a fake bundle is supplied.
- `evaluate_route()` may receive fake freshness evidence, execution-capability evidence, or a fake live gate evidence bundle but still does not read ledger/storage directly, create live `CapturePlan` objects, import execution/live runner modules, place orders, or return `LIVE_ELIGIBLE`.
- In-memory Broad Scan to Focused Refresh handoff using existing `RouteCandidate` contracts.
- Per-venue `VenueObservation` input contract.
- Source-aware fees and funding.
- Route/snapshot alignment.
- Full-target order-book VWAP executability.
- Unknown economics fail closed.
- Live `CapturePlan` creation blocked.
- No real adapters, orders, paper exchange simulation, live runner behavior, or live trading.

## Tests last reported for accepted RX-011

- `python3 -m apps.cli.main`: exit 0
- `python3 -m pytest`: `222 passed in 0.37s`
- `python3 -m compileall apps core storage tests`: exit 0
- `python3 -c "import core.monitoring.funding_settlement; import core.accounting.reconciliation"`: exit 0
- `python3 -c "from core.monitoring.funding_settlement import replay_funding_settlement_verification; from core.accounting.reconciliation import replay_ledger_reconciliation"`: exit 0
- targeted pytest: `37 passed in 0.08s`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for accepted RX-Q001

- `python scripts/validate_next_task.py`: `NEXT_TASK.md: OK` under login `bash`; default `zsh` has no `python` command
- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `32 passed`
- `python3 -m pytest`: `234 passed`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Tests last reported for RX-012 branch

- `python3 scripts/validate_next_task.py`: `NEXT_TASK.md: OK`
- `python3 -m pytest tests/invariant`: `33 passed in 0.14s`
- `python3 -m pytest`: `255 passed in 0.38s`
- `python3 -m compileall apps core storage tests scripts`: exit 0
- `python3 -m apps.cli.main`: exit 0; Broad Scan BTC `PAPER_ELIGIBLE`, ETH `REJECTED`; Focused Refresh BTC `PAPER_ELIGIBLE`, ETH `REJECTED`
- `git diff --check`: exit 0
- `git diff --cached --check`: exit 0

## Known limitations

- Funding settlement verifier, ledger reconciliation, and CapturePlan freshness remain deterministic fake offline replay scaffolding only.
- Execution capability remains deterministic fake offline gate scaffolding only.
- Live gate evidence bundle remains deterministic fake offline gate scaffolding only.
- CapturePlan freshness evidence is not executable live order planning.
- Execution capability evidence is not executable live order planning.
- Live gate evidence bundle is not executable live order planning.
- No real RiseX/Hyperliquid adapters.
- No network calls.
- No orders.
- No live runner behavior.
- No live trading.
- No live `CapturePlan` creation.
- Fresh CapturePlan evidence is not permission to trade live by itself.
- Fresh execution capability evidence is not permission to trade live by itself.
- Exact fake live gate evidence bundle is not permission to trade live by itself.

## Next recommended task

RX-013 — Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage, starting from the accepted RX-012 baseline after reviewer acceptance.
