# RiseX Points Farmer

RiseX Points Farmer is a modular-monolith research system for capture-centric hedged funding opportunities on RiseX with hedge venue support, initially Hyperliquid.

The current branch remains a non-trading research, fake paper-lifecycle, funding-verification, ledger-reconciliation, non-sending execution-planning, guarded no-order live-runner, explicit approval-gated order-boundary, and read-only dashboard skeleton. Offline runners still use fake data and do not place orders. RX-022 adds one read-only RiseX public market-data adapter, RX-023 adds one read-only Hyperliquid public market-data adapter, RX-024 adds one narrow real market-data route snapshot assembly handoff, RX-025 adds one-route real-data research runner behavior, RX-026 adds one approval-gated funding settlement verification path for explicit caller-supplied observed evidence, RX-027 adds one non-sending execution planning workflow for already-verified prerequisite evidence, RX-028 adds one guarded live runner workflow without orders, RX-029 adds one explicit approval-gated order placement boundary that invokes only an injected deterministic boundary after exact evidence checks, RX-030 adds one read-only monitor view for already-derived fixture evidence, RX-038 adds one manual one-route real-data CLI entry point, RX-039 completes explicit public funding-rate metadata into route-notional funding cash only inside the existing one-route snapshot path, RX-040 preserves explicit public fee-source metadata while keeping fee cash unknown, RX-041 completes explicit public account-independent taker fee-rate metadata into entry plus estimated-exit route-notional fee cash only inside the existing one-route snapshot path, RX-045 adds one opt-in manual public readiness report for the same explicit one-route CLI flow, RX-048 adds one opt-in structured JSON stdout format for that same manual report, and RX-052 records Product Owner clarification that the next product path is a working fake-money paper trader system before any live trading work is considered. These pieces do not use credentials, private account endpoints, real exchange order submission, or real API keys.

## Product baseline

- Main strategy: hedged funding capture on RiseX with hedge venue support.
- One `Capture` equals one funding settlement opportunity.
- Points value, expected airdrop value, leaderboard rewards in base PnL, and unreceived rebates are all explicitly zero.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.
- Live trading is disabled by default.
- Future live gate evidence is fail-closed and currently requires verified funding settlement evidence from canonical replay, explicit ledger reconciliation derived from current append-only ledger history, exactly one fresh fake CapturePlan evidence record, and exactly one fresh fake execution-capability evidence record for the current Capture, route, and funding settlement opportunity.
- Where the fake live gate evidence bundle path is used, the bundle must match the current Capture, route, and funding settlement opportunity and carry the already-derived funding verification, explicit ledger reconciliation, CapturePlan freshness, and execution-capability evidence.
- Missing, stale, duplicated, cross-capture, cross-route, cross-settlement, unverified funding, false reconciliation, or non-executable execution evidence fails closed. Exact gate evidence still does not permit `LIVE_ELIGIBLE`; live trading remains disabled by default and current route decisions stop at `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.
- Non-sending execution plans are evidence only. They describe intended venues, symbols, sides, target notional, settlement timestamp, and prerequisite evidence references, but they contain no credentials, account state, private endpoint payloads, sendable order requests, or order placement permission.
- The guarded live runner consumes existing prerequisite evidence plus one existing non-sending execution plan. It fails closed unless the live switch is explicit and every prerequisite matches the current Capture settlement, then stops at a no-order dry-run ready state without constructing sendable order material.
- The approval-gated order placement boundary consumes one exact no-order ready guarded result, one existing non-sending execution plan, and one caller-supplied `OrderPlacementApproval`. Missing, stale, false, malformed, cross-identity, disabled-live, non-ready, or stale-plan evidence fails closed before the injected deterministic boundary can be called.
- Route statuses are `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, and `REJECTED`.
- `CANARY_ELIGIBLE` and a separate canary runner are forbidden.
- `RouteCandidate` is the authoritative route identity and selected-notional contract. Empty or malformed capture/route identity, venues, symbols, entry sides, or target notional fail at construction; positive notionals below the product minimum still fail through the existing route-evaluation minimum-notional gate.

## Roadmap posture

RX-008 through RX-016 are accepted fail-closed offline safety hardening. They prove funding verification, ledger reconciliation, fake CapturePlan freshness, fake execution capability, fake live-gate bundle checks, and SQLite replay behavior from deterministic evidence. They are not a product strategy change, not executable live architecture, and not permission to keep adding offline scaffolding ahead of the current task.

RX-022 adds a read-only RiseX observation adapter only. RX-023 adds a read-only Hyperliquid observation adapter only. RX-024 adds a one-route real market-data snapshot handoff only. RX-025 adds a one-route real-data research runner only. RX-026 adds approval-gated funding settlement verification only. RX-027 adds non-sending execution planning only. RX-028 adds guarded live runner readiness without orders only. RX-029 adds an explicit approval-gated order placement boundary only. RX-030 adds read-only monitoring display only; it does not add route discovery, polling, adapters, decisions, ledger writes, execution, or orders. RX-038 adds one manual CLI entry point for one explicit RiseX plus Hyperliquid route; it does not add discovery, ranking, polling, private endpoints, credentials, ledger writes, execution automation, or orders. RX-039 completes public funding-rate metadata into USD funding cash only when the existing route notional and entry side make the value grounded. RX-040 preserves explicit public fee-source metadata from existing public adapter payloads only as unknown fee cash metadata. RX-041 completes public account-independent taker fee-rate metadata into entry plus estimated-exit USD fee cash only when the existing route notional and RX-040 public field/container provenance make the value grounded. RX-045 adds one opt-in manual public readiness report that displays existing one-route public evidence and UNKNOWN components without changing decisions, routes, adapters, economics, ledger state, execution, or live gates. RX-048 adds one machine-readable JSON stdout format for the same report only, explicitly tied to `--public-readiness-report`, with no file writes, ledger writes, adapter endpoint changes, execution planning, orders, private/account endpoints, credentials, account state, or live trading. RX-052 is governance/source-of-truth only and records that the next clarified product goal is fake-money paper-trading readiness before any live-trading work. Later roadmap stages must be promoted through `NEXT_TASK.md` one at a time and remain gated.

## Offline research runner

The fake runner builds multiple `RouteCandidate` values and normalized `VenueObservation` inputs. It runs deterministic Broad Scan followed by Focused Refresh. Both stages reuse the RX-005 offline orchestration path: each successful candidate assembles a route snapshot through the single `assemble_route_snapshot()` path and evaluates through the single `evaluate_route()` decision pipeline.

```bash
python -m apps.cli.main
pytest
```

## Real market-data snapshot handoff

RX-024 adds `assemble_route_snapshot_from_adapters()` in `core/pipeline/snapshot.py`. It accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one Hyperliquid `VenueAdapter`, and an explicit timezone-aware assembly timestamp. The handoff fetches exactly the route's RiseX symbol and hedge symbol through `fetch_observation(symbol)`, then delegates construction to the existing `assemble_route_snapshot()` path.

The handoff does not call `evaluate_route()`, calculate profitability, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, place orders, or add live runner behavior. Adapter tests and handoff tests use injected deterministic adapters or fixtures.

## Real-data research runner

RX-025 adds `run_real_data_research_route()` in `apps/research_runner/real_data.py`. It accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, one explicit timezone-aware assembly timestamp, and one `EvaluationMode`. RX-045 adds an app-layer companion helper that returns the same decision plus the already-assembled snapshot for reporting only.

The runner delegates snapshot creation to `assemble_route_snapshot_from_adapters()` and delegates route decisions to `evaluate_route(route, snapshot, mode)`. Adapter or snapshot handoff failures fail closed as `REJECTED` with `RejectReason.REQUIRED_LIVE_DATA_MISSING` before any route evaluation and return no report snapshot. The runner does not discover routes, rank routes, write ledger events, start paper lifecycle, verify settlement, plan execution, place orders, add live behavior, or enable live trading.

## Manual one-route real-data CLI

RX-038 adds `real-data-route` to `apps/cli/main.py`. The command accepts one explicit route/capture identity, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, positive finite target notional, evaluation mode, and timezone-aware assembly timestamp.

The CLI validates malformed inputs before constructing adapters, then instantiates the existing read-only public `RiseXObservationAdapter` and `HyperliquidObservationAdapter` and delegates to `run_real_data_research_route()`. It prints a deterministic one-decision summary with route id, mode, status, reasons, net profit, and existing entry EV fields. Missing economics remain `None`; the CLI does not turn unknown funding or fees into zero. The command does not discover or rank routes, loop, poll, write ledger events, start paper lifecycle, verify settlement, plan execution, place orders, call private endpoints, use credentials, or enable live trading.

RX-045 adds the opt-in `--public-readiness-report` flag to the same `real-data-route` command. The flag preserves all explicit route input requirements and public adapter construction boundaries, then prints the existing decision fields, Entry EV fields, source-aware funding and fee evidence from the retained snapshot, deterministic `UNKNOWN` components, and a display-only public-readiness conclusion for later fail-closed live-readiness review.

The readiness conclusion is operator context only. It does not add or mutate route statuses, reject reasons, route eligibility, Capture state, ledger state, live gates, execution planning, approval-boundary behavior, order requests, or live trading.

RX-048 adds the opt-in `--public-readiness-report-format json` selector for the same manual one-route public readiness report. JSON output is produced only when the operator also supplies `--public-readiness-report`; the existing default `real-data-route` one-decision text output and existing `--public-readiness-report` text output remain unchanged. Supplying the JSON format selector without the report flag fails before adapter construction. The JSON is stdout-only and serializes the same route identity, decision fields, Entry EV fields, source-aware funding and fee evidence, deterministic `UNKNOWN` components, and display-only public-readiness conclusion as the text report.

## Fake-money paper trader handoff

RX-052 records explicit Product Owner direction that the next product path is a working fake-money paper trader system before any live trading is considered. Paper trader means fake paper lifecycle and ledger behavior only. It is not live exchange execution, real order placement, private/account endpoint access, credential use, exchange account state, account balances, sendable exchange request construction, or order payload construction.

The prepared RX-053 handoff is one manual bridge from an existing public one-route real-data ENTRY decision into the existing fake paper lifecycle and append-only ledger. It may write fake paper ledger events only through the existing accounting ownership, may use an explicit local SQLite ledger path if implemented inside the existing SQLite ledger contract, and must preserve stdout-only operator summary behavior, no route discovery or ranking, no polling or background loops, no new decision/snapshot/EV paths, no new route statuses or reject reasons, and no unknown-to-zero behavior.

## Public one-route economics source completion

RX-039 preserves explicit public funding-rate metadata from the existing read-only RiseX and Hyperliquid adapter responses, then completes that metadata into USD funding cash only inside the existing one-route `assemble_route_snapshot()` path where `RouteCandidate.target_notional_usd` and the leg entry side are known. Positive funding rates model longs paying shorts: `buy` legs use `-rate * notional`, and `sell` legs use `rate * notional`.

Missing, malformed, non-finite, non-public, or ungrounded funding-rate inputs remain `ValueSource.UNKNOWN` and cannot become zero. Public or schedule-based account-tier fees remain unknown cash values; RX-039 does not invent fee tiers, default fees, route discovery, polling, private endpoints, credentials, account state, ledger writes, execution planning, orders, or live trading.

## Public one-route fee source metadata preservation

RX-040 preserves explicit public fee-rate or account-tier fee-source metadata from the existing read-only RiseX and Hyperliquid public adapter payloads on the existing unknown `FeeComponent.amount_usd` values.

Fee cash remains `ValueSource.UNKNOWN` with `value=None` because the adapter observation has no selected route notional, account tier, or maker/taker execution certainty, and RX-040 does not add a fee cash completion rule. Missing, malformed, non-finite, non-public, account-tier-dependent, account-state-dependent, or ungrounded fee inputs remain unknown and cannot become zero or default economics. The existing one-route adapter handoff, real-data research runner, `evaluate_route()` path, and manual CLI output format are unchanged.

## Public one-route account-independent fee cash completion

RX-041 completes explicit public account-independent taker fee-rate metadata from the existing read-only RiseX and Hyperliquid adapter responses into USD fee cash only inside the existing one-route `assemble_route_snapshot()` path where `RouteCandidate.target_notional_usd` is known.

Completed fee cash represents the current entry plus immediate estimated-exit taker fills for that venue: `taker_rate * target_notional_usd * 2`. Completion requires RX-040 public provenance for the selected taker field and container, `public_fee_metadata_source=OBSERVED`, `public_fee_metadata_kind=fee_rate_fields`, and `public_fee_account_scope=account_independent`. Missing, malformed, non-finite, non-public, maker-only, ambiguous, missing-provenance, account-tier-dependent, account-state-dependent, or ungrounded fee inputs remain `ValueSource.UNKNOWN` and cannot become zero. The existing one-route adapter handoff, real-data research runner, `evaluate_route()` path, and manual CLI output format are unchanged.

## Offline paper runner

The fake paper runner is downstream of route decisions. It consumes existing `DecisionResult` values, starts fake capture execution only for `PAPER_ELIGIBLE` decisions, and records non-started decisions as paper rejections. It does not recalculate profitability, assemble snapshots, place orders, import the live runner, or create `CapturePlan` objects.

Paper results include deterministic start attribution and PnL explanation copied from the input `DecisionResult`. Started runs are attributed to an ENTRY `PAPER_ELIGIBLE` decision; non-started runs identify the mode/status blocker and preserve any available expected funding, total fees, simulated roundtrip cost, and net profit already produced by `evaluate_route()`. Missing economics remain missing and do not become zero.

Paper history is written through `core/accounting/ledger.py` as append-only events. `storage/sqlite/ledger.py` is a minimal deterministic SQLite implementation of the same ledger contract for offline persistence and replay tests.

## Offline funding settlement verifier

The deterministic funding settlement verifier is downstream of paper lifecycle and ledger evidence. It models required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds, then replays append-only ledger events to compare checkpoint expected funding/notional inputs with observed settlement evidence.

The verifier records evidence and verification results only through `core/accounting/ledger.py`. Missing, unknown, or inconsistent settlement evidence fails closed as not verified. It does not evaluate route profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, or enable live trading.

## Approval-gated funding settlement verification

RX-026 keeps settlement verification in `core/monitoring/funding_settlement.py` and ledger writes in `core/accounting/ledger.py`. `verify_approval_gated_funding_settlement()` accepts one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one explicit approval flag, and caller-supplied observed settlement funding/notional evidence.

The workflow records settlement evidence through the existing `funding_settlement_evidence_recorded` event and then calls the canonical verifier replay. Settlement evidence must carry `approval_granted=True`, `observed_at` equal to the settlement timestamp, and actual funding/notional values with `ValueSource.OBSERVED`; missing approval, false approval, stale observation time, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed. The workflow does not call `evaluate_route()`, assemble snapshots, calculate profitability, reconcile ledgers, mutate eligibility, plan execution, place orders, or enable live trading.

## Execution planning without orders

RX-027 adds `plan_execution_without_orders()` in `core/execution/planning.py`. It accepts one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing route decision, one funding verification result, one ledger reconciliation result, one fresh CapturePlan freshness evidence record, one execution-capability evidence record, and one explicit planning timestamp.

The workflow validates exact Capture, route, settlement, ENTRY `PAPER_ELIGIBLE` decision, verified funding settlement, reconciled ledger result, fresh plan evidence, and executable capability evidence before returning a `NonSendingExecutionPlan`. The plan records intended venues, symbols, entry/unwind sides, target notional, settlement timestamp, planning validity, and prerequisite event-sequence references. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, write ledger events, call adapters, import live runner behavior, create live `CapturePlan` objects, include credentials or sendable API requests, place orders, or enable live trading.

## Guarded live runner without orders

RX-028 adds `run_guarded_live_without_orders()` in `apps/live_runner/guarded.py`. It accepts one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing `NonSendingExecutionPlan`, one funding verification result, one ledger reconciliation result, one live-gate evidence bundle, one explicit evaluation timestamp, and explicit `ProductRules`.

The runner fails closed unless `ProductRules.live_trading_enabled is True`, the Capture/route/settlement identity is exact, funding is verified, ledger reconciliation is current, the live-gate bundle passes the existing risk-owned bundle check, and the existing non-sending plan is fresh and matches route identity plus prerequisite evidence references. Even when every prerequisite is exact, it returns only a no-order guarded readiness result. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay ledgers, write ledger events, call adapters, import order placement behavior, construct sendable exchange requests, place orders, or enable live trading by default.

## Approval-gated order placement boundary

RX-029 adds `OrderPlacementApproval`, `ApprovalGatedOrderPlacementResult`, and `run_approval_gated_order_boundary()` in `core/execution/orders.py`, plus `run_approval_gated_live_order_placement()` in `apps/live_runner/order_placement.py` to consume the app-local guarded result without reversing core/app imports.

The workflow requires explicit `ProductRules(live_trading_enabled=True)`, exact Capture/route/settlement identity, an exact no-order ready `GuardedLiveRunnerResult`, a fresh `NonSendingExecutionPlan`, and caller-supplied approval that matches the guarded evaluation timestamp plus the plan's prerequisite references. Only after all checks pass does it invoke the injected deterministic boundary. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, use credentials, create exchange request payloads, place real orders, or enable live trading by default.

## Read-only monitoring dashboard

RX-030 adds `render_capture_monitor_view()` in `apps/dashboard/read_only.py` for one existing `Capture`, one existing `RouteCandidate`, one explicit settlement timestamp, and already-derived fixture evidence only.

The renderer copies identity, decision status, prerequisite evidence state, non-sending plan state, guarded no-order readiness, approval evidence, approval-boundary result state, and existing economics values for display. Missing, malformed, stale, cross-identity, unverified, unreconciled, non-ready, false-approval, stale-approval, or boundary-blocked evidence renders as `missing` or `blocked`. It does not call `evaluate_route()`, assemble snapshots, calculate profitability, verify funding, reconcile ledgers, check live-gate bundles, plan execution, run guarded live readiness, call the approval boundary, write ledger events, call adapters, use credentials, perform network I/O, or place orders.

## Offline ledger reconciliation

The deterministic fake ledger reconciliation layer is downstream of route decisions, fake paper lifecycle history, and funding settlement verification. It replays append-only ledger evidence for one Capture, recomputes recorded funding settlement verification results from raw evidence through the canonical funding verifier replay, and records an explicit reconciliation result through `core/accounting/ledger.py`.

Missing, duplicated, non-contiguous, out-of-order, unknown, malformed, stale, forged, or contradictory ledger evidence fails closed as unreconciled. A reconciliation result records the checked `event_count` and `last_sequence`, and `is_ledger_explicitly_reconciled()` returns true only when the latest ledger event reconciles the exact current history. Reconciliation does not evaluate profitability, assemble snapshots, calculate EV, place orders, create `CapturePlan` objects, mutate route decisions, or enable live trading.

SQLite reopen coverage proves that `SQLiteLedger` keeps append-only sequence continuity across close/reopen boundaries. A later persisted append after successful reconciliation makes the prior explicit reconciliation stale until a new reconciliation result covers the current persisted history, and replay from reopened SQLite records remains deterministic.

SQLite reopen fail-closed coverage proves that malformed, stale, or contradictory appends persisted after reopening an existing `SQLiteLedger` remain unreconciled after SQLite round-trip. The helper-derived explicit reconciliation flag remains false for those histories, and replay from reopened records remains deterministic.

## Offline CapturePlan freshness gate

The deterministic fake CapturePlan freshness gate is downstream of route decisions, funding settlement verification, and ledger reconciliation. It consumes fake `CapturePlanFreshnessEvidence` values only; these are not executable order plans and do not contain exchange instructions.

Missing, stale, duplicated, cross-capture, cross-route, or cross-settlement plan evidence fails closed through `RejectReason.CAPTURE_PLAN_NOT_FRESH`. Fresh evidence alone is not permission to trade live: live trading remains disabled by default, and even with helper-derived reconciliation plus fresh evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline execution capability gate

The deterministic fake execution capability gate is downstream of route decisions, funding settlement verification, ledger reconciliation, and CapturePlan freshness. It consumes fake `ExecutionCapabilityEvidence` values that reference the existing four current `ExecutableQuote` contracts only.

Missing, stale, cross-route, wrong-side, wrong-target, partial-fill, contradictory, unknown-source, or non-orderbook-source execution evidence fails closed through existing centralized reject reasons. Fresh execution evidence alone is not permission to trade live: live trading remains disabled by default, and even with helper-derived reconciliation plus fresh CapturePlan and execution-capability evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline live gate evidence bundle

The deterministic fake live gate evidence bundle is downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability. It aggregates already-derived fake evidence into one `LiveGateEvidenceBundle` for the future live gate sequence.

The bundle records the current `capture_id`, `route_id`, funding settlement timestamp, funding-settlement verified flag, helper-derived ledger reconciliation flag, fake `CapturePlanFreshnessEvidence`, and fake `ExecutionCapabilityEvidence`. Bundle checking lives in `core/risk/gates.py` and reuses the existing plan freshness and execution-capability gates. It does not replay ledger history, recalculate funding, recalculate VWAP, evaluate profitability, create order plans, or enable live trading.

Missing, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale/missing plan evidence, or stale/missing/non-executable execution evidence fails closed through existing centralized reject reasons. Even with live trading manually enabled and exact fake bundle evidence, `evaluate_route()` still returns `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED` and no live `CapturePlan`.

## Offline live gate evidence bundle ledger recording

The fake bundle-check result can be recorded as append-only offline ledger evidence through `core/accounting/ledger.py` and replayed through `core/accounting/reconciliation.py`.

The recorded event stores the current route, fake `LiveGateEvidenceBundle`, evaluated timestamp, referenced route-decision, funding-verification, and ledger-reconciliation event sequences, plus the already-computed RX-012 bundle gate result. Replay reconstructs the same fake evidence and reruns the existing bundle gate without recalculating EV, fees, funding, VWAP, basis, or profitability. Missing, duplicated, stale, malformed, or contradictory bundle ledger evidence fails closed, and ledger reconciliation cannot pass over a contradictory bundle record. SQLite persistence coverage proves that valid, malformed, and contradictory bundle records round-trip through `storage/sqlite/ledger.py` with the same replay outcomes as in-memory ledger records.

A recorded successful fake bundle check still does not permit `LIVE_ELIGIBLE`: live trading remains disabled by default, and current route decisions stop at `PAPER_ELIGIBLE` with `LIVE_GATES_NOT_IMPLEMENTED`.

## Boundaries

Business logic has single-owner modules:

- fees: `core/economics/fees.py`
- funding: `core/economics/funding.py`
- liquidity/VWAP: `core/economics/liquidity.py`
- basis/unwind tracking: `core/economics/basis.py`
- EV: `core/economics/ev.py`
- risk gates: `core/risk/gates.py`
- route decision: `core/pipeline/evaluate.py`
- execution planning and orders: `core/execution/`
- ledger writes: `core/accounting/ledger.py`
- ledger reconciliation: `core/accounting/reconciliation.py`
- funding settlement verification: `core/monitoring/funding_settlement.py`
- execution capability gating: `core/risk/gates.py`
- live gate evidence bundling: `core/risk/gates.py`
- guarded live runner without orders: `apps/live_runner/guarded.py`
- explicit approval-gated order boundary: `core/execution/orders.py`
- guarded-result compatibility wrapper: `apps/live_runner/order_placement.py`

Venue adapters may fetch and normalize data only. They must not calculate EV, make route decisions, send orders, or write ledger events.
