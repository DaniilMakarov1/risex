# Implementation Plan

## Roadmap Source Of Truth

This file records the consolidated implementation roadmap. `NEXT_TASK.md` remains the only handoff contract for the next Codex session and must contain exactly one task. Later roadmap stages listed here are gated future work, not permission to implement them early or combine them with the current task.

The original product direction remains hedged funding capture on RiseX with hedge venue support inside a modular monolith:

- one `Capture` equals one funding settlement opportunity;
- one `evaluate_route(route, snapshot, mode)` route decision path;
- one `assemble_route_snapshot()` route snapshot assembly path;
- one append-only ledger;
- one owner module per business logic area;
- no canary architecture, hold-next-cycle logic, artificial filters, hidden buffers, or speculative live architecture.

RX-037 records explicit Product Owner roadmap direction supplied through Control Tower: the intended long-term end goal is a live-capable hedged funding capture system on RiseX with hedge venue support, initially Hyperliquid. The current implementation remains non-trading and fail-closed. Future work must advance toward live readiness through explicit, reviewable, fail-closed stages, and no live trading, private/account endpoint, credential, order, sendable exchange request, automation, or financially dangerous scope is authorized until an exact future task and explicit approval gate authorize it.

RX-052 records explicit Product Owner clarification supplied through Control Tower after RX-051: continue autonomously toward a working fake-money paper trader system before any live trading work is considered. This clarification shifts the next concrete product path from research-only reporting to paper-trading readiness, but only through existing fake paper lifecycle and ledger behavior. It does not authorize live trading, real order placement, private/account endpoints, credentials, account balances/state, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, or financially dangerous action.

RX-054 records explicit Product Owner clarification supplied through Control Tower after RX-053: continue beyond the manual one-route bridge toward a full fake-money paper trader system for serial strategy testing. Product Owner plans to test through a Telegram bot later, but Telegram is product direction only for now. RX-054 and RX-055 do not authorize Telegram credentials, bot tokens, external Telegram network transport, webhooks, alerts, messaging behavior, live trading, private/account endpoints, account balances/state, real orders, sendable exchange requests, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, or financially dangerous action.

RX-055 is reviewer-accepted and finalized on `main` as the manual serial fake-money paper session runner. It does not authorize Telegram transport, live trading, private/account endpoints, credentials, order placement, sendable exchange request construction, order payload construction, execution automation, execution planning, or financially dangerous action.

RX-056 is reviewer-accepted and finalized on `main` as governance/source-of-truth only. It records that the accepted RX-055 outcome plus Product Owner and Control Tower direction clearly ground exactly one next non-dangerous fake-money paper-trader handoff: manual local JSON report/history export for serial paper sessions.

RX-057 is reviewer-accepted and finalized on `main` as the manual paper session report/history export. It adds an explicit local `--session-report-json-path` JSON report/history export for the existing `paper-trade-session` command, while preserving no artifact writes when the path is absent and keeping the export downstream of accepted RX-055 session outcomes and paper ledger events.

RX-058 is reviewer-accepted and finalized on `main` as the local paper session command payload parser/fixture helper. It normalizes explicit JSON payload fixtures into the same route-list input shape accepted by `paper-trade-session --routes-json-path`, while preserving the accepted 25-route ENTRY validation boundary and avoiding session execution, adapter construction, ledger writes, report writes, Telegram transport, credentials, messaging, network calls, discovery, polling, execution automation, live/order/private/account scope, and second owner paths.

RX-059 is reviewer-accepted and finalized on `main` as governance/source-of-truth only. It records explicit Product Owner direction supplied through Control Tower that the needed next step toward a fuller fake-money paper trader system for serial strategy testing is RX-060 Local Paper Session Operator Package Builder. RX-059 prepares RX-060 as one local/manual/fake-money testing-support handoff while preserving all hard-stop gates and avoiding runtime changes in RX-059 itself.

RX-060 is implementation-complete on `task/rx-060-local-paper-session-operator-package-builder` and pending reviewer acceptance. It adds one explicit local/manual `build-paper-session-package` command that consumes local command payload fixtures through the RX-058 parser/validation boundary, writes one validated route-list JSON artifact and one descriptive preview/manifest JSON artifact, and stops before session execution, adapter construction, ledger writes, session report/history result writes, Telegram/network/credential behavior, live/order/private/account scope, discovery/ranking/polling, replay/reconciliation/storage changes, aggregate PnL invention, unknown-to-zero behavior, or second owner paths.

## Completed Accepted Work

- RX-000 through RX-007 established the project constitution, domain contracts, product rules, economics, per-venue observations, offline scan/refresh orchestration, fake paper lifecycle, and append-only ledger persistence scaffolding.
- RX-008 through RX-016 are an accepted offline safety-hardening detour. They added deterministic fail-closed replay coverage for funding settlement verification, ledger reconciliation, fake CapturePlan freshness, fake execution capability, fake live-gate evidence bundles, bundle ledger recording, SQLite bundle replay, SQLite reopen append continuity, and SQLite reopen fail-closed behavior.
- RX-018 tightened settlement timestamp alignment so one eligible route snapshot represents exactly one funding settlement opportunity.
- RX-019 updated repository handoff metadata after RX-018 review without changing product behavior.
- RX-020 hardened the existing `RouteCandidate` identity and selected-notional construction contract.
- RX-021 added deterministic fake paper-result attribution and PnL explanation downstream of existing route decisions and fake paper lifecycle events.
- RX-022 added the read-only RiseX public market-data observation adapter.
- RX-023 added the read-only Hyperliquid public market-data observation adapter.
- RX-024 added the real market-data route snapshot assembly handoff from read-only per-venue observations into the existing `assemble_route_snapshot()` path.
- RX-025 added the one-route real-data research runner that uses the existing adapter handoff and `evaluate_route()` path.
- RX-026 added approval-gated funding settlement verification for explicit caller-supplied observed evidence.
- RX-027 added non-sending execution planning for already-verified prerequisite evidence.
- RX-028 added a guarded no-order live runner for already-verified prerequisite evidence and existing non-sending execution-plan evidence.
- RX-029 added an explicit approval-gated order placement boundary downstream of guarded no-order readiness and non-sending execution planning.
- RX-030 added a read-only monitoring dashboard renderer for already-derived deterministic fixture evidence without adding decisions, polling, network I/O, or orders.
- RX-031 recorded the review-directed no-additional-fix disposition after RX-030 and prepared a Product Owner roadmap authorization gate without changing product behavior.
- RX-032 recorded the narrowed Product Owner authorization for exactly one next governance/docs task without changing product behavior or removing hard approval gates.
- RX-033 defined Control Tower autonomous task selection for future non-dangerous RX tasks from source-of-truth repository docs without changing product behavior or removing hard approval gates.
- RX-034 recorded the roadmap selection audit outcome and prepared a metadata-only RX-035 cleanup handoff without changing product behavior or removing hard approval gates.
- RX-035 recorded the post-audit handoff cleanup outcome and prepared a metadata-only RX-036 clarification gate without changing product behavior or removing hard approval gates.
- RX-036 recorded the roadmap source-of-truth clarification outcome and prepared a Product Owner roadmap direction gate before product/runtime scope resumes, without changing product behavior or removing hard approval gates.
- RX-037 recorded explicit Product Owner roadmap direction toward a live-capable hedged funding capture system and prepared RX-038 as one manual read-only public-data CLI step toward live readiness, without changing product behavior or removing hard approval gates.
- RX-038 added one manual read-only public-data `real-data-route` CLI entry point for one explicit RiseX plus Hyperliquid route, preserving the existing one-route real-data runner/evaluate path, no-argument fake CLI behavior, and all live/order/private/account-state gates.
- RX-039 completed explicit public funding-rate metadata into route-notional USD funding cash inside the existing one-route snapshot path, while keeping adapters read-only/public-only, fee cash unknown, and all live/order/private/account-state gates intact.
- RX-040 preserved explicit public fee-rate and account-tier fee-source metadata from existing read-only RiseX and Hyperliquid public adapter payloads on unknown fee cash values, while keeping adapter fee cash unknown and all live/order/private/account-state gates intact.
- RX-041 completed explicit public account-independent taker fee-rate metadata with selected RX-040 field/container provenance into entry plus immediate estimated-exit route-notional USD fee cash inside the existing one-route snapshot path, while keeping unsafe fee inputs unknown and all live/order/private/account-state gates intact.
- RX-042 recorded that no concrete safe post-RX-041 public/read-only runtime live-readiness handoff is clearly grounded in the current source-of-truth docs, prepared RX-043 as a narrow Product Owner direction gate, and did not change product/runtime behavior.
- RX-043 recorded that explicit Product Owner direction remains broad live-capable product direction only, does not authorize hard-stop scope, and still does not clearly ground one concrete safe public/read-only/non-trading runtime handoff.
- RX-044 recorded explicit Product Owner clarification selecting option A, Manual One-Route Public Readiness Report, prepared RX-045 as that one safe later runtime reporting task, and did not change product/runtime behavior.
- RX-045 added one opt-in manual public readiness report for one explicitly supplied RiseX plus Hyperliquid route, preserving existing public read-only adapter, snapshot, runner, fee/funding completion, and evaluation paths while keeping the conclusion display-only and non-trading.
- RX-046 recorded that no concrete safe post-RX-045 public/read-only/non-trading runtime handoff was clearly grounded in the accepted docs, prepared RX-047 as a narrow Product Owner direction gate, and did not change product/runtime behavior.
- RX-047 recorded explicit Product Owner and Control Tower direction selecting RX-048, opt-in structured JSON stdout for the existing manual one-route public readiness report, as the next safe handoff without changing product/runtime behavior.
- RX-048 added one opt-in structured JSON stdout format for the existing manual one-route public readiness report, preserving existing public read-only adapter, snapshot, runner, fee/funding completion, and evaluation paths while keeping output stdout-only, display/report-only, and non-trading.
- RX-049 recorded that no concrete safe post-RX-048 public/read-only/non-trading runtime handoff was clearly grounded in the accepted docs, prepared RX-050 as a narrow Product Owner direction gate, and did not change product/runtime behavior.
- RX-050 recorded that explicit Product Owner/Control Tower direction remained broad live-capable product direction only, prepared RX-051 as a narrow concrete clarification handoff, and did not change product/runtime behavior.
- RX-051 audited repository instruction/source-of-truth hygiene, removed the one stale tracked cross-project wording by rephrasing it generically, prepared RX-052 as the single next clarification handoff, and did not change product/runtime behavior.
- RX-052 recorded Product Owner clarification that the next concrete product path is a working fake-money paper trader system before live trading work, prepared RX-053 as one manual fake-money paper bridge, and did not change product/runtime behavior.
- RX-053 added one manual `paper-trade-route` fake-money bridge from one public one-route ENTRY decision into the existing fake paper lifecycle and append-only ledger.
- RX-054 recorded Product Owner clarification that the fake-money paper trader path should continue beyond the manual one-route bridge toward serial strategy testing, recorded Telegram as later interface direction only, prepared RX-055 as one manual serial paper session runner handoff, and did not change product/runtime behavior.
- RX-055 added one manual `paper-trade-session` fake-money serial runner for an operator-supplied local JSON route-list file capped at 25 exact explicit ENTRY routes, preserving existing decision, paper lifecycle, and ledger ownership paths.
- RX-056 recorded that the accepted RX-055 outcome plus Product Owner and Control Tower direction clearly ground exactly one next non-dangerous fake-money paper-trader handoff, manual local JSON report/history export for serial paper sessions, and did not change product/runtime behavior.
- RX-057 added one explicit local JSON report/history export for `paper-trade-session` results, requiring `--session-report-json-path` before writing any report artifact and preserving existing session owner paths, count-only/unknown-null semantics, and no aggregate PnL invention.
- RX-058 added one local-only paper session payload parser/fixture helper that normalizes explicit JSON payload fixtures into the accepted `paper-trade-session` route-list shape, reuses the paper-session validation boundary, and does not run sessions, construct adapters, write ledgers, write reports, send messages, call networks, add credentials, or add live/order/private/account scope.
- RX-Q001 and RX-Q002 added repository workflow, handoff validation, and supervised-worker governance.

## Accepted Offline Safety-Hardening Detour

RX-008 through RX-016 are accepted as fail-closed safety hardening only. They do not change the product strategy, do not make fake evidence executable, do not create a live runner, do not create live `CapturePlan` objects, do not connect to venues, do not place orders, and do not authorize more offline scaffolding unless a future task explicitly requires it.

The detour's purpose is to keep future live-adjacent work honest: funding settlement evidence, ledger history, fake plan freshness, fake execution capability, fake bundle checks, and SQLite replay must fail closed when evidence is missing, stale, duplicated, malformed, contradictory, or not current for the exact Capture, route, and funding settlement opportunity.

## Latest Accepted Product Task

RX-058 - Local Paper Session Command Payload Parser Fixtures is reviewer-accepted and finalized on `main`. It adds one local-only paper session payload parser/fixture helper in `apps/cli/paper_session_payloads.py`, keeps `paper-trade-session --routes-json-path` on the same validation boundary, and returns exact route-list dictionaries only. It preserves the RX-055 25-route explicit ENTRY cap, RX-057 report/export boundaries, unknown/null behavior by omitting economics/report fields, and no-session/no-adapter/no-ledger/no-report/no-network behavior.

## Previous Product Task

RX-057 - Manual Paper Session Report History Export is reviewer-accepted and finalized on `main`. It adds one explicit local JSON report/history export for the existing `paper-trade-session` command. The artifact is written only when the operator supplies `--session-report-json-path`, and its payload is built from the existing validated route inputs, serial session outcomes, and paper ledger events already produced through RX-055 owner paths. It preserves count-only known/unknown summary fields, string-or-null economics values, and explicit `aggregate_paper_net_profit_usd = null`.

## Earlier Product Task

RX-055 - Manual Serial Paper Session Runner is reviewer-accepted and finalized on `main`. It adds one explicit `paper-trade-session` command for an operator-supplied local JSON route-list file capped at 25 exact explicit RiseX plus Hyperliquid ENTRY routes. It validates the whole list before adapter construction, runs each route serially through `run_real_data_research_route_with_snapshot()` and the shared `evaluate_route(route, snapshot, mode)` path, delegates fake paper behavior to `run_paper_lifecycle()` when a public snapshot is available, writes fake paper events only through existing accounting ledger ownership, optionally persists through explicit local SQLite only, and prints deterministic per-route output plus count-only session summaries without aggregating PnL or turning unknowns into zero.

## Current Task Branch

RX-060 Local Paper Session Operator Package Builder is implementation-complete on its task branch and pending reviewer acceptance. Implementation completion is not acceptance; RX-058 remains the latest accepted product/runtime baseline on `main`, and RX-059 remains the latest accepted governance/source-of-truth baseline on `main` until reviewer acceptance and finalization.

## Previous Product Baseline

RX-053 - Manual One-Route Public Paper Trader Bridge remains the accepted one-route product/runtime baseline before RX-055. It adds one explicit `paper-trade-route` command for one public RiseX plus Hyperliquid route, requires `EvaluationMode.ENTRY`, reuses the existing one-route real-data runner and shared `evaluate_route(route, snapshot, mode)` path, delegates fake paper behavior to `run_paper_lifecycle()`, writes fake paper ledger events only through the existing accounting ledger ownership, and optionally persists them only through an explicit local SQLite ledger path.

## Previous Reporting Baseline

RX-048 - Structured JSON Stdout Public Readiness Report Output remains the previous accepted product/reporting baseline before RX-053. It adds one opt-in `real-data-route --public-readiness-report --public-readiness-report-format json` stdout format for exactly one explicit public route, reusing the accepted RX-045 manual public-readiness report evidence. It preserves the default one-decision text output and the default text public-readiness report, fails closed when the JSON format selector is supplied without `--public-readiness-report`, preserves unknown values as `null`/`UNKNOWN` with context, and does not change decisions, routes, adapters, economics rules, ledger state, execution, live gates, orders, private/account endpoints, credentials, account state, or live trading.

## Current Repository Handoff

RX-048 is reviewer-accepted and finalized on `main` as the prior accepted product/reporting task before RX-053. RX-049 is reviewer-accepted and finalized on `main` as the prior governance/source-of-truth task that prepared RX-050. RX-048 implements the concrete safe handoff selected by RX-047: an opt-in structured JSON stdout output for the existing RX-045 manual one-route public readiness report.

RX-048 reuses the existing public read-only one-route adapter handoff, retained snapshot/report helper, source-aware fee/funding completion, and `evaluate_route()` path, preserves the default one-decision text output and default text public-readiness report, and prepares RX-049 as a narrow post-RX-048 handoff clarification rather than inventing later runtime scope.

RX-049 inspected the accepted RX-048 outcome and current source-of-truth docs, found no clearly grounded concrete safe post-RX-048 public/read-only/non-trading runtime handoff, recorded the no-grounded-runtime-handoff conclusion, and prepares RX-050 as a narrow Product Owner direction gate. RX-049 changes no product/runtime behavior.

RX-050 is reviewer-accepted and finalized on `main` as the prior accepted governance/source-of-truth task that prepared RX-051. It inspects the accepted RX-049 governance/source-of-truth clarification outcome, the accepted RX-048 structured JSON stdout public readiness report outcome, current source-of-truth docs, and explicit Product Owner/Control Tower direction. The supplied direction confirms the long-term goal of live-capable hedged funding capture/trading on RiseX with Hyperliquid hedge support, but remains broad product direction only and still does not clearly identify one concrete safe public/read-only/non-trading runtime handoff after RX-048. RX-050 records the no-clarified-runtime-handoff conclusion and prepares RX-051 as a narrow concrete clarification handoff without changing product/runtime behavior.

RX-051 is reviewer-accepted and finalized on `main` as the accepted governance/source-of-truth task before RX-052 after explicit Control Tower direction. It audits tracked and hidden non-.git repository files for stale cross-project workflow references, repo-local instruction directories, and tracked stale generated artifacts. RX-051 remains governance/source-of-truth hygiene only, changes no product/runtime behavior, and prepares RX-052 as the carried-forward narrow concrete clarification handoff.

RX-052 is reviewer-accepted and finalized on `main` as the accepted governance/source-of-truth task before RX-054. It records Product Owner clarification that the next product goal is a working fake-money paper trader system before any live trading work. RX-052 itself does not implement runtime behavior; it prepares RX-053 as one manual fake-money paper-trader bridge from an existing public one-route real-data ENTRY decision into the existing fake paper lifecycle and append-only ledger.

RX-053 is reviewer-accepted and finalized on `main` as the accepted one-route product/runtime task before RX-055. It adds one explicit manual `paper-trade-route` command that validates one public RiseX plus Hyperliquid route, requires `EvaluationMode.ENTRY`, reuses the existing one-route real-data runner and shared `evaluate_route(route, snapshot, mode)` path, delegates fake paper behavior to `run_paper_lifecycle()`, writes fake paper ledger events only through the existing accounting ledger ownership, and optionally persists them only through an explicit local SQLite ledger path.

RX-054 is reviewer-accepted and finalized on `main` as the accepted governance/source-of-truth task before RX-056. It inspects the accepted RX-053 bridge outcome, records Product Owner clarification to continue toward serial fake-money paper strategy testing, records Telegram as later interface direction only, and prepares RX-055 Manual Serial Paper Session Runner as exactly one next non-dangerous handoff. RX-054 changes no product/runtime behavior.

RX-055 is reviewer-accepted and finalized on `main` as the accepted product/runtime task before RX-057. It adds one explicit manual `paper-trade-session` command for a local JSON route-list file capped at 25 exact explicit ENTRY routes, reuses the existing public one-route decision path, delegates fake paper handling to the existing fake paper lifecycle, keeps ledger writes inside existing accounting ownership, preserves unknown economics as count-only known/unknown summary fields, and keeps aggregate PnL as `None`.

RX-056 is reviewer-accepted and finalized on `main` as the latest accepted governance/source-of-truth task. It inspects the accepted RX-055 serial paper session runner, current source-of-truth docs, Product Owner direction toward serial fake-money paper strategy testing, and Control Tower review direction. It finds that exactly one next implementation handoff is grounded after RX-055: a manual local JSON report/history export for `paper-trade-session` results using explicit local output paths and existing session outcomes or paper ledger events only. The handoff is narrow test-enabling infrastructure for later Telegram command/display adaptation, but it must not add Telegram transport, bot tokens, webhooks, messaging, network calls, discovery, polling, execution automation, live/order/private/account, ledger replay/reconciliation, storage-migration, second-owner-path, or unknown-to-zero scope.

RX-057 is reviewer-accepted and finalized on `main` as the accepted product/runtime reporting task before RX-058. It implements the RX-056 handoff as one explicit local JSON report/history export for the existing manual session command and preserves RX-055 session ownership, no-write-without-path behavior, count-only summaries, unknown/null semantics, and explicit no aggregate PnL.

RX-058 is reviewer-accepted and finalized on `main` as the latest accepted product/runtime input-preparation task. It extracts the accepted paper session route-list validation boundary into `apps/cli/paper_session_payloads.py`, keeps the existing `paper-trade-session --routes-json-path` file loader on that boundary, and adds a local command payload fixture parser that returns exact route-list dictionaries only. It does not run sessions, construct adapters, write ledgers, write reports, send messages, call networks, add credentials, discover/rank/watchlist/poll/schedule, automate execution, change economics, mutate eligibility, add statuses/reasons, or create second owner paths.

RX-059 is reviewer-accepted and finalized on `main` as governance/source-of-truth only. It inspects the accepted RX-058 local payload parser outcome, the accepted RX-055 through RX-057 fake-money paper-trader testing trail, current source-of-truth docs, the supervised worker design checkpoint, and latest explicit Product Owner direction supplied through Control Tower. That direction grounds exactly one next safe local/manual/fake-money testing-support handoff: RX-060 Local Paper Session Operator Package Builder.

RX-060 is implementation-complete on its task branch as the local operator-package builder prepared by RX-059. Explicit Product Owner direction continues to ground implementation of needed fake-money paper trader testing-support steps. The next concrete non-dangerous handoff is RX-061 Local Paper Session Report Display Renderer, a local/manual display layer for already-written RX-057 session report JSON artifacts suitable for later Telegram display adaptation without Telegram transport, messaging/network credentials, execution automation, route discovery/ranking/polling, live/order/private/account scope, replay/reconciliation/storage changes, or financially dangerous stages.

## Remaining Gated Roadmap After RX-060 Implementation

Future stages must be promoted through `NEXT_TASK.md` one at a time and accepted before any later stage starts. RX-060 implements exactly one local/manual/fake-money testing-support handoff and does not authorize any additional trading, execution automation, execution planning, polling, ranking, discovery, ledger/storage/replay change, Telegram transport, credentials, messaging, alerts, webhooks, or live-order roadmap stage.

1. RX-061 Local Paper Session Report Display Renderer.


## RX-000 — Project Constitution and Walking Skeleton Foundation

Create repository docs, structure, Python test setup, minimal domain contracts, fake route evaluation, and append-only ledger tests. No real adapters, no live orders, and no external exchange connectivity.

## RX-001 — Domain Contracts and State Machine

Strengthen domain contracts and introduce the formal state machine for `Capture`, route lifecycle, decision history, and future `CapturePlan` freshness rules.

## RX-002 — Product Rules, Value Sources, and Central Reject Reasons

Make `ProductRules`, `ValueSource`, `EstimatedValue`, and `RejectReason` authoritative. Keep live trading disabled by default and enforce no-artificial-filter invariants.

## RX-002A — GitHub CI Workflow

Add minimal CI for pytest and compileall without secrets, deployment, linting, coverage, exchange connectivity, or live trading.

## RX-003 — Economics Engine Candidate

Add source-aware offline economics for fees, funding, order-book VWAP liquidity, immediate roundtrip cost, basis/unwind PnL, and Entry EV through the single `evaluate_route()` pipeline.

RX-003 FIX repairs the candidate contract before review acceptance:

- Route/snapshot alignment is centralized in `core/risk/gates.py`.
- `RouteCandidate` explicitly owns route venues, symbols, target notional, and intended opposing entry sides.
- Roundtrip quote pairing rejects venue, symbol, side, target-notional, executability, and VWAP mismatches.
- Expected missing economics input failures use a scoped exception contract.
- RX-003 never constructs `CapturePlan` or `LIVE_ELIGIBLE` decisions.
- `VenueAdapter` is read-only and per-venue; RX-004 supersedes the order-book primitive with `fetch_observation()`.

## RX-004 — Per-Venue Observation and Route Snapshot Contracts

Add normalized per-venue `VenueObservation` inputs and the single `assemble_route_snapshot()` path that converts route-aligned observations into `VenueSnapshot` values for `evaluate_route()`.

## RX-005 — Offline Scan Orchestration over Per-Venue Observations

Add deterministic fake offline orchestration over multiple `RouteCandidate` values and normalized observation mappings. Every successful candidate uses `assemble_route_snapshot()` and then `evaluate_route()`. Missing or contradictory observations fail closed before evaluation without trades, orders, ledger writes, paper lifecycle, live trading, or `CapturePlan` creation.

## RX-006 — Broad Scan and Focused Refresh orchestration

Add deterministic fake Broad Scan and Focused Refresh over the same offline observation, snapshot assembly, and `evaluate_route()` path. Keep the scan/refresh layer fake-data-only, read-only, non-trading, and free of paper execution, ledger writes, real adapters, live trading, or `CapturePlan` creation.

## RX-007 — Paper Runner Lifecycle and Append-only Ledger Persistence

Add deterministic fake paper lifecycle downstream of existing `DecisionResult` values and append-only ledger persistence scaffolding. Start paper capture execution only for `PAPER_ELIGIBLE` decisions, use the single Capture state machine, write all fake paper history through `core/accounting/ledger.py`, and keep real adapters, orders, live trading, live runner behavior, `CapturePlan` creation, second decision paths, second EV paths, and second snapshot assembly paths out of scope.

## RX-008 — Funding Settlement Verifier Design and Fake Replay Coverage

Add deterministic offline funding settlement verifier contracts and fake replay coverage. Model required pre-settlement checkpoints at T-20 minutes, T-60 seconds, T-10 seconds, and T-5 seconds. Write checkpoint evidence, observed settlement evidence, and verification results through append-only ledger helpers. Replay ledger events to compare fake expected funding/notional inputs against fake observed settlement records, failing closed on missing, unknown, or inconsistent evidence. Keep the verifier downstream of existing route decisions, snapshots, Capture lifecycle, and ledger boundaries without real adapters, order placement, live `CapturePlan` creation, route eligibility mutation, or live trading.

## RX-009 — Ledger Reconciliation Gate Design and Fake Replay Coverage

Add deterministic offline ledger reconciliation contracts and fake replay coverage. Reconcile one Capture ledger history from append-only route decision, fake paper lifecycle, funding evidence, and funding settlement verification events. Record reconciliation results through ledger helpers, fail closed on missing, duplicated, out-of-order, or contradictory evidence, and require explicit reconciliation before any future live path can pass the ledger reconciliation gate. Keep live trading disabled and do not create live `CapturePlan` objects.

## RX-010 — Fresh CapturePlan Gate Design and Fake Replay Coverage

Add deterministic offline CapturePlan freshness gate contracts and fake replay coverage. Require exactly one fake non-executable freshness evidence record for the current Capture, route, and funding settlement opportunity before any future live path can pass the plan freshness gate. Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and append-only ledger boundaries without creating live `CapturePlan` objects, executable order plans, adapters, orders, or live trading.

## RX-011 — Offline Execution Capability Gate Design and Fake Replay Coverage

Add deterministic offline execution-capability gate contracts and fake replay coverage. Require exactly one fake non-executable evidence record with current order-book `ExecutableQuote` values proving that the current route can still execute its full selected target notional on RiseX entry, hedge entry, RiseX unwind, and hedge unwind sides before any future live path can pass the execution-capability gate. Keep the gate downstream of route decisions, ledger reconciliation, funding settlement verification, and CapturePlan freshness without recalculating VWAP/EV, creating order plans, adapters, orders, or live trading.

## RX-012 — Offline Live Gate Evidence Bundle Design and Fake Replay Coverage

Add deterministic offline live-gate evidence bundle contracts and fake replay coverage. Require one fake non-executable aggregate bundle for the current Capture, route, and funding settlement opportunity before any future live path can consider the full live gate sequence. Keep the bundle downstream of route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability without replaying ledger/funding evidence, recalculating VWAP/EV, creating order plans, adapters, orders, or live trading.

## RX-013 — Offline Live Gate Evidence Bundle Ledger Recording and Replay Coverage

Add deterministic append-only ledger recording and replay coverage for fake live gate evidence bundle check results. Keep recording in `core/accounting/ledger.py`, replay validation in `core/accounting/reconciliation.py`, bundle checking in `core/risk/gates.py`, and live eligibility still blocked by `LIVE_GATES_NOT_IMPLEMENTED`.

## RX-014 — Offline Live Gate Evidence Bundle SQLite Persistence Replay Coverage

Add deterministic SQLite persistence replay coverage for fake live gate evidence bundle ledger records. Prove that valid, malformed, and contradictory `live_gate_evidence_bundle_recorded` payloads round-trip through `storage/sqlite/ledger.py` and replay with the same outcomes as in-memory ledger records, without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## RX-015 — Offline SQLite Ledger Reopen Append Continuity Replay Coverage

Add deterministic SQLite reopen coverage for append-only sequence continuity and reconciliation freshness. Prove that appending after reopening an existing `SQLiteLedger` continues from the last persisted sequence, that a later persisted append makes prior reconciliation stale, and that a later reconciliation over reopened records replays deterministically without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## RX-016 — Offline SQLite Ledger Reopen Fail-Closed Replay Coverage

Add deterministic SQLite reopen coverage proving that malformed, stale, or contradictory append-only evidence persisted after reopening an existing `SQLiteLedger` remains unreconciled after SQLite round-trip. Prove deterministic reconciliation replay from reopened SQLite records and the helper-derived explicit reconciliation gate remains false without changing storage architecture, route decisions, economics, risk gates, adapters, orders, or live trading.

## RX-018 — Settlement Timestamp Alignment Contract

Tighten route/snapshot alignment so RiseX and hedge funding settlement timestamps must match before a route can pass into executability, Entry EV, and paper eligibility. Preserve per-leg settlement timestamps in `assemble_route_snapshot()`, fail mismatches through existing `RejectReason.TECHNICALLY_NOT_EXECUTABLE`, and avoid changing economics, VWAP/liquidity, adapters, orders, live behavior, route statuses, reject reasons, or second decision paths.

## RX-019 — Reviewer-Directed Follow-up After RX-018

Apply reviewer-directed repository handoff metadata fixes after RX-018 acceptance. Keep RX-018 as the latest accepted product baseline, record RX-019 as metadata-only follow-up, and prepare the next task prompt without changing product behavior.

## RX-020 — RouteCandidate Identity And Notional Contract Hardening

Harden the existing `RouteCandidate` construction contract so malformed capture id, route id, venues, symbols, entry sides, or target notional fail before snapshot assembly, route evaluation, paper lifecycle, ledger evidence, or future live-gate evidence can consume the route. Preserve `assemble_route_snapshot()` and `evaluate_route(route, snapshot, mode)` as the single snapshot and decision paths, keep positive below-minimum notionals in the existing minimum-notional risk gate, and avoid real adapters, market-data assembly, paper-result attribution, execution planning, live behavior, orders, route statuses, reject reasons, or later roadmap stages.

## RX-021 — Paper Result Attribution And PnL Explanation

Add deterministic paper-result attribution and PnL explanation downstream of existing route decisions and fake paper lifecycle events. Preserve fake paper start eligibility exactly as ENTRY `PAPER_ELIGIBLE`, explain non-started decisions through deterministic mode/status blockers, copy existing `DecisionResult` economics into inspectable paper results and optional paper ledger payloads, and keep missing economics as missing instead of zero.

RX-021 must not recalculate EV, fees, funding, VWAP, liquidity, basis, spread, slippage, or profitability; mutate route eligibility; add route statuses or reject reasons; create adapters, orders, live runner behavior, executable `CapturePlan`, or a second ledger/replay path.

## RX-022 — Read-only RiseX Observation Adapter

Add a read-only RiseX adapter that fetches and normalizes per-venue `VenueObservation` inputs only. Keep route snapshot assembly in `assemble_route_snapshot()`, route decisions in `evaluate_route()`, and all trading/execution behavior out of scope.

RX-022 implementation notes:

- `core/venues/risex.py` fetches public `GET /v1/markets` and `GET /v1/orderbook` data and returns one normalized `VenueObservation`.
- RiseX funding rates and fee bps are not converted into USD cash flow inside the adapter because `VenueObservation` requires source-aware cash values and `fetch_observation(symbol)` has no selected notional or account fee tier.
- Missing or malformed markets, settlement timestamps, orderbook sides, prices, quantities, or observation timestamps fail closed before a `VenueObservation` is returned.
- RX-022 does not assemble route snapshots, evaluate routes, rank routes, write ledger events, create plans, use private endpoints, place orders, add live runner behavior, or add a Hyperliquid adapter.

## RX-023 — Read-only Hyperliquid Observation Adapter

Add a read-only Hyperliquid adapter that fetches and normalizes per-venue `VenueObservation` inputs only. Keep route snapshot assembly in `assemble_route_snapshot()`, route decisions in `evaluate_route()`, and all trading/execution behavior out of scope.

RX-023 implementation notes:

- `core/venues/hyperliquid.py` posts only public `type=metaAndAssetCtxs`, `type=l2Book`, and `type=predictedFundings` requests to Hyperliquid `/info` and returns one normalized `VenueObservation`.
- Hyperliquid funding rates and fee schedules are not converted into USD cash flow inside the adapter because `VenueObservation` requires source-aware cash values and `fetch_observation(symbol)` has no selected notional, side, or account fee tier.
- Missing or malformed market metadata, asset contexts, orderbook sides, prices, sizes, observation timestamps, or predicted `HlPerp.nextFundingTime` values fail closed before a `VenueObservation` is returned.
- RX-023 does not assemble route snapshots, evaluate routes, rank routes, write ledger events, create plans, use private account endpoints, place orders, add live runner behavior, or change the RiseX adapter.

## RX-024 — Real Market-Data Route Snapshot Assembly

Add the smallest real market-data route snapshot assembly handoff that consumes existing read-only per-venue observations and calls the existing `assemble_route_snapshot()` path for one `RouteCandidate` at a time.

RX-024 implementation notes:

- `core/pipeline/snapshot.py` owns `assemble_route_snapshot_from_adapters()`.
- The handoff calls `fetch_observation(route.risex_symbol)` once on the RiseX adapter and `fetch_observation(route.hedge_symbol)` once on the hedge adapter.
- The handoff passes the two returned `VenueObservation` values into the existing `assemble_route_snapshot()` function and relies on that path for route-aligned snapshot construction and metadata validation.
- Non-observation adapter returns and contradictory route/observation metadata fail before any route decision can run.
- RX-024 does not call `evaluate_route()`, calculate EV, rank routes, mutate eligibility, write ledger events, start paper lifecycle, create plans, place orders, add private endpoints, add credentials, add live runner behavior, or create a second snapshot assembly path.

## RX-025 — Real-Data Research Runner

Add the smallest non-trading one-route real-data research runner that consumes one existing `RouteCandidate`, existing read-only venue adapters, the existing real market-data snapshot handoff, and the existing `evaluate_route(route, snapshot, mode)` path.

RX-025 implementation notes:

- `apps/research_runner/real_data.py` owns `run_real_data_research_route()`.
- The runner accepts one existing `RouteCandidate`, one RiseX `VenueAdapter`, one hedge `VenueAdapter`, an explicit timezone-aware assembly timestamp, and one `EvaluationMode`.
- Snapshot creation flows through `assemble_route_snapshot_from_adapters()` and then the existing `assemble_route_snapshot()` path.
- Route decisions flow through `evaluate_route(route, snapshot, mode)` only after successful snapshot assembly.
- Adapter or snapshot handoff failures return a deterministic `REJECTED` decision with `RejectReason.REQUIRED_LIVE_DATA_MISSING` and do not call `evaluate_route()`.
- RX-025 does not discover routes, rank routes, change fake runner behavior, write ledger events, start paper lifecycle, verify funding settlement, create plans, place orders, add private endpoints, add credentials, add live runner behavior, or create a second snapshot or decision path.

## RX-026 — Approval-Gated Real Funding Settlement Verification

Add the smallest approval-gated funding settlement verification path for one existing `Capture`, one existing `RouteCandidate`, and one explicit funding settlement timestamp.

RX-026 implementation notes:

- `core/monitoring/funding_settlement.py` owns `verify_approval_gated_funding_settlement()`.
- The workflow validates exact `Capture`/`RouteCandidate`/settlement timestamp identity before evidence is appended.
- Settlement evidence is recorded through the existing `append_funding_settlement_evidence_event()` helper and existing `funding_settlement_evidence_recorded` event type.
- Canonical funding settlement replay requires `approval_granted=True`, `observed_at == settlement_time`, and actual funding/notional values with `ValueSource.OBSERVED`.
- Missing approval, false approval, stale observation time, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed.
- RX-026 does not call `evaluate_route()`, assemble snapshots, calculate profitability, mutate route eligibility, start paper lifecycle, reconcile ledgers, plan execution, place orders, add private endpoints, add credentials, add live runner behavior, or create a second funding verifier, ledger-write path, replay path, snapshot path, or decision path.

## RX-027 — Execution Planning Without Orders

Add the smallest non-sending execution planning workflow for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-derived prerequisite evidence.

RX-027 implementation notes:

- `core/execution/planning.py` owns `plan_execution_without_orders()` and `NonSendingExecutionPlan`.
- The workflow accepts exact Capture/route/settlement inputs plus an existing ENTRY `PAPER_ELIGIBLE` `DecisionResult`, verified `FundingSettlementVerificationResult`, reconciled `LedgerReconciliationResult`, one fresh `CapturePlanFreshnessEvidence`, one fresh `ExecutionCapabilityEvidence`, and an explicit timezone-aware planning timestamp.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, or non-executable execution capability evidence fails closed through existing centralized reject reasons.
- The returned plan describes intended venues, symbols, entry and unwind sides, target notional, settlement timestamp, validity, and prerequisite event-sequence references only.
- RX-027 does not call `evaluate_route()`, assemble snapshots, calculate profitability, write ledger events, replay ledgers, call adapters, import live runner behavior, create live `CapturePlan` objects, place orders, include credentials or sendable API requests, enable live trading, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, or live execution path.

## RX-028 — Guarded Live Runner Without Orders

Add the smallest guarded live runner workflow for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing non-sending execution plan, and already-derived prerequisite evidence.

RX-028 implementation notes:

- `apps/live_runner/guarded.py` owns `run_guarded_live_without_orders()` and `GuardedLiveRunnerResult`.
- The workflow requires explicit `ProductRules(live_trading_enabled=True)` before any no-order ready state. Missing rules, default rules, or non-bool truthy switch values fail closed with `LIVE_TRADING_DISABLED`.
- The workflow accepts exact Capture/route/settlement inputs plus existing verified funding settlement evidence, current ledger reconciliation evidence, a passing `LiveGateEvidenceBundle`, one fresh `NonSendingExecutionPlan`, and an explicit timezone-aware evaluation timestamp.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution capability evidence, missing non-sending plan, stale non-sending plan, live switch disabled, or sendable order material fails closed through existing centralized reject reasons.
- A successful result is no-order readiness only. RX-028 does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, import order placement behavior, create live `CapturePlan` objects, construct sendable exchange requests, place orders, enable live trading by default, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, execution-planning, or order path.

## RX-029 — Explicit Approval-Gated Order Placement Boundary

Add the smallest explicit approval-gated order placement boundary for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, one existing no-order ready guarded live runner result, one existing non-sending execution plan, and one caller-supplied approval.

RX-029 implementation notes:

- `core/execution/orders.py` owns `OrderPlacementApproval`, `ApprovalGatedOrderPlacementResult`, and `run_approval_gated_order_boundary()`.
- `apps/live_runner/order_placement.py` owns `run_approval_gated_live_order_placement()` as a thin app wrapper that consumes exact `GuardedLiveRunnerResult` values without making `core/execution` import app-layer code.
- The workflow requires explicit `ProductRules(live_trading_enabled=True)`, exact Capture/route/settlement identity, no-order ready guarded result identity, a fresh existing `NonSendingExecutionPlan`, and approval evidence tied to the guarded result timestamp plus plan prerequisite references.
- Missing, stale, malformed, cross-capture, cross-route, cross-settlement, failed existing live prerequisites, non-ready guarded result, disabled live switch, missing/stale non-sending plan, missing approval, false approval, stale approval, or cross-identity approval fails closed before the injected deterministic boundary is invoked.
- RX-029 does not call `evaluate_route()`, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, use credentials, create exchange request payloads, place real orders, enable live trading by default, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## RX-030 — Read-Only Monitoring Dashboard Without Decisions Or Orders

Add the smallest read-only monitoring/dashboard surface for one existing `Capture`, one existing `RouteCandidate`, one explicit funding settlement timestamp, and already-derived caller-supplied deterministic evidence.

RX-030 implementation notes:

- `apps/dashboard/read_only.py` owns `render_capture_monitor_view()`.
- The renderer displays exact identity, existing route decision status, funding verification state, ledger reconciliation state, live-gate bundle state, non-sending execution plan state, guarded no-order readiness state, approval evidence state, approval-boundary result state, and copied economics values.
- Missing, malformed, stale, cross-capture, cross-route, cross-settlement, unverified, unreconciled, non-ready, false approval, stale approval, or boundary-blocked inputs render as missing or blocked display state.
- Missing economics remain missing display values instead of zero.
- RX-030 does not call `evaluate_route()`, assemble snapshots, calculate profitability, verify funding, reconcile ledgers, check live-gate bundles, plan execution, run guarded live readiness, call approval-boundary execution, write ledger events, call adapters, use credentials, perform network I/O, place orders, enable live trading, add route statuses, add reject reasons, or create a second decision, snapshot, verifier, ledger-write, replay, economics, live-runner, execution-planning, or order path.

## RX-031 — Review-Directed Follow-up After RX-030

Apply only explicit reviewer-directed dashboard fixes or repository handoff metadata updates after RX-030 acceptance. In the absence of discoverable actionable reviewer feedback in local repo/git evidence or GitHub connector context, RX-031 remains metadata-only: it records the no-additional-fix disposition, leaves dashboard/product code unchanged, and prepares a Product Owner authorization gate for the next single handoff.

## RX-032 — Product Owner Roadmap Authorization Gate

Record the Product Owner authorization supplied through Control Tower as authorization for exactly one next governance/docs task. The authorization permits preparing a workflow change so Control Tower may autonomously select, create, run, review, fix, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.

RX-032 does not itself change Control Tower autonomy rules. It does not authorize live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions without explicit user approval.

## RX-033 — Control Tower Autonomous Task Selection Governance

Define the repository workflow rule that, after RX-033 reviewer acceptance, Control Tower may autonomously select, create, run, coordinate review/fixes for, and finalize future non-dangerous RX tasks from source-of-truth repository docs without asking the user to name each next task.

RX-033 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, source-of-truth repository docs, Parent ownership, worker checkpoint requirements, and explicit reviewer acceptance. It does not authorize live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, or financially dangerous actions without explicit user approval.

## RX-034 — Control Tower Roadmap Selection Audit Gate

Autonomously inspect the source-of-truth repository docs after RX-033 reviewer acceptance and prepare exactly one next RX handoff. The audit found that `IMPLEMENTATION_PLAN.md`, `STATUS.md`, and `NEXT_TASK.md` clearly identify RX-034 as the current handoff but do not clearly ground a concrete post-RX-034 product/runtime task. Under the RX-034 fallback rule, prepare RX-035 as one metadata-only post-audit handoff cleanup rather than inventing product scope or requiring Product Owner approval for ordinary safe governance work.

RX-034 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, and explicit reviewer acceptance. It does not change product behavior, dashboard behavior, route discovery, ranking, polling, adapters, market-data calls, private endpoints, credentials, account state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, replay behavior, route statuses, reject reasons, live trading by default, or any product/runtime abstraction.

## RX-035 — Post-RX-034 Roadmap Handoff Cleanup

After RX-034 reviewer acceptance, record the roadmap selection audit outcome and prepare exactly one next RX handoff without inventing product or runtime scope. RX-035 re-inspects the source-of-truth docs and keeps the work metadata-only because they still do not clearly ground a concrete non-dangerous post-RX-034 product/runtime task.

Under the post-audit fallback path, RX-035 prepares RX-036 as one metadata-only roadmap source-of-truth clarification gate. RX-035 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, reviewer-only acceptance, and hard approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions.

RX-035 does not change product behavior, dashboard behavior, route discovery, ranking, polling, adapters, market-data calls, private endpoints, credentials, account state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, replay behavior, route statuses, reject reasons, live trading by default, or any product/runtime abstraction.

## RX-036 — Roadmap Source-of-Truth Clarification Gate

After RX-035 reviewer acceptance, clarify the post-audit roadmap source of truth without inventing product or runtime scope. RX-036 re-inspects the source-of-truth docs and keeps the work metadata-only because they still do not clearly ground a concrete non-dangerous post-RX-035 product/runtime task.

Under the clarification fallback path, RX-036 prepares RX-037 as one Product Owner roadmap direction gate. RX-037 must record explicit Product Owner roadmap direction before product/runtime scope resumes, while preserving RX-033 autonomy for ordinary non-dangerous repository work and preserving hard approval gates for live trading, order placement, sendable exchange requests, private endpoints, credentials, account balances/state, destructive reset, unsafe scope, and financially dangerous actions.

RX-036 preserves one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, reviewer-only acceptance, and hard approval gates.

RX-036 does not change product behavior, dashboard behavior, route discovery, ranking, polling, adapters, market-data calls, private endpoints, credentials, account state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, replay behavior, route statuses, reject reasons, live trading by default, or any product/runtime abstraction.

## RX-037 — Product Owner Roadmap Direction Gate

After RX-036 reviewer acceptance, RX-037 records explicit Product Owner roadmap direction supplied through Control Tower before product/runtime scope resumes.

The recorded direction is that RiseX Points Farmer is intended to become a live-capable hedged funding capture system on RiseX with hedge venue support, initially Hyperliquid. The current implementation remains non-trading and fail-closed, and future work must advance toward live readiness through explicit, reviewable, fail-closed stages without enabling live trading by default.

Under this direction, RX-037 prepares exactly one next task: RX-038, a manual one-route real-data CLI toward live readiness. RX-038 must use existing read-only public RiseX and Hyperliquid adapters, the existing one-route real-data snapshot handoff, and the existing one-route real-data research runner/evaluate path. It must not add route discovery, ranking, watchlists, polling, background loops, automatic refresh, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, or live trading by default.

RX-037 preserves RX-033 autonomy for ordinary non-dangerous tasks grounded in source-of-truth docs, one RX task at a time, one clean executor task, one task branch, exactly-one-task `NEXT_TASK.md`, Parent ownership, worker checkpoint requirements, reviewer-only acceptance, and hard approval gates.

RX-037 does not change product behavior, dashboard behavior, route discovery, ranking, polling, adapters, market-data behavior, private endpoints, credentials, account state, order placement, sendable exchange requests, execution automation, route evaluation, snapshot assembly, profitability calculation, funding verification, ledger reconciliation, live-gate checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, replay behavior, route statuses, reject reasons, live trading by default, or any product/runtime abstraction.

## RX-038 — One-Route Real Data CLI Toward Live Readiness

After RX-037 reviewer acceptance, RX-038 adds one manual CLI entry point for one explicitly supplied RiseX plus Hyperliquid route.

RX-038 implementation notes:

- `apps/cli/main.py` owns the `real-data-route` command.
- The command requires explicit route id, capture id, exact RiseX and Hyperliquid venue names, symbols, opposing entry sides, positive finite target notional, evaluation mode, and timezone-aware assembly timestamp.
- Missing or malformed identity, venue, symbol, side, mode, target notional, or assembly timestamp inputs fail before public adapter construction.
- After validation, the CLI instantiates the existing read-only public RiseX and Hyperliquid adapters and delegates to `run_real_data_research_route()`.
- Existing real-data snapshot creation remains inside the RX-024 adapter handoff, called only through the RX-025 runner, and route decisions remain inside the existing `evaluate_route()` path through that runner.
- The command prints deterministic one-decision output with route id, mode, status, reasons, net profit, and existing entry EV fields while preserving missing economics as `None`.
- Existing no-argument `python3 -m apps.cli.main` fake Broad Scan/Focused Refresh behavior remains unchanged.

RX-038 does not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second decision, snapshot, EV, VWAP, ledger-write, replay, execution-planning, or live execution path.

## RX-039 — Public One-Route Economics Source Completion

After RX-038 reviewer acceptance, RX-039 adds the smallest source-aware public-data-only funding economics completion for one explicitly supplied RiseX plus Hyperliquid route.

RX-039 implementation notes:

- `core/venues/risex.py` and `core/venues/hyperliquid.py` preserve explicit public funding-rate metadata from existing public responses while still returning unknown USD funding cash from `fetch_observation(symbol)`.
- `core/economics/funding.py` owns `complete_public_funding_cash_flow()`, which converts public funding-rate metadata into `ValueSource.OBSERVED` USD funding cash only when the existing route target notional and leg entry side are available.
- Positive funding rates mean longs pay shorts, so `buy` legs use `-rate * notional` and `sell` legs use `rate * notional`.
- `core/pipeline/snapshot.py` calls the funding-owned completion helper inside the existing `assemble_route_snapshot()` path before building the existing `FundingSnapshot`.
- `assemble_route_snapshot_from_adapters()`, `run_real_data_research_route()`, `evaluate_route()`, and `apps/cli/main.py` keep their existing one-route handoff, runner, decision, and output paths.
- Missing, malformed, non-finite, non-public, or ungrounded funding-rate inputs remain `ValueSource.UNKNOWN`; account-tier fee cash remains unknown.

RX-039 does not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-040 — Public One-Route Fee Source Metadata Preservation

After RX-039 reviewer acceptance, RX-040 adds the smallest source-aware public-data-only fee-source metadata preservation for one explicitly supplied RiseX plus Hyperliquid route.

RX-040 implementation notes:

- `core/venues/risex.py` and `core/venues/hyperliquid.py` preserve whitelisted explicit public fee-rate fields from existing public responses on `FeeComponent.amount_usd.metadata`.
- The adapters also preserve public account-tier fee-source field provenance as metadata while marking it `account_tier_dependent`.
- Fee cash remains `ValueSource.UNKNOWN` with `value=None`; RX-040 does not calculate fee cash, add defaults, or change Entry EV.
- The existing `assemble_route_snapshot()` path preserves the metadata by concatenating the existing fee components from both venue observations.
- `assemble_route_snapshot_from_adapters()`, `run_real_data_research_route()`, `evaluate_route()`, and `apps/cli/main.py` keep their existing one-route handoff, runner, decision, and output paths.
- Missing, malformed, non-finite, non-public, account-state-dependent, account-tier-dependent, or ungrounded fee inputs remain unknown and cannot become zero.

RX-040 does not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, fee cash completion, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-041 — Public One-Route Account-Independent Fee Cash Completion

After RX-040 reviewer acceptance and finalization, RX-041 should add the smallest fee-owned public-data-only completion from explicit account-independent public fee-rate metadata into route-notional USD fee cash for one explicitly supplied RiseX plus Hyperliquid route.

RX-041 implementation notes:

- `core/economics/fees.py` should own any fee cash completion helper and continue to own fee validation/calculation.
- Completion may use only explicit RX-040 metadata that is public, finite, `account_independent`, not account-tier schedule metadata, taker-role metadata, backed by selected public field/container provenance, and grounded by the existing one-route `RouteCandidate.target_notional_usd`.
- Completed fee cash represents the current entry plus immediate estimated-exit taker fills for that venue: `taker_rate * target_notional_usd * 2`.
- Fee cash must remain unknown for missing, malformed, non-finite, non-public, maker-only, ambiguous, missing-provenance, account-tier-dependent, account-state-dependent, or ungrounded metadata.
- The existing `assemble_route_snapshot()` path calls the fee-owned helper while building the existing `FeeModel`; the adapter handoff, one-route real-data runner, route decision pipeline, and manual CLI output path remain the same.

RX-041 must not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-042 — Post-RX-041 Public Live-Readiness Handoff Clarification

After RX-041 reviewer acceptance, RX-042 inspects the source-of-truth docs and the accepted RX-041 outcome to identify exactly one next non-dangerous public/read-only live-readiness handoff if one is clearly grounded.

RX-042 implementation notes:

- If a concrete safe next public/read-only product/runtime task is clearly grounded in `NEXT_TASK.md`, `IMPLEMENTATION_PLAN.md`, `STATUS.md`, `DECISIONS.md`, Product Owner direction, and repository invariants, prepare that exact one task in `NEXT_TASK.md`.
- If no such task is clearly grounded, record that no concrete post-RX-041 runtime step is source-grounded yet and prepare a narrow clarification handoff instead of inventing scope.
- Preserve RX-041 as pending or accepted according to explicit reviewer evidence; do not treat implementation completion as reviewer acceptance.
- Keep RX-042 docs/governance-only unless a clearly grounded non-dangerous handoff is selected for later work.

RX-042 branch outcome:

- RX-041 is reviewer-accepted and finalized on `main`.
- The current source-of-truth docs record the long-term live-capable product direction, but they do not clearly ground a concrete next public/read-only runtime task after RX-041.
- RX-042 therefore records the no-grounded-runtime-handoff conclusion and prepares RX-043 as one narrow Product Owner direction gate instead of inventing route discovery, polling, private endpoint, account-state, order, execution automation, or live-trading scope.

RX-042 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-043 — Product Owner Public Live-Readiness Handoff Direction Gate

After RX-042 reviewer acceptance, RX-043 should record explicit Product Owner direction, supplied through Control Tower or source-of-truth docs, for exactly one next non-dangerous public/read-only/non-trading live-readiness handoff before runtime scope resumes.

RX-043 implementation notes:

- Treat RX-043 as governance/source-of-truth only.
- If explicit Product Owner direction clearly identifies one concrete safe public/read-only/non-trading runtime task, prepare exactly that one later task in `NEXT_TASK.md`.
- If explicit Product Owner direction is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve RX-041 as the latest accepted product baseline unless a later reviewer-accepted product task exists.
- Preserve RX-042 as pending or accepted according to explicit reviewer evidence.

RX-043 accepted outcome:

- RX-042 is reviewer-accepted and finalized on `main`; RX-041 remains the latest accepted product baseline.
- The explicit Product Owner direction supplied through Control Tower confirms the long-term goal of a live-capable hedged funding capture/trading system on RiseX with Hyperliquid hedge support.
- That direction remains broad product direction only. It is not authorization for live trading, private/account endpoints, credentials, account balances/state, orders, sendable exchange requests, execution automation, destructive actions, unsafe scope, or financially dangerous actions.
- The docs plus explicit Product Owner direction still do not clearly identify one concrete safe public/read-only/non-trading runtime handoff. RX-043 therefore records the no-clarified-runtime-handoff conclusion and prepares RX-044 as one narrow Product Owner concrete public runtime handoff clarification instead of inventing route discovery, polling, adapter changes, private endpoint, account-state, order, execution automation, or live-trading scope.

RX-043 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-044 — Product Owner Concrete Public Runtime Handoff Clarification

After RX-043 reviewer acceptance, RX-044 should inspect the accepted RX-043 conclusion, current source-of-truth docs, and any explicit Product Owner clarification supplied through Control Tower for exactly one concrete safe public/read-only/non-trading runtime handoff.

RX-044 implementation notes:

- Treat RX-044 as governance/source-of-truth only unless explicit Product Owner clarification clearly identifies one concrete safe public/read-only/non-trading runtime task.
- If one concrete safe runtime task is clearly grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If Product Owner clarification is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve RX-041 as the latest accepted product baseline unless a later reviewer-accepted product task exists.
- Preserve RX-043 as pending or accepted according to explicit reviewer evidence.

RX-044 accepted outcome:

- RX-043 is reviewer-accepted and finalized on `main`; RX-041 remains the latest accepted product baseline.
- Product Owner clarification supplied through Control Tower selects option A, Manual One-Route Public Readiness Report.
- Option A clearly grounds exactly one later safe public/read-only/non-trading runtime reporting task when constrained to one explicitly supplied route, existing public read-only RiseX and Hyperliquid adapters, the existing one-route adapter handoff, the existing route snapshot assembly and evaluation paths, existing source-aware public fee/funding completion, and fail-closed unknown handling.
- RX-044 records the clarification and prepares RX-045 as that one next handoff. RX-044 itself remains docs/governance-only and does not implement report behavior, product/runtime behavior, adapter changes, private/account endpoint access, credentials, account state, orders, sendable exchange requests, execution automation, or live trading.

RX-044 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, private endpoints, credentials, account balances/state, orders, sendable exchange request or order payload construction, execution automation, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, execution planning, guarded live runner execution, approval-boundary execution, live trading by default, route statuses, reject reasons, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-045 — Manual One-Route Public Readiness Report

After RX-044 reviewer acceptance, RX-045 should add one manual, one-route, public/read-only, non-trading readiness report for an explicitly supplied RiseX plus Hyperliquid route.

RX-045 implementation notes:

- Expand the existing one-route CLI/reporting surface so an operator can request a deterministic public readiness report for one explicitly supplied route.
- Preserve existing input requirements from the manual one-route real-data CLI: route id, capture id, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, positive finite target notional, evaluation mode, and timezone-aware assembly timestamp.
- Use the existing read-only public RiseX and Hyperliquid adapters, existing one-route adapter handoff, existing `assemble_route_snapshot()` path, existing source-aware public fee/funding completion, and existing `evaluate_route(route, snapshot, mode)` path.
- Report which public funding, fee, and economics evidence was applied, which components remain `UNKNOWN`, the existing decision status/reasons, existing Entry EV fields, and a report-only explanation of why the route is or is not ready for later fail-closed live-readiness stages.
- Keep the readiness conclusion display-only. It must not add or mutate route statuses, reject reasons, route eligibility, Capture state, ledger state, live gates, or execution state.

RX-045 must not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters or adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

RX-045 accepted outcome:

- Adds `run_real_data_research_route_with_snapshot()` in `apps/research_runner/real_data.py` as an app-layer reporting helper that returns the existing decision plus the existing assembled snapshot, or no snapshot on the existing fail-closed adapter/handoff failure path.
- Preserves `run_real_data_research_route()` behavior by delegating to the helper and returning only the decision.
- Adds `--public-readiness-report` to the existing `real-data-route` CLI command while preserving no-argument fake CLI behavior and default `real-data-route` output.
- Reports route identity, decision status/reasons, Entry EV fields, source-aware funding and fee values/metadata from the retained snapshot, deterministic `UNKNOWN` components, and a display-only public-readiness conclusion.
- RX-045 is reviewer-accepted and finalized on `main`; it remains manual, one-route, public/read-only, non-trading, and reporting-only.

## RX-046 — Post-RX-045 Public Live-Readiness Handoff Clarification

After RX-045 reviewer acceptance, RX-046 should inspect the accepted RX-045 public readiness report outcome and source-of-truth docs to identify exactly one next non-dangerous public/read-only/non-trading live-readiness handoff if one is clearly grounded.

RX-046 implementation notes:

- Treat RX-046 as governance/source-of-truth only unless one concrete safe later task is clearly grounded in accepted docs and does not reach hard-stop scope.
- If a concrete safe next public/read-only/non-trading task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If no such task is grounded, record the no-grounded-runtime-handoff conclusion and prepare a narrow clarification handoff rather than inventing route discovery, polling, private endpoint, account-state, order, execution automation, or live-trading scope.
- Preserve RX-045 as the latest accepted product baseline.
- Preserve RX-044 as the latest accepted governance/source-of-truth task unless a later reviewer-accepted governance task exists.

RX-046 accepted outcome:

- RX-045 is reviewer-accepted and finalized on `main`; it remains the latest accepted product baseline.
- RX-046 is reviewer-accepted and finalized on `main`; it is the latest accepted governance/source-of-truth task.
- The accepted RX-045 report outcome and current source-of-truth docs do not clearly ground one concrete safe public/read-only/non-trading runtime handoff after RX-045.
- RX-046 therefore records the no-grounded-runtime-handoff conclusion and prepares RX-047 as one narrow Product Owner direction gate instead of inventing route discovery, polling, adapter endpoint changes, private/account endpoint work, credentials, account state, orders, sendable request construction, execution automation, or live trading.
- RX-046 is governance/source-of-truth only and changes no product/runtime behavior.

RX-046 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-047 — Product Owner Post-RX-045 Public Runtime Direction Gate

After RX-046 reviewer acceptance, RX-047 should record explicit Product Owner direction, supplied through Control Tower or source-of-truth docs, for exactly one next non-dangerous public/read-only/non-trading live-readiness handoff after the accepted RX-045 manual public readiness report.

RX-047 implementation notes:

- Treat RX-047 as governance/source-of-truth only.
- If explicit Product Owner direction clearly identifies one concrete safe public/read-only/non-trading runtime task, prepare exactly that one later task in `NEXT_TASK.md`.
- If Product Owner direction is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve RX-045 as the latest accepted product baseline unless a later reviewer-accepted product task exists.
- Preserve RX-046 as pending or accepted according to explicit reviewer evidence.

RX-047 accepted outcome:

- RX-046 is reviewer-accepted and finalized on `main`; RX-045 remains the latest accepted product baseline.
- Product Owner and Control Tower direction for RX-047 confirms the long-term goal of live-capable hedged funding capture/trading on RiseX with Hyperliquid hedge support while preserving all hard-stop gates.
- The supplied direction identifies exactly one concrete safe later handoff: RX-048, an opt-in structured JSON stdout output for the existing RX-045 manual one-route public readiness report.
- RX-048 is safe and source-grounded only when scoped to one manually supplied explicit RiseX plus Hyperliquid route, existing public/read-only adapters, the existing one-route adapter handoff, retained snapshot/report helper, source-aware fee/funding completion, and `evaluate_route(route, snapshot, mode)`.
- RX-047 remains governance/source-of-truth only and changes no product/runtime behavior.

RX-047 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-048 — Structured JSON Stdout Public Readiness Report Output

After RX-047 finalization, RX-048 should add one opt-in structured JSON stdout output mode for the existing RX-045 manual public readiness report on the existing `real-data-route` command.

RX-048 implementation notes:

- Add an explicit opt-in JSON stdout mode for one manually supplied RiseX plus Hyperliquid route while preserving the existing default one-decision CLI output and existing `--public-readiness-report` text output.
- Produce JSON only when `--public-readiness-report --public-readiness-report-format json` are both supplied. `--public-readiness-report-format json` without the public-readiness report flag must fail before adapter construction instead of silently changing ordinary one-decision output.
- Reuse the existing public read-only `RiseXObservationAdapter` and `HyperliquidObservationAdapter`, existing one-route adapter handoff, existing retained snapshot/report helper, existing source-aware public fee/funding completion, and existing `evaluate_route(route, snapshot, mode)` path.
- Serialize only existing report evidence already available to the RX-045 report: route identity, decision status/reasons, Entry EV fields, source-aware public funding and fee evidence, deterministic `UNKNOWN` components, and display-only public-readiness conclusion.
- Preserve unknown values as unknown/null with their sources or metadata, never as zero or success.
- Emit JSON to stdout only. Do not write files, ledgers, storage records, migrations, or replay evidence.

RX-048 branch outcome:

- Adds `--public-readiness-report-format {text,json}` to the existing `real-data-route` command, defaulting to the existing text report behavior when the format flag is omitted.
- Requires the existing `--public-readiness-report` flag before JSON report output can be selected; a standalone JSON format selector fails before adapter construction.
- Serializes the accepted RX-045 report evidence to stdout only: route identity, decision status/reasons, Entry EV fields, retained snapshot funding and fee evidence, deterministic unknown components, display-only public-readiness conclusion, and later fail-closed blockers.
- Preserves unknown fee, funding, snapshot, and Entry EV values as `null` or `UNKNOWN` with metadata rather than zero or success.
- RX-048 remains one-route, public/read-only, non-trading, and formatting-only after reviewer acceptance and finalization.

RX-048 must not add route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters or adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-049 — Post-RX-048 Public Live-Readiness Handoff Clarification

After RX-048 reviewer acceptance, RX-049 should inspect the accepted RX-048 structured JSON stdout report outcome and source-of-truth docs to identify exactly one next non-dangerous public/read-only/non-trading live-readiness handoff if one is clearly grounded.

RX-049 implementation notes:

- Treat RX-049 as governance/source-of-truth only unless one concrete safe later task is clearly grounded in accepted docs and does not reach hard-stop scope.
- If a concrete safe next public/read-only/non-trading task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If no such task is grounded, record the no-grounded-runtime-handoff conclusion and prepare a narrow clarification handoff rather than inventing route discovery, polling, private endpoint, account-state, order, execution automation, or live-trading scope.
- Preserve RX-048 as the latest accepted product/reporting baseline.
- Preserve RX-047 as the latest accepted governance/source-of-truth task unless a later reviewer-accepted governance task exists.

RX-049 branch outcome:

- RX-048 is reviewer-accepted and finalized on `main`; it is the latest accepted product/reporting task.
- RX-049 is reviewer-accepted and finalized on `main`; it is the latest accepted governance/source-of-truth task.
- The accepted RX-048 structured JSON stdout public readiness report outcome and current source-of-truth docs do not clearly ground one concrete safe post-RX-048 public/read-only/non-trading runtime handoff.
- RX-049 therefore records the no-grounded-runtime-handoff conclusion and prepares RX-050 as one narrow Product Owner direction gate instead of inventing route discovery, ranking, polling, adapter endpoint changes, private/account endpoint work, credentials, account state, orders, sendable request construction, execution automation, execution planning, ledger/storage/replay changes, or live trading.
- RX-049 remains governance/source-of-truth only after reviewer acceptance and finalization and changes no product/runtime behavior.

RX-049 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-050 — Product Owner Post-RX-048 Public Runtime Direction Gate

After RX-049 reviewer acceptance, RX-050 should record explicit Product Owner direction, supplied through Control Tower or source-of-truth docs, for exactly one next non-dangerous public/read-only/non-trading live-readiness handoff after the accepted RX-048 structured JSON stdout public readiness report.

RX-050 implementation notes:

- Treat RX-050 as governance/source-of-truth only.
- If explicit Product Owner direction clearly identifies one concrete safe public/read-only/non-trading runtime task, prepare exactly that one later task in `NEXT_TASK.md`.
- If Product Owner direction is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve RX-048 as the latest accepted product/reporting baseline unless a later reviewer-accepted product task exists.
- Preserve RX-049 as pending or accepted according to explicit reviewer evidence.

RX-050 branch outcome:

- RX-049 is reviewer-accepted and finalized on `main`; RX-048 remains the latest accepted product/reporting baseline.
- Product Owner/Control Tower direction for RX-050 confirms the long-term goal of live-capable hedged funding capture/trading on RiseX with Hyperliquid hedge support while preserving all hard-stop gates.
- The supplied direction remains broad product direction only. It does not authorize live trading, private/account endpoints, credentials, account balances/state, orders, sendable exchange requests, execution automation, execution planning, destructive actions, unsafe scope, or financially dangerous actions.
- The docs plus explicit Product Owner/Control Tower direction still do not clearly identify one concrete safe public/read-only/non-trading runtime handoff after RX-048.
- RX-050 therefore records the no-clarified-runtime-handoff conclusion and prepares RX-051 as one narrow concrete clarification handoff instead of inventing route discovery, ranking, polling, adapter endpoint changes, private/account endpoint work, credentials, account state, orders, sendable request construction, execution automation, execution planning, ledger/storage/replay changes, or live-trading scope.
- RX-050 remains governance/source-of-truth only after reviewer acceptance and finalization and changes no product/runtime behavior.

RX-050 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-051 — Repository Instruction Hygiene And Stale Cross-Project Reference Audit

After RX-050 reviewer acceptance and explicit Control Tower direction, RX-051 audits the RiseX repository source-of-truth docs and tracked files for stale cross-project workflow instructions or references.

RX-051 implementation notes:

- Treat RX-051 as governance/source-of-truth hygiene only.
- Search tracked and hidden non-.git repository files for stale cross-project workflow references.
- If stale tracked historical wording is present, reword it to generic RiseX-safe language.
- Verify that there is no repo-local `.codex` instruction directory.
- Verify that there are no tracked cross-project instruction files and no tracked stale generated artifacts.
- Document ignored/generated local artifacts as cleanup candidates only; do not commit generated artifact deletion.
- Preserve RX-048 as the latest accepted product/reporting baseline and RX-050 as the latest accepted governance/source-of-truth baseline.
- Prepare exactly one next non-dangerous handoff in `NEXT_TASK.md`.

RX-051 accepted outcome:

- The audit found one historical stale literal cross-project workflow name in `STATUS.md` and reworded it to generic RiseX-safe language.
- The audit found no repo-local `.codex` instruction directory.
- The audit found no tracked cross-project instruction files; the only tracked instruction file found by filename audit was the RiseX `AGENTS.md`.
- The audit found no tracked stale generated artifacts.
- Ignored/generated local artifacts remain cleanup candidates only and were not deleted or committed by RX-051.
- RX-051 prepares RX-052 as one narrow Product Owner/Control Tower concrete public runtime handoff clarification rather than inventing runtime scope.

RX-051 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-052 — Product Owner Concrete Post-RX-048 Public Runtime Handoff Clarification

After RX-051 reviewer acceptance, RX-052 should inspect the accepted RX-051 repository instruction hygiene outcome, the accepted RX-050 conclusion, current source-of-truth docs, and any explicit Product Owner or Control Tower clarification supplied for exactly one concrete safe public/read-only/non-trading runtime handoff after RX-048.

RX-052 implementation notes:

- Treat RX-052 as governance/source-of-truth only. Explicit clarification may select one later task, but RX-052 must not implement runtime behavior.
- If one concrete safe runtime task is clearly grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If clarification is absent, ambiguous, unsafe, or reaches a hard-stop category, record that no clarified runtime handoff is available and do not invent product/runtime scope.
- Preserve RX-048 as the latest accepted product/reporting baseline unless a later reviewer-accepted product task exists.
- Preserve RX-051 as reviewer-accepted and finalized on `main`.

RX-052 branch outcome:

- RX-051 is reviewer-accepted and finalized on `main`; RX-048 remains the latest accepted product/reporting baseline and RX-051 remains the latest accepted governance/source-of-truth baseline.
- Product Owner clarification supplied through Control Tower directs continued autonomous work toward a working fake-money paper trader system before any live trading work is considered.
- The clarification clearly grounds one concrete next non-dangerous runtime handoff when scoped as a manual fake-money bridge from one existing public one-route real-data ENTRY decision into the existing fake paper lifecycle and append-only ledger.
- RX-052 prepares RX-053 Manual One-Route Public Paper Trader Bridge as exactly one next task in `NEXT_TASK.md`.
- RX-052 remains governance/source-of-truth only and changes no product/runtime behavior.

RX-052 must not add product/runtime behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, automatic refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

## RX-053 — Manual One-Route Public Paper Trader Bridge

After RX-052 reviewer acceptance and finalization, RX-053 should add one explicit manual operator command or app-layer runner that connects one existing public one-route real-data ENTRY decision to the existing fake paper lifecycle and append-only ledger.

RX-053 implementation notes:

- The bridge must consume one explicitly supplied RiseX plus Hyperliquid route using the existing manual public route input requirements and read-only public adapter construction boundaries.
- The public decision must flow through the existing one-route real-data runner and the single `evaluate_route(route, snapshot, mode)` path in `EvaluationMode.ENTRY`; RX-053 must not add a second decision, snapshot, EV, VWAP, fee, funding, or route model path.
- The bridge must delegate fake paper execution to the existing `run_paper_lifecycle()` behavior in `apps/paper_runner/lifecycle.py`.
- Fake paper ledger writes must occur only through `core/accounting/ledger.py`. If RX-053 adds optional explicit local persistence, it must use the existing `storage/sqlite/ledger.py` contract and an explicit operator-supplied local SQLite path.
- The bridge must print a deterministic stdout summary covering route id, mode, decision status/reasons, whether fake paper started, paper start blockers if any, ledger event count/sequences/types, and any existing PnL explanation values without recalculating profitability.
- Focused tests must cover a started fake paper case, a non-started decision case, explicit local SQLite path behavior if implemented, malformed CLI/operator input fail-closed before adapter construction, preservation of unknown economics as missing rather than zero, and no live/order/private/account-state behavior.

RX-053 must not add live trading, real exchange order placement, order cancellation, order status fetching, private/account endpoints, credentials, API keys, exchange account state, account balances, account-tier assumptions, sendable exchange request construction, order payload construction, automatic polling, background loops, scheduling, alerts, auto-refresh, route discovery, route ranking, watchlists, execution automation, execution planning, guarded live runner execution, approval-boundary execution, funding settlement verification changes, ledger reconciliation changes, replay changes, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, unknown-to-zero behavior, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot assembly path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

RX-053 branch outcome:

- Adds one explicit `paper-trade-route` command for one manually supplied RiseX plus Hyperliquid public route.
- Requires `--mode ENTRY`; discovery mode is rejected before adapter construction.
- Validates route id, capture id, exact RiseX and Hyperliquid venues, symbols, opposing entry sides, positive finite target notional, and timezone-aware assembly timestamp before constructing adapters.
- Reuses `run_real_data_research_route_with_snapshot()` and therefore the existing one-route adapter handoff plus the single `evaluate_route(route, snapshot, mode)` decision path.
- Delegates fake paper behavior to `run_paper_lifecycle()` when a public snapshot is available. Started decisions write route-decision/open/settlement/close events; non-started decisions with a snapshot write the existing route-decision plus paper-rejection events.
- Keeps fake paper ledger writes inside `core/accounting/ledger.py` and supports optional explicit local persistence only through `storage/sqlite/ledger.py` via `--ledger-sqlite-path`.
- Prints deterministic stdout covering route id, capture id, decision mode/status/reasons, decision net profit, snapshot availability, funding settlement timestamp when available, fake paper started state, paper start blockers, ledger event count/sequences/types, and paper PnL explanation values.
- Preserves missing snapshot, Entry EV, funding, fee, and net-profit values as `None`/unknown rather than zero, success, or profitability.
- Preserves existing no-argument fake CLI behavior, existing `real-data-route` default output, existing public-readiness text output, and existing public-readiness JSON output unless the new bridge command is explicitly invoked.
- Does not add live trading, orders, private/account endpoints, credentials, account state, sendable requests, order payloads, execution planning, route discovery/ranking/polling/watchlists, new route statuses/reject reasons, ledger reconciliation/replay changes, economics changes, route eligibility mutation, Capture transition changes, or second owner paths.

## RX-054 — Post-Manual Paper Bridge Handoff Clarification

After RX-053 reviewer acceptance and finalization, RX-054 should inspect the accepted manual paper bridge outcome and current source-of-truth docs to identify exactly one next non-dangerous fake-money paper-trader handoff if one is clearly grounded.

RX-054 implementation notes:

- Treat RX-054 as governance/source-of-truth only.
- If one concrete safe next fake-money paper-trader task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If no such task is grounded, record the no-grounded-handoff conclusion and prepare one narrow Product Owner clarification gate rather than inventing route discovery, ranking, polling, execution automation, live trading, order placement, private/account endpoint, credential, account-state, ledger replay, reconciliation, or storage-migration scope.
- Preserve RX-053 as pending or accepted according to explicit reviewer evidence.

RX-054 must not add product/runtime behavior, CLI output behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, auto-refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

RX-054 branch outcome:

- RX-053 is reviewer-accepted and finalized on `main`; RX-053 remains the latest accepted product/runtime baseline.
- Product Owner clarification supplied through Control Tower directs continued work beyond the one-route manual bridge toward a full fake-money paper trader system for serial strategy testing.
- Telegram is recorded as later interface direction only. RX-054 does not authorize Telegram bot tokens, credentials, external Telegram network transport, webhooks, alerts, messaging behavior, live trading, real orders, private/account endpoints, account state, sendable exchange requests, order payloads, execution automation, execution planning, guarded live runner execution, approval-boundary execution, or financially dangerous actions.
- The accepted RX-053 bridge plus RX-052 paper-trader clarification ground one next non-dangerous runtime handoff when scoped as a manual, explicitly invoked serial paper session runner for a finite operator-supplied list of explicit routes.
- RX-054 prepares RX-055 Manual Serial Paper Session Runner as exactly one next task in `NEXT_TASK.md`.
- RX-054 remains governance/source-of-truth only and changes no product/runtime behavior.

## RX-055 — Manual Serial Paper Session Runner

After RX-054 reviewer acceptance and finalization, RX-055 should add one manual, explicitly invoked serial fake-money paper testing runner or command for a finite operator-supplied list of explicit RiseX plus Hyperliquid routes.

RX-055 implementation notes:

- The runner must consume only a finite operator-supplied list of explicit routes, capped at 25 routes as an operator input safety bound. It must not discover, rank, truncate, skip, auto-batch, watchlist, poll, schedule, alert, loop in the background, silently accept partial lists, or auto-refresh routes.
- Each route must reuse the existing manual public route input requirements and public read-only adapter construction boundaries.
- Each route decision must flow through `run_real_data_research_route_with_snapshot()` and the single shared `evaluate_route(route, snapshot, mode)` path in `EvaluationMode.ENTRY`.
- Fake paper behavior must delegate to `run_paper_lifecycle()` when a public snapshot is available.
- Fake paper ledger writes must stay inside `core/accounting/ledger.py`; optional local persistence must use only the existing `storage/sqlite/ledger.py` contract through an explicit operator-supplied local SQLite path.
- The runner must print deterministic per-route and session-level summary stdout for strategy testing.
- Missing public snapshot, Entry EV, funding, fee, decision net profit, or paper PnL values must remain `None`/unknown in route output and session summaries; count-only known/unknown fields must cover Entry EV, paper expected funding, paper total fees, decision net profit, and paper net profit, and aggregates must not turn unknown values into zero, success, or profitability.
- Telegram remains out of scope. Bot-ready command parsing may be a later non-network task; actual Telegram transport, bot tokens, credentials, webhooks, external network behavior, alerts, and messaging require an explicit future credentials/network gate.
- Focused tests must cover started and non-started routes, deterministic session summary output, finite explicit route list handling, optional SQLite behavior if implemented, malformed input failing before adapter construction, unknown-as-missing preservation, and absence of live/order/private/account/Telegram behavior.

RX-055 must not add live trading, real exchange order placement, order cancellation, order status fetching, private/account endpoints, credentials, API keys, Telegram bot tokens, Telegram transport, external Telegram network calls, webhooks, alerts, messaging behavior, exchange account state, account balances, account-tier assumptions, sendable exchange request construction, order payload construction, automatic polling, background loops, scheduling, auto-refresh, route discovery, route ranking, watchlists, execution automation, execution planning, guarded live runner execution, approval-boundary execution, funding settlement verification changes, ledger reconciliation changes, replay changes, storage migrations, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, unknown-to-zero behavior, artificial filters, canary architecture, hold-next-cycle logic, or any second route model, decision path, snapshot assembly path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

RX-055 branch outcome:

- Adds one explicit `paper-trade-session` command for one operator-supplied local JSON route-list file.
- The route-list schema is a non-empty finite JSON array of at most 25 exact route objects only. Missing, empty, over-limit, malformed, extra-field, discovery-style, ranking-style, watchlist-style, polling-style, non-ENTRY, wrong-venue, same-side, non-finite-notional, or timezone-naive inputs fail before adapter construction.
- Each route reuses `RouteCandidate`, `run_real_data_research_route_with_snapshot()`, and the shared `evaluate_route(route, snapshot, mode)` path in `EvaluationMode.ENTRY`.
- Each route delegates fake paper handling to `run_paper_lifecycle()` when a public snapshot is available. Missing snapshots remain `UNKNOWN`, do not invent funding settlement timestamps, and do not write paper lifecycle events.
- The command uses `InMemoryLedger` by default and optional explicit local `SQLiteLedger` persistence only through `--ledger-sqlite-path`.
- Per-route output remains deterministic and copies existing decision and paper lifecycle values. Session summary output reports counts, Entry EV known/unknown, paper expected funding known/unknown, paper total fees known/unknown, decision net profit known/unknown, paper net profit known/unknown, ledger event sequences/types, and `aggregate_paper_net_profit_usd=None` rather than aggregating PnL.
- Existing no-argument fake CLI behavior, `real-data-route`, public-readiness text/JSON output, and `paper-trade-route` behavior are preserved unless `paper-trade-session` is explicitly invoked.
- RX-055 does not add Telegram behavior, live trading, orders, private/account endpoints, credentials, account state, sendable requests, order payloads, execution planning, discovery/ranking/polling/watchlists, new route statuses/reject reasons, economics changes, ledger reconciliation/replay changes, storage migrations, route eligibility mutation, Capture transition changes, or second owner paths.

## RX-056 — Post-Serial Paper Session Handoff Clarification

After RX-055 reviewer acceptance and finalization, RX-056 should inspect the accepted manual serial paper session outcome and current source-of-truth docs to identify exactly one next non-dangerous fake-money paper-trader handoff if one is clearly grounded.

RX-056 implementation notes:

- Treat RX-056 as governance/source-of-truth only.
- Preserve RX-055 as pending or accepted according to explicit reviewer evidence.
- Record that the accepted RX-055 outcome plus Product Owner and Control Tower direction ground exactly one next safe fake-money paper-trader task.
- Prepare exactly that one later task in `NEXT_TASK.md`: manual local JSON report/history export for `paper-trade-session` results, with explicit local output paths and existing session outcomes or paper ledger events only.
- Keep Telegram transport, credentials, discovery, ranking, polling, execution automation, live trading, order placement, private/account endpoint, account-state, ledger replay, reconciliation, storage migration, second owner paths, and unknown-to-zero behavior out of the handoff.

RX-056 must not add product/runtime behavior, CLI output behavior, route discovery, ranking, watchlists, background loops, polling, scheduling, alerts, auto-refresh, adapters, adapter endpoint changes, private/account endpoints, credentials, API keys, Telegram bot tokens, Telegram transport, webhooks, external Telegram network calls, messaging behavior, account balances/state, account-tier assumptions, order placement, order cancellation, order status fetching, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, storage migrations, replay changes, paper lifecycle changes, funding settlement verification, ledger reconciliation, route eligibility mutation, Capture state transitions, route statuses, reject reasons, fee/funding/VWAP/liquidity/basis/spread/price-impact/slippage/max-level/hidden-buffer/safety-margin rule changes, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot path, EV path, VWAP path, ledger-write path, replay path, execution-planning path, or live execution path.

RX-056 branch outcome:

- RX-055 is reviewer-accepted and finalized on `main`; it remains the latest accepted product/runtime baseline.
- RX-056 inspected the accepted RX-055 serial session outcome, current source-of-truth docs, Product Owner direction to continue toward fake-money paper strategy testing before live trading, and Control Tower review direction after the initial conservative RX-056 branch conclusion.
- The docs and direction clearly ground the accepted manual serial `paper-trade-session` command, the 25-route cap, deterministic per-route/session stdout, count-only known/unknown summary fields, optional explicit local SQLite ledger persistence, Telegram as later interface direction only, and the need for one local deterministic report/history artifact layer before later Telegram command/display adaptation.
- RX-056 prepares RX-057 Manual Paper Session Report History Export as exactly one next product/runtime handoff.
- RX-056 remains governance/source-of-truth only and changes no product/runtime behavior.

## RX-057 — Manual Paper Session Report History Export

After RX-056 reviewer acceptance and finalization, RX-057 should add an explicit, manually invoked local JSON report/history export for `paper-trade-session` session results.

RX-057 implementation notes:

- The export must be manually invoked and require explicit local output paths. It must not write report/history artifacts unless the operator supplies the output path.
- The export may use only existing `paper-trade-session` route inputs, session outcomes, and paper ledger events already produced through RX-055 owner paths. It must not add route discovery, route ranking, watchlists, polling, background loops, scheduling, alerts, automatic refresh, or any second session runner.
- The JSON schema must be deterministic and suitable for later Telegram command/display adapter consumption, but RX-057 must not add Telegram transport, bot tokens, webhooks, alerts, messaging, credentials, or external network calls.
- The export must preserve the RX-055 route-list cap of 25 exact explicit ENTRY routes and must preserve known/unknown/null semantics for Entry EV, paper expected funding, paper total fees, decision net profit, and paper net profit. Unknown values must remain unknown/null, and aggregate paper PnL must remain absent or explicit `None` rather than inferred.
- The implementation must reuse existing decision, snapshot, economics, fake paper lifecycle, and ledger ownership. It must not add a second route model, decision path, snapshot path, EV path, VWAP path, fee/funding path, paper lifecycle path, ledger-write path, replay path, reconciliation path, execution-planning path, or live execution path.
- Focused tests must cover deterministic JSON report/history output, explicit output path behavior, preservation of RX-055 count-only known/unknown summary fields, unknown/null preservation without zero conversion, no aggregate PnL invention, no output write when the flag/path is absent, and no Telegram/live/order/private/account/discovery/polling behavior.

RX-057 must not add live trading, real exchange order placement, order cancellation, order status fetching, private/account endpoints, credentials, API keys, Telegram bot tokens, Telegram transport, webhooks, external Telegram network calls, alerts, messaging behavior, exchange account state, account balances, account-tier assumptions, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, automatic polling, background loops, scheduling, auto-refresh, route discovery, route ranking, watchlists, storage migrations, replay changes, ledger reconciliation changes, funding settlement verification changes, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, unknown-to-zero behavior, aggregate PnL invention, artificial filters, canary architecture, hold-next-cycle logic, live trading by default, or any second route model, decision path, snapshot assembly path, EV path, VWAP path, fee/funding path, paper lifecycle path, ledger-write path, replay path, reconciliation path, execution-planning path, or live execution path.

RX-057 branch outcome:

- Adds one optional `--session-report-json-path` flag to the existing `paper-trade-session` command.
- Writes no report/history artifact unless the operator supplies that explicit local path.
- Builds the deterministic JSON payload from validated route inputs, already-retained decisions/snapshots, paper lifecycle outcomes, and paper ledger events produced by the existing session run.
- Preserves the RX-055 25-route explicit ENTRY cap, existing stdout behavior, count-only known/unknown summary fields, unknown/null values, and explicit `aggregate_paper_net_profit_usd=null`.
- Does not add Telegram transport, tokens, credentials, network calls, messaging, alerts, webhooks, discovery, ranking, watchlists, polling, background loops, scheduling, execution automation, live/order/private/account scope, replay, reconciliation, storage migrations, new statuses/reasons, or second owner paths.

## RX-058 — Local Paper Session Command Payload Parser Fixtures

After RX-057 reviewer acceptance and finalization, RX-058 should add a local-only parser/fixture layer for paper session command payloads suitable for later Telegram command/display adaptation.

RX-058 implementation notes:

- The parser must be local-only and deterministic. It may convert caller-supplied text or JSON-like payload fixtures into the existing `paper-trade-session` route-list input shape, but it must not invoke Telegram transport, bot tokens, webhooks, external network calls, alerts, messaging behavior, credentials, or API keys.
- It must preserve the existing `paper-trade-session` 25-route explicit ENTRY cap by delegating to or matching the accepted route-list validation boundary before adapter construction.
- It must not run sessions, call adapters, write ledgers, write report artifacts, discover/rank routes, poll, schedule, create watchlists, replay or reconcile ledgers, plan execution, place orders, use private/account endpoints, read account state, mutate route eligibility, add statuses/reasons, or add second owner paths.
- Focused tests must cover accepted fixture parsing, malformed payload rejection before adapter/session construction, no network/Telegram/live/order/private/account scope, preservation of explicit ENTRY route fields, and no weakening of RX-055/RX-057 validation or unknown/null semantics.

RX-058 must not add Telegram transport, Telegram bot tokens, webhooks, external Telegram network calls, alerts, messaging behavior, credentials, API keys, live trading, order placement/cancel/status behavior, private/account endpoints, account state, account balances, sendable exchange requests, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, route discovery, ranking, watchlists, polling, background loops, scheduling, auto-refresh, adapter endpoint changes, fee/funding/VWAP/liquidity/basis/economics rule changes, funding settlement verification changes, ledger reconciliation changes, replay changes, storage migrations, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, canary architecture, hold-next-cycle logic, unknown-to-zero behavior, aggregate PnL invention, or second route/session/decision/snapshot/economics/paper lifecycle/ledger-write/replay/reconciliation/execution/live paths.

RX-058 branch outcome:

- Adds `apps/cli/paper_session_payloads.py` as a local-only parser/fixture helper for explicit paper session command payloads.
- Moves the accepted paper session route-list validation boundary into that helper and keeps `paper-trade-session --routes-json-path` using the same boundary.
- `paper_session_route_list_from_command_payload()` accepts an explicit local JSON route array or an object with exactly `routes`, validates it through the existing finite route-list rules, and returns the same exact route-list dictionaries accepted by `--routes-json-path`.
- Preserves the RX-055 cap of 25 exact explicit ENTRY routes, exact field validation, required RiseX/Hyperliquid venues, opposing entry sides, positive finite string notional, and timezone-aware `assembled_at`.
- Parser output contains no decision, economics, paper, summary, ledger, report, aggregate PnL, or unknown-to-zero fields.
- The parser does not run sessions, construct adapters, write ledgers, write report artifacts, send messages, call networks, add credentials, discover/rank/watchlist/poll/schedule, automate execution, change economics, mutate eligibility, add statuses/reasons, or create second owner paths.
- RX-058 is reviewer-accepted and finalized on `main`.

## RX-059 — Post-Local Paper Session Payload Parser Handoff Clarification

After RX-058 reviewer acceptance and finalization, RX-059 should inspect the accepted local paper session command payload parser outcome and current source-of-truth docs to identify exactly one next non-dangerous fake-money paper-trader handoff if one is clearly grounded.

RX-059 implementation notes:

- Treat RX-059 as governance/source-of-truth only.
- Preserve RX-058 as pending or accepted according to explicit reviewer evidence.
- If one concrete safe next fake-money paper-trader task is grounded, prepare exactly that one later task in `NEXT_TASK.md`.
- If no such task is grounded, record the no-grounded-handoff conclusion and prepare one narrow Product Owner clarification gate rather than inventing Telegram transport, credentials, discovery, ranking, polling, execution automation, live trading, order placement, private/account endpoint, account-state, ledger replay, reconciliation, storage-migration, or second-owner-path scope.
- Keep `NEXT_TASK.md` to exactly one task and preserve reviewer-only acceptance.

RX-059 must not add product/runtime behavior, CLI output behavior, Telegram transport, Telegram bot tokens, webhooks, external network calls, alerts, messaging behavior, credentials, API keys, live trading, real exchange order placement, order cancellation, order status fetching, private/account endpoints, account state, account balances, sendable exchange request construction, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, route discovery, ranking, watchlists, polling, background loops, scheduling, auto-refresh, adapter endpoint changes, fee/funding/VWAP/liquidity/basis/economics rule changes, funding settlement verification changes, ledger reconciliation changes, replay changes, storage migrations, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, canary architecture, hold-next-cycle logic, unknown-to-zero behavior, aggregate PnL invention, or second route/session/decision/snapshot/economics/paper lifecycle/ledger-write/replay/reconciliation/execution/live paths.

RX-059 branch outcome:

- RX-058 is reviewer-accepted and finalized on `main`; it remains the latest accepted product/runtime baseline.
- RX-059 inspected the accepted RX-058 parser outcome, current source-of-truth docs, the accepted RX-055 through RX-057 fake-money paper testing trail, the required supervised worker design checkpoint, and latest explicit Product Owner direction supplied through Control Tower.
- The accepted trail plus Product Owner direction clearly ground exactly one next concrete safe local/manual/fake-money testing-support handoff after RX-058: a local operator-package/preview builder that consumes the RX-058 parser/validation boundary and prepares deterministic local artifacts for manual serial paper-session testing and later Telegram display adaptation.
- RX-059 prepares RX-060 Local Paper Session Operator Package Builder as exactly one next product/runtime testing-support handoff.
- RX-059 remains governance/source-of-truth only and changes no product/runtime behavior.

## RX-060 — Local Paper Session Operator Package Builder

After RX-059 reviewer acceptance and finalization, RX-060 should add one local-only, manually invoked operator-package/preview builder for serial fake-money paper sessions.

RX-060 implementation notes:

- The builder must consume explicit local command payload fixtures through the RX-058 parser/validation boundary.
- It must produce deterministic local operator artifacts for manual serial paper-trader testing and later Telegram display adaptation: a validated route-list JSON file and a preview/manifest JSON describing route count, route ids, intended local input/report paths, and the exact manual `paper-trade-session --routes-json-path ... --session-report-json-path ...` command plan.
- It must require explicit local output paths for every artifact written and validate the whole payload before writing any artifact.
- It must keep route-list output to the exact dictionary shape accepted by `paper-trade-session --routes-json-path`, preserving the RX-055 25-route ENTRY cap, exact fields, known/unknown behavior by omission, and no aggregate PnL.
- The preview/manifest is descriptive only. It must not contain credentials, secrets, bot tokens, private/account data, sendable exchange requests, order payloads, live execution material, realized session results, ledger events, report/history results, aggregate PnL, or invented economics.
- It must not execute the session, construct adapters, call `run_real_data_research_route()` or `run_real_data_research_route_with_snapshot()`, call `run_paper_lifecycle()`, instantiate ledgers, write ledger events, write session report/history results, send messages, call networks, or add Telegram transport.

RX-060 must not add Telegram transport, Telegram bot tokens, webhooks, external network calls, alerts, messaging behavior, credentials, API keys, live trading, order placement/cancel/status behavior, private/account endpoints, account state, account balances, account-tier assumptions, sendable exchange requests, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, route discovery, ranking, watchlists, polling, background loops, scheduling, auto-refresh, adapter endpoint changes, fee/funding/VWAP/liquidity/basis/economics rule changes, funding settlement verification changes, ledger reconciliation changes, replay changes, storage migrations, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, canary architecture, hold-next-cycle logic, unknown-to-zero behavior, aggregate PnL invention, or second route/session/decision/snapshot/economics/paper lifecycle/ledger-write/replay/reconciliation/execution/live paths.

RX-060 branch outcome:

- RX-060 adds `build-paper-session-package` in the CLI app layer.
- The command reads an explicit local command payload fixture path and validates the full payload through `paper_session_route_list_from_command_payload()` before writing any artifact.
- The route-list artifact contains only exact route-list dictionaries accepted by `paper-trade-session --routes-json-path`.
- The preview/manifest artifact is descriptive only: route count, route ids, route-list artifact path, intended session report path, and exact manual command plan.
- RX-060 does not run sessions, construct adapters, instantiate ledgers, write report/history results, write ledger events, call networks, add Telegram transport, add live/order/private/account behavior, discover/rank/poll, replay/reconcile ledgers, migrate storage, add statuses/reasons, invent aggregate PnL, or create second owner paths.
- RX-060 prepares RX-061 Local Paper Session Report Display Renderer as exactly one next product/runtime testing-support handoff pending reviewer acceptance.

## RX-061 — Local Paper Session Report Display Renderer

After RX-060 reviewer acceptance and finalization, RX-061 should add one local-only, manually invoked display/preview renderer for already-written RX-057 `paper-trade-session --session-report-json-path` JSON reports.

RX-061 implementation notes:

- The renderer must consume an explicit local session report JSON path.
- It may optionally consume an explicit local RX-060 operator package preview/manifest path only if report-only context is insufficient; keep the first implementation report-only if sufficient.
- It must produce deterministic local display output suitable for later Telegram display adaptation, either stdout only or stdout plus one explicit local display artifact.
- It may display route count, route ids, per-route decision and paper statuses already present in the report, known/unknown summary counts, string-or-null economics exactly as represented in the report, and `aggregate_paper_net_profit_usd` preserved as null/unknown.
- It must validate malformed report input before any optional display artifact write.
- It must not execute sessions, construct adapters, write ledger events, write or mutate session report/history results, send messages, call networks, add Telegram transport, or add live/order/private/account scope.
- It must not recompute decisions, paper outcomes, economics, summary counts, ledger events, or aggregate PnL.

RX-061 must not add Telegram transport, Telegram bot tokens, webhooks, external network calls, alerts, messaging behavior, credentials, API keys, live trading, order placement/cancel/status behavior, private/account endpoints, account state, account balances, account-tier assumptions, sendable exchange requests, order payload construction, execution automation, execution planning, guarded live runner execution, approval-boundary execution, route discovery, ranking, watchlists, polling, background loops, scheduling, auto-refresh, adapter endpoint changes, fee/funding/VWAP/liquidity/basis/economics rule changes, funding settlement verification changes, ledger reconciliation changes, replay changes, storage migrations, route eligibility mutation, Capture state transition changes, route statuses, reject reasons, canary architecture, hold-next-cycle logic, unknown-to-zero behavior, aggregate PnL invention/calculation, or second route/session/decision/snapshot/economics/paper lifecycle/ledger-write/report/replay/reconciliation/execution/live paths.

## Next Sequence

1. RX-061 Local Paper Session Report Display Renderer.

Do not promote execution automation, background loops, ranking, order placement, polling, alerts, auto-refresh, Telegram transport, bot tokens, private endpoints, credentials, account-state access, destructive reset, financially dangerous actions, or later roadmap stages into the current handoff unless that exact future task is explicitly user-approved for hard-stop scope or explicitly directed by the Product Owner, autonomously selected by Control Tower under RX-033 for non-dangerous scope, and passes the repository's hard approval gates.
