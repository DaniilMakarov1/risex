# RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV

## Task ID

RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV

## Objective

Implement the first real pure economics contracts for fees, funding estimates, VWAP liquidity, basis/unwind tracking, and entry EV while keeping the system offline, fake-data-compatible, and non-trading.

The implementation must strengthen the existing single `evaluate_route(route, snapshot, mode)` pipeline without adding live exchange connectivity or changing product strategy.

## Allowed Scope

- Add or refine pure economics logic inside the established single-owner modules.
- Use `ValueSource` and `EstimatedValue` for fee, funding, liquidity, and other source-sensitive economics inputs where appropriate.
- Model user-configured default fees only with `source=USER_CONFIGURED`.
- Model last-observed funding fallbacks only with `source=ESTIMATED_FROM_LAST_VALUE`.
- Calculate VWAP executability for the configured `MIN_LEG_NOTIONAL_USD = 500`.
- Keep poor spread, price impact, slippage, basis, and fees inside PnL math, not as independent reject filters.
- Keep `evaluate_route()` as the only route decision pipeline for both `DISCOVERY` and `ENTRY` modes.
- Keep all behavior offline and compatible with fake data and tests.
- Update focused unit, integration, and invariant tests for the new economics contracts.
- Update `STATUS.md`, `DECISIONS.md` if a durable architecture decision is made, and `NEXT_TASK.md` with exactly one next proposed task.

## Forbidden Scope

- Do not implement real exchange adapters.
- Do not add API keys, secrets, credentials, or environment-specific production configuration.
- Do not implement or enable live trading.
- Do not place orders.
- Do not add `CANARY_ELIGIBLE`, `canary_runner`, or separate canary architecture.
- Do not add artificial filters such as arbitrary max spread, max price impact, max levels consumed, hidden conservative buffers, or hidden safety margins.
- Do not use `expected_basis_change` as a forecast of future basis.
- Do not create a second route decision pipeline, second EV path, second fee model, second funding model, or second liquidity model.
- Do not change domain lifecycle states unless the task explicitly proves the existing state machine blocks the economics contracts.
- Do not start real venue connectivity, dashboard work, persistence migrations, paper execution, or RX-004 scope.

## Required Files / Modules

Read before implementing:

- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT_INVARIANTS.md`
- `IMPLEMENTATION_PLAN.md`
- `STATUS.md`
- `DECISIONS.md`
- `NEXT_TASK.md`

Primary implementation modules:

- `core/economics/fees.py`
- `core/economics/funding.py`
- `core/economics/liquidity.py`
- `core/economics/basis.py`
- `core/economics/ev.py`
- `core/pipeline/evaluate.py`
- `core/risk/gates.py`

Supporting modules may be updated only if needed for contracts and tests:

- `core/domain/contracts.py`
- `core/domain/enums.py`
- `core/config/product_rules.py`
- `apps/research_runner/fake_data.py`
- `apps/cli/main.py`
- `tests/unit/`
- `tests/integration/`
- `tests/invariant/`

Documentation updates required at task completion:

- `STATUS.md`
- `DECISIONS.md` if an architecture decision was made
- `NEXT_TASK.md`

## Required Tests

Add or update tests that prove:

- Unknown values never silently become zero.
- User-configured fee defaults require `ValueSource.USER_CONFIGURED`.
- Last-observed funding estimates use `ValueSource.ESTIMATED_FROM_LAST_VALUE`.
- Missing funding estimates cannot produce `LIVE_ELIGIBLE`.
- VWAP for `MIN_LEG_NOTIONAL_USD = 500` is calculated from order-book levels.
- If a $500 target notional cannot be executed on a required leg, the route is rejected through a centralized `RejectReason`.
- Poor executable prices affect net PnL instead of triggering artificial spread, impact, or levels-consumed rejects.
- Entry EV uses expected funding, hedge funding, explicit/source-aware fees, entry VWAP, and simulated immediate roundtrip or close VWAP.
- `evaluate_route()` remains the only route decision path.
- Live trading remains disabled by default and no orders are placed.

Run before final report:

- `python3 -m pytest`
- `python3 -m compileall apps core storage tests`
- `git diff --check`

## Required Report Format

Return the full RX-003 report inside one fenced Markdown code block and no prose outside it.

Use this template:

```text
Task ID:
Branch:
Starting HEAD:
Final HEAD:
Changed files:
What was implemented:
Tests run:
Test results:
Known limitations:
Risk impact:
Next suggested task:
```
