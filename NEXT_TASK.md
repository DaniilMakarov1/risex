## Task ID

RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

## Objective

Add a deterministic fake offline contract that bundles the already-implemented future live-gate inputs for one Capture route evaluation so callers cannot accidentally mix ledger reconciliation, CapturePlan freshness, and execution-capability evidence from different captures, routes, or funding settlement opportunities.

## Allowed scope

- Use fake deterministic inputs only.
- Keep the bundle downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution-capability evidence.
- Reuse existing `RouteCandidate`, `VenueSnapshot`, `CapturePlanFreshnessEvidence`, `ExecutionCapabilityEvidence`, and `evaluate_route()` contracts.
- Prove cross-capture, cross-route, cross-settlement, missing-component, and stale-component bundles fail closed before any future live path can proceed.
- Keep live trading disabled.

## Forbidden scope

- Do not implement real RiseX, Hyperliquid, network calls, API clients, authentication, or production adapters.
- Do not place orders or enable live trading.
- Do not implement live runner behavior.
- Do not create executable live order plans.
- Do not add canary architecture, `CANARY_ELIGIBLE`, or `canary_runner`.
- Do not add hold-next-cycle logic.
- Do not add artificial filters or hidden buffers.
- Do not add a second route model, EV path, route decision function, snapshot assembly function, or VWAP/liquidity path.

## Required files

- AGENTS.md
- README.md
- ARCHITECTURE.md
- PRODUCT_INVARIANTS.md
- IMPLEMENTATION_PLAN.md
- STATUS.md
- DECISIONS.md
- NEXT_TASK.md
- core/domain/contracts.py
- core/risk/gates.py
- core/pipeline/evaluate.py
- tests/unit/test_risk_gates.py
- tests/replay/test_capture_plan_freshness.py
- tests/replay/test_execution_capability.py

## Required tests

- Missing live-gate evidence bundle fails closed.
- Cross-capture bundle components fail closed.
- Cross-route bundle components fail closed.
- Cross-settlement bundle components fail closed.
- Stale CapturePlan freshness evidence inside the bundle fails closed.
- Stale execution-capability evidence inside the bundle fails closed.
- Fresh bundle does not bypass live disabled.
- Fresh bundle does not bypass unreconciled ledger.
- Fresh bundle still stops at `LIVE_GATES_NOT_IMPLEMENTED` and does not create a live `CapturePlan`.
- Existing RX-009, RX-010, and RX-011 tests still pass.

## Required report format

Return one fenced Markdown code block with no prose outside.

Include:

- Task ID
- Repository path
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- New functions/classes/contracts added and why each was necessary
- Tests run
- Exact test results
- Working-tree status
- Known limitations
- Risk impact
- Next suggested task
