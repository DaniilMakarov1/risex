# Product Invariants

## Strategy

- Main strategy: hedged funding capture on RiseX with hedge venue support, initially Hyperliquid.
- One `Capture` equals one funding settlement opportunity.
- One shared decision pipeline evaluates routes.
- One append-only ledger records decisions and future execution/accounting events.

## Roadmap gates

- RX-008 through RX-016 are accepted fail-closed offline safety hardening, not a product strategy change.
- Offline safety scaffolding must not become an open-ended detour. Future work must return to the intended product path one `NEXT_TASK.md` handoff at a time.
- Future roadmap stages are gated and scoped. A roadmap mention is not permission to implement real adapters, network calls, execution planning, live runner behavior, monitoring/dashboard behavior, or order placement before an explicit task authorizes that exact stage.
- Product Owner clarification recorded by RX-052 sets the next product path as fake-money paper-trading readiness before any live-trading work is considered.
- Paper trader means fake paper lifecycle and append-only ledger behavior only. It is not live exchange execution, real order placement, private/account endpoint access, credential use, exchange account state, account balances, sendable exchange request construction, order payload construction, or any financially dangerous action.
- The manual public paper-trader bridge may connect only one existing public one-route real-data ENTRY decision to the existing fake paper lifecycle and existing append-only ledger. It must not add discovery, ranking, watchlists, polling, background loops, execution planning, guarded live runner execution, approval-boundary execution, new route statuses, new reject reasons, new decision/snapshot/EV paths, or unknown-to-zero behavior.
- Product Owner clarification recorded by RX-054 continues the fake-money paper-trader path toward serial strategy testing. A manual serial paper session runner may process only a finite operator-supplied list of explicit routes, one route at a time, through the existing public one-route ENTRY decision path and existing fake paper lifecycle plus ledger ownership.
- RX-056 records that the accepted RX-055 serial session outcome plus Product Owner and Control Tower direction clearly ground exactly one next fake-money paper-trader handoff: a manual local JSON report/history export for `paper-trade-session` results.
- RX-057 implements that handoff through an explicit local `--session-report-json-path` on `paper-trade-session`. No report/history artifact may be written when the operator does not supply the output path. The export may use existing route inputs, session outcomes, and paper ledger events only; it must preserve the 25-route explicit ENTRY cap, known/unknown/null semantics, count-only summary fields, no aggregate PnL, no Telegram transport, no network, no credentials, no discovery/ranking/polling/watchlists, no execution automation, no ledger replay/reconciliation or storage migration, and no live/order/private/account scope.
- RX-058 adds local paper session command payload parser fixtures only. The parser may normalize explicit local JSON payload fixtures into the existing `paper-trade-session` route-list shape, but it must delegate to the accepted 25-route explicit ENTRY validation boundary and must not run sessions, construct adapters, write ledgers, write report artifacts, send messages, call networks, add credentials, discover/rank/poll/watchlist, automate execution, or add live/order/private/account scope.
- RX-059 records explicit Product Owner direction grounding exactly one next fake-money paper-trader testing-support handoff after RX-058: a local-only, manually invoked operator-package/preview builder that consumes the RX-058 parser/validation boundary and writes deterministic local artifacts for manual serial paper-session testing and later Telegram display adaptation.
- RX-060 may write only explicit local package artifacts such as a validated route-list JSON file and a preview/manifest JSON with route count, route ids, intended local input/report paths, and the exact manual `paper-trade-session --routes-json-path ... --session-report-json-path ...` command plan. It must not execute sessions, construct adapters, write ledger events, write session report/history results, send messages, call networks, add Telegram transport, credentials, discovery/ranking/polling/watchlists, execution automation, live/order/private/account scope, replay/reconciliation/storage migration, new statuses/reasons, aggregate PnL, unknown-to-zero behavior, or second owner paths.
- RX-060 implements `build-paper-session-package` as a CLI-layer local artifact builder only. It must validate the entire command payload through the RX-058 parser before any artifact write, require explicit local output paths for the route-list and preview/manifest artifacts, and treat `--session-report-json-path` as an intended later manual session output path only. The route-list artifact must contain exact route-list dictionaries only; the preview/manifest artifact must remain descriptive and must not contain realized results, ledger events, report/history results, economics, aggregate PnL, transport fields, credentials, private/account data, sendable requests, order payloads, or unknown-to-zero placeholders.
- RX-061 implements `render-paper-session-report` as a CLI-layer stdout renderer for already-written RX-057 session report JSON artifacts. It must read an explicit local report path, validate the accepted report shape before printing, copy route count, route ids, per-route decision status, per-route paper started state, string-or-null economics, known/unknown summary counts, and `aggregate_paper_net_profit_usd=null`, and reject malformed numeric economics or non-null aggregate PnL rather than coercing values. It must not run sessions, construct adapters, write ledgers, mutate reports, send messages, call networks, add Telegram transport, credentials, discovery/ranking/polling/watchlists, execution automation, live/order/private/account scope, replay/reconciliation/storage migration, new statuses/reasons, aggregate PnL calculation, unknown-to-zero behavior, or second owner paths.
- RX-062 implements the next concrete local/manual/fake-money paper testing-support handoff: a local display command payload parser/fixture helper for the RX-061 renderer plus one explicit local command wrapper. It accepts only payloads with exactly `schema_version=1` and `session_report_json_path`, validates them before report reading, returns only the normalized report path, and delegates display to the accepted RX-061 renderer without recalculating or mutating report values. It must not render through Telegram, send messages, call networks, use credentials, run sessions, construct adapters, write ledgers, mutate reports, discover/rank/watchlist/poll, automate execution, add live/order/private/account scope, calculate aggregate PnL, turn unknowns into zero, or create second owner paths.
- RX-063 implements the next concrete local/manual/fake-money paper testing-support handoff after RX-062 finalization: a local display payload fixture builder. It consumes one explicit already-written RX-057 session report JSON path and one explicit display payload JSON output path, reuses RX-061 report-display validation without printing display output, validates the generated fixture through the accepted RX-062 parser, and writes exactly one local display payload fixture with only `schema_version=1` and `session_report_json_path`. It must not render through Telegram, send messages, call networks, use credentials, run sessions, construct adapters, write ledgers, mutate report results outside the fixture artifact, discover/rank/watchlist/poll, automate execution, add live/order/private/account scope, calculate aggregate PnL, turn unknowns into zero, or create second owner paths.
- RX-064 is prepared as the next concrete local/manual/fake-money paper testing-support handoff after RX-063 reviewer acceptance and finalization: a local display command preview builder. It may consume one explicit local display payload fixture path and write one explicit local preview/manifest artifact with the exact manual `render-paper-session-report-from-payload --paper-session-display-command-payload-json-path ...` command plan, but it must not render through Telegram, send messages, call networks, use credentials, run sessions, construct adapters, write ledgers, mutate report results, discover/rank/watchlist/poll, automate execution, add live/order/private/account scope, calculate aggregate PnL, turn unknowns into zero, or create second owner paths.
- Telegram is later interface direction only. Current tasks do not authorize Telegram bot tokens, credentials, external Telegram network transport, webhooks, alerts, messaging behavior, private/account endpoints, account state, live trading, real orders, sendable exchange requests, or order payloads. Bot-ready command parsing may be a later non-network task; actual Telegram transport and token handling require an explicit future credentials/network gate.
- Do not add speculative helpers, wrappers, future hooks, duplicate owner modules, second decision paths, second snapshot paths, second VWAP paths, second ledger-write paths, or second live execution paths.

## PnL constants

The single authoritative code contract for these constants is `ProductRules`.

- Points value is `0`.
- Expected airdrop value is `0`.
- Leaderboard rewards are `0` in base PnL.
- Unreceived rebates are `0`.
- `MIN_LEG_NOTIONAL_USD = 500`.
- `MIN_NET_PROFIT_USD = 1`.

## Live trading

- Live trading is disabled by default.
- RX-000 must not connect to exchanges.
- RX-000 must not place live orders.
- Future live eligibility requires explicit live gates, fresh executable data, reconciled ledger state, and funding settlement verification.
- Offline funding settlement verification evidence is not permission to trade live by itself.
- Offline ledger reconciliation evidence is not permission to trade live by itself.
- A future live path must fail closed with `LEDGER_NOT_RECONCILED` unless ledger reconciliation is explicitly true for the current append-only ledger history.
- Offline CapturePlan freshness evidence is not permission to trade live by itself.
- A future live path must fail closed with `CAPTURE_PLAN_NOT_FRESH` unless exactly one fake freshness evidence record matches the current `capture_id`, `route_id`, and funding settlement timestamp and is still inside its explicit validity window.
- Offline execution-capability evidence is not permission to trade live by itself.
- A future live path must fail closed unless exactly one fake execution-capability evidence record matches the current `capture_id`, `route_id`, funding settlement timestamp, and validity window, and proves all four current entry/unwind `ExecutableQuote` values fully fill `RouteCandidate.target_notional_usd` from order-book source.
- Offline live gate evidence bundles are not permission to trade live by themselves.
- A future live path that uses a fake evidence bundle must fail closed unless the bundle matches the current `capture_id`, `route_id`, and funding settlement timestamp, carries verified funding-settlement and helper-derived ledger reconciliation outputs, and reuses fresh CapturePlan and execution-capability evidence.
- Recorded fake live gate evidence bundle checks are not permission to trade live by themselves.
- A future live path that uses recorded fake bundle-check evidence must fail closed unless one current append-only ledger event replays against the current Capture, route, funding settlement timestamp, referenced route-decision, funding-verification, and ledger-reconciliation history, and its recorded bundle gate result matches `core/risk/gates.py`.
- Read-only venue adapters, real market-data snapshot assembly, and real-data research runners are data-ingestion and research stages only. They are not permission to place orders, enable live trading, or create executable order plans.
- The real market-data snapshot handoff may fetch one RiseX observation and one Hyperliquid observation for one existing route, then must delegate to `assemble_route_snapshot()` without route decisions, profitability calculations, ledger writes, paper lifecycle, execution planning, or live runner behavior.
- The real-data research runner may evaluate one explicit existing route only by calling the existing adapter handoff and then `evaluate_route(route, snapshot, mode)`. It must fail closed before evaluation on adapter or snapshot handoff failures and must not write ledger events, start paper lifecycle, verify funding settlement, plan execution, place orders, or add live runner behavior.
- The manual one-route real-data CLI may instantiate existing public read-only RiseX and Hyperliquid adapters only after explicit CLI route inputs pass validation, and it may evaluate only through `run_real_data_research_route()`. It must not discover routes, rank routes, poll, loop, write ledger events, start paper lifecycle, plan execution, place orders, use private endpoints, use credentials, read account state, or enable live trading.
- Public funding-rate metadata from the existing read-only RiseX and Hyperliquid adapter responses may become USD expected funding cash only in the existing one-route snapshot path when an explicit `RouteCandidate.target_notional_usd` and leg entry side make the value grounded. Missing, malformed, non-finite, non-public, or ungrounded funding-rate inputs must remain unknown and fail closed. Account-tier fee cash must remain unknown unless a future exact task provides explicit non-private grounding without account assumptions.
- Public fee-rate or fee-source metadata from the existing read-only RiseX and Hyperliquid adapter responses may be preserved on unknown fee cash values for source-aware inspection. Explicit public account-independent taker fee-rate metadata may become USD fee cash only in the existing one-route snapshot path when the existing `RouteCandidate.target_notional_usd`, order-book-taker quote model, selected taker field/container provenance, and entry plus immediate estimated-exit fee semantics make the value grounded. Missing, malformed, non-finite, non-public, maker-only, ambiguous, account-state-dependent, account-tier-dependent, missing-provenance, or ungrounded fee inputs must remain unknown and fail closed; they must not become zero, defaults, or partial USD cash.
- Approval-gated funding settlement verification may record only explicit caller-supplied observed settlement evidence for one existing `Capture`, one existing `RouteCandidate`, and one explicit settlement timestamp. It is not permission to trade live by itself.
- Approval-gated settlement evidence must carry `approval_granted=True`, an observation timestamp equal to the explicit settlement timestamp, and actual funding/notional values with `ValueSource.OBSERVED`; missing approval, false approval, stale observations, unknown values, unobserved sources, malformed payloads, cross-capture, cross-route, cross-settlement, or contradictory evidence fails closed.
- Non-sending execution plans are evidence only. They may describe intended venues, symbols, entry/unwind sides, target notional, settlement timestamp, validity, and prerequisite evidence references, but they must not contain credentials, account state, private endpoint payloads, sendable API requests, or order placement permission.
- A guarded live runner may consume one existing non-sending execution plan only after exact prerequisite evidence is supplied. Missing, stale, malformed, cross-capture, cross-route, cross-settlement, unverified funding, unreconciled ledger, stale plan prerequisites, non-executable execution evidence, disabled live switch, missing non-sending plan, stale non-sending plan, or sendable order material must fail closed.
- A successful guarded live runner result is no-order readiness only. It is not `LIVE_ELIGIBLE`, not ledger evidence, not order placement permission, and not permission to construct sendable exchange requests.
- An explicit approval-gated order placement boundary may consume a successful guarded live runner result only with the exact current `Capture`, `RouteCandidate`, funding settlement timestamp, existing non-sending plan, explicit request timestamp, and caller-supplied approval evidence. Missing, false, stale, malformed, cross-capture, cross-route, cross-settlement, disabled live switch, non-ready guarded result, missing approval, false approval, stale approval, cross-identity approval, missing non-sending plan, stale non-sending plan, stale plan prerequisites, or failed prerequisite evidence must fail closed before any injected deterministic order boundary is invoked.
- A read-only monitoring dashboard may display one existing Capture, one existing route, and already-derived fixture evidence only. Missing, malformed, stale, cross-capture, cross-route, cross-settlement, unverified, unreconciled, non-ready, false approval, stale approval, or boundary-blocked inputs must render as missing or blocked display state without recalculating decisions, replaying evidence, planning execution, invoking boundaries, polling venues, writing ledgers, or placing orders.
- Execution planning without orders, a guarded live runner, and order placement must remain separate tasks with explicit acceptance gates.

## Route statuses

Allowed statuses:

- `RESEARCH_ONLY`
- `PAPER_ELIGIBLE`
- `LIVE_ELIGIBLE`
- `REJECTED`

Forbidden status:

- `CANARY_ELIGIBLE`

## Rejection rules

A route may be rejected only when:

1. The route is technically impossible to execute.
2. Required data for live calculation is missing.
3. `net_profit_usd < MIN_NET_PROFIT_USD`.
4. An explicit user rule is violated.
5. An exchange, market, or mode is disabled.
6. The ledger is not reconciled.
7. There is no fresh `CapturePlan`.
8. The route does not meet `MIN_LEG_NOTIONAL_USD`.
9. The order book cannot execute the configured minimum notional on a required leg.

Code represents these with the centralized `RejectReason` enum.

## No artificial filters

Do not add arbitrary max spread, arbitrary max price impact, arbitrary max levels consumed, hidden conservative buffers, or hidden safety margins. Spread, price impact, basis, slippage, and fees enter PnL calculations instead of acting as independent arbitrary reject filters.

## Unknown values

Unknown values must not silently become zero. If a fee is unknown, use only a user-configured default fee with source `USER_CONFIGURED`. If exact funding is unknown, a future task may use last observed funding before settlement with source `ESTIMATED_FROM_LAST_VALUE`. Public funding-rate metadata may become `ValueSource.OBSERVED` USD cash only when it is explicit, finite, public, and grounded by the route notional plus leg side. Public fee metadata may become `ValueSource.OBSERVED` USD cash only when it is explicit, finite, public, account-independent, taker-rate based, backed by selected field/container provenance, and grounded by route notional plus entry and immediate estimated-exit taker fills. Preserved metadata alone is not fee cash and cannot participate in economics. If there is no grounded funding estimate, the route cannot be `LIVE_ELIGIBLE`.

`RouteCandidate.target_notional_usd` must be an explicit positive finite `Decimal`. Unknown, missing, non-numeric, non-finite, zero, or negative target notionals must fail at construction instead of becoming zero or a default notional. Positive target notionals below `MIN_LEG_NOTIONAL_USD` fail through the centralized minimum-notional route evaluation gate.

Actual settlement funding and actual settlement notional evidence are proof inputs for funding settlement verification. They must be explicitly approved, observed at the settlement timestamp, and `OBSERVED`; documented, estimated, user-configured, unknown, missing, malformed, stale, or non-positive notional actuals are not proof. Ledger reconciliation must verify any recorded funding settlement result against the canonical funding verifier replay from raw checkpoint and settlement evidence.

Ledger reconciliation is a replay contract for append-only history consistency. It must not calculate profitability, mutate route decisions, create live plans, place orders, or silently treat missing, duplicated, non-contiguous, out-of-order, unknown, malformed, stale, or contradictory evidence as reconciled.

Paper result attribution must remain downstream of `DecisionResult` and the fake paper lifecycle. It may explain why paper started or did not start, and may copy existing `DecisionResult` PnL components for inspection, but it must not recalculate route profitability, mutate eligibility, or turn missing economics into zero.

SQLite ledger persistence must preserve append-only sequence continuity across close/reopen boundaries. A persisted append after successful reconciliation must make the prior reconciliation stale until a later reconciliation result covers the current persisted history.

Malformed, stale, or contradictory evidence persisted after reopening a SQLite ledger must remain unreconciled after SQLite round-trip. The helper-derived explicit reconciliation flag must remain false for those histories, and the explicit reconciliation gate must fail closed.

Execution capability is a fake live-gate evidence contract over existing order-book quotes. It must not recalculate VWAP, decide profitability, replace ledger reconciliation, replace funding settlement verification, replace CapturePlan freshness, create live plans, or place orders.

Live gate evidence bundles are fake aggregate evidence only. They must not replay ledger history, replay funding settlement verification, recalculate VWAP/EV/profitability, replace the existing plan freshness or execution-capability gates, create live plans, or place orders.

Live gate evidence bundle ledger records are fake accounting evidence only. They must not recalculate VWAP/EV/profitability, replace ledger reconciliation, replace funding settlement verification, create live plans, place orders, or turn a recorded successful fake bundle check into live eligibility. Ledger reconciliation must fail closed over any malformed, stale, duplicated, missing-reference, or contradictory live gate bundle record. SQLite-persisted live gate bundle records must replay with the same deterministic outcomes as in-memory ledger records.

Execution planning without orders must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, and execution capability evidence. It must not call route evaluation, assemble snapshots, calculate profitability, write ledger events, call adapters, import live runner behavior, create executable `CapturePlan` objects, place orders, or enable live trading.

Guarded live runner readiness without orders must remain downstream of existing route decisions, funding settlement verification, ledger reconciliation, CapturePlan freshness, execution capability evidence, live-gate bundle checks, and non-sending execution planning. It must not call route evaluation, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, import order placement behavior, construct sendable exchange requests, place orders, mutate route eligibility, or enable live trading by default.

Explicit approval-gated order placement boundaries must remain downstream of guarded no-order readiness and non-sending execution planning. They must not call route evaluation, assemble snapshots, calculate profitability, replay funding or ledger history, write ledger events, call adapters, use credentials, create exchange request payloads before exact approval, place real orders by default, mutate route eligibility, add route statuses or reject reasons, or enable live trading by default. The default product rules must still fail closed.

Read-only monitoring dashboard rendering must remain downstream of existing result contracts. It must preserve missing economics as missing display values instead of zero, and it must not call route evaluation, snapshot assembly, venue adapters, funding verification, ledger reconciliation, live-gate bundle checks, execution planning, guarded live runner execution, approval-boundary execution, ledger writes, network I/O, or order placement.

Manual one-route real-data CLI output must remain downstream of existing `DecisionResult` values. It may print route id, mode, status, reasons, net profit, and existing entry EV fields for inspection, but it must not recalculate profitability, mutate eligibility, call snapshot assembly or route evaluation directly, or turn missing economics into zero.

Manual one-route public readiness report output must remain downstream of the existing public one-route adapter handoff, `assemble_route_snapshot()` path, source-aware fee/funding completion, and `evaluate_route()` path. It may display the retained snapshot's public funding and fee evidence, existing Entry EV fields, decision status/reasons, deterministic `UNKNOWN` components, and a display-only public-readiness conclusion, but it must not recalculate profitability, add or mutate route statuses or reject reasons, mutate eligibility, write ledger events, start paper lifecycle, verify funding settlement, reconcile ledgers, plan execution, run guarded live readiness, call approval-boundary execution, construct sendable requests, place orders, use private/account endpoints or credentials, read account state, enable live trading, or turn unknown evidence into zero or success.

Structured JSON stdout output for the manual one-route public readiness report may serialize only the same existing public report evidence for machine reading. It must remain opt-in, require the existing public-readiness report flag, emit to stdout only for one explicit RiseX plus Hyperliquid route, preserve unknowns as unknown/null rather than zero or success, and must not write files or ledgers, mutate statuses/reasons/eligibility/state, change adapters or endpoints, add discovery/ranking/watchlists, poll or schedule, use private/account endpoints or credentials, read account state, construct sendable requests or order payloads, place orders, automate execution, or enable live trading. A JSON format selector without the public-readiness report flag must fail closed rather than silently changing ordinary one-decision output.

The manual public paper-trader bridge may start fake paper lifecycle only downstream of an existing `DecisionResult` produced from one explicit public route in `EvaluationMode.ENTRY`. Fake paper ledger writes must remain behind `core/accounting/ledger.py`, optional local SQLite persistence must remain inside the existing `storage/sqlite/ledger.py` contract, and non-started decisions must remain explicit paper rejections. A missing public snapshot blocks paper lifecycle because no funding settlement timestamp is available; that missing snapshot must remain unknown in stdout rather than becoming a default timestamp, zero, success, or profitability. The bridge must not recalculate public route economics, bypass `evaluate_route()`, mutate route eligibility, read account state, construct order material, or treat missing funding, fee, snapshot, Entry EV, or net-profit values as zero.

A manual serial paper session runner may aggregate only deterministic route outcomes and counts from a finite operator-supplied explicit route list. It must not discover, rank, poll, schedule, alert, loop in the background, read private/account state, construct order material, or automate execution. Missing snapshot, Entry EV, funding, fee, decision net profit, or paper PnL values must remain missing in route output and session summaries; session aggregates must not turn unknown values into zero, success, or profitability.

The RX-055 manual serial command accepts only a non-empty finite local JSON array of at most 25 exact route objects. Discovery-style, ranking-style, watchlist-style, polling-style, over-limit, missing, empty, malformed, extra-field, non-ENTRY, non-opposing-side, non-finite-notional, or timezone-naive route-list inputs fail before adapter construction. The 25-route cap is an operator input safety bound, not a strategy filter: the command must not rank, truncate, skip, auto-batch, poll, schedule, or silently accept partial lists. Session summaries are count-only for outcomes, Entry EV known/unknown, paper expected funding known/unknown, paper total fees known/unknown, decision net profit known/unknown, and paper net profit known/unknown; aggregate paper PnL remains `None`.

The RX-058 local payload parser returns only exact route-list dictionaries suitable for the existing `paper-trade-session --routes-json-path` input. It must not add economics, decision, paper, summary, report, ledger, aggregate PnL, unknown-to-zero, or transport fields. Malformed, over-limit, non-ENTRY, extra-field, missing-field, non-string, non-finite, same-side, wrong-venue, or timezone-naive payload fixtures fail before any session execution, adapter construction, ledger write, or report write.

Allowed value sources are exactly:

- `DOCUMENTED`
- `OBSERVED`
- `ESTIMATED_FROM_ORDERBOOK`
- `ESTIMATED_FROM_LAST_VALUE`
- `USER_CONFIGURED`
- `UNKNOWN`
