# Architecture

RiseX Points Farmer is a modular monolith. The repository is organized around a single capture-centric decision pipeline and explicit ownership of business logic.

## Top-level layout

```text
apps/
  research_runner/
  paper_runner/
  live_runner/
  dashboard/
  cli/
core/
  domain/
  venues/
  pipeline/
  economics/
  risk/
  execution/
  accounting/
  monitoring/
  config/
storage/
  sqlite/
  migrations/
tests/
  unit/
  integration/
  invariant/
  replay/
```

## Core domain

- `Capture`: one funding settlement opportunity.
- `RouteCandidate`: a potential RiseX + hedge route.
- `VenueSnapshot`: normalized current market and cash-flow inputs.
- `ExecutableQuote`: current executable VWAP quote for a target notional.
- `DecisionResult`: result of the shared decision pipeline.
- `RouteStatus`: `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `LIVE_ELIGIBLE`, `REJECTED`.
- `EvaluationMode`: `DISCOVERY` or `ENTRY`.

## Single-owner business logic

- Fees are calculated only in `core/economics/fees.py`.
- Funding is calculated only in `core/economics/funding.py`.
- Liquidity and VWAP are calculated only in `core/economics/liquidity.py`.
- Basis and unwind tracking belong only in `core/economics/basis.py`.
- Entry EV is calculated only in `core/economics/ev.py`.
- Risk gates belong only in `core/risk/gates.py`.
- Route decisions happen only in `core/pipeline/evaluate.py`.
- Orders can be sent only through `core/execution/`.
- Ledger writes happen only through `core/accounting/ledger.py`.

## Evaluation pipeline

`evaluate_route(route, snapshot, mode)` is the only route decision path.

RX-000 behavior:

1. Verify the route and all fake executable VWAP quotes can represent the configured minimum notional.
2. Calculate entry EV from explicit funding, explicit fees, and simulated immediate roundtrip cost.
3. Reject only when technical executability fails or net profit is below the configured minimum.
4. Return `PAPER_ELIGIBLE` for profitable fake routes while live gates are not implemented.
5. Never place orders.
6. Optionally append the decision event to the ledger through `core/accounting/ledger.py`.

## No artificial filters

Spread, price impact, basis, slippage, and fees are not independent arbitrary reject filters. They must be represented in executable VWAP, fee, funding, and PnL calculations.

## Entry and exit economics

Entry EV does not use `expected_basis_change` as a prediction. Before entry, the architecture uses current executable VWAP and simulated immediate roundtrip cost. After entry, future work must monitor `current_unwind_pnl_usd`, meaning the PnL if both legs were closed using current order books.
