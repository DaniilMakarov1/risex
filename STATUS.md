# Status

- Last accepted task: RX-001 — Domain Contracts and Capture State Machine
- Accepted baseline RX-001 HEAD: `53f3b35c62f3ec510cb7c0f40d2784e3788ae2a5`
- Current task: RX-002 — Product Rules, Config Contracts, and No-Artificial-Filters Enforcement
- Current branch: task/rx-002-product-rules-config
- Repository state at task start: clean checkout at accepted baseline RX-001 HEAD

## Known limitations

- Only fake data is available.
- No real RiseX or Hyperliquid adapters exist.
- No live order placement exists.
- No persistent SQLite ledger exists yet.
- Funding settlement verification is not implemented.
- Live eligibility cannot be operationally trusted yet.
- Capture lifecycle transitions are in-memory domain operations only; no ledger persistence for lifecycle events exists yet.
- Fee, funding, VWAP liquidity, basis, and entry EV are still fake/minimal walking-skeleton economics.
- `EstimatedValue` is available as a source-aware domain value object, but the current fake `VenueSnapshot` still uses explicit decimal inputs until RX-003 economics contracts are implemented.

## Next recommended task

RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
