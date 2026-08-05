# Status

- Last accepted task: RX-002 — Product Rules, Config Contracts, and No-Artificial-Filters Enforcement
- Accepted baseline RX-002 HEAD: `35dabda35fa569385a9f7c787346e176b5809e88`
- Current task: RX-002A — Add GitHub CI Workflow
- Current branch: task/rx-002a-github-ci
- Repository state at task start: clean checkout at accepted baseline RX-002 HEAD

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
- GitHub CI now runs the existing test suite and compile check only; it does not add linting, coverage, deployment, secrets, Docker, exchange connectivity, or live trading.

## Next recommended task

RX-003 — Economics Engine: Fees, Funding, VWAP Liquidity, Basis, and Entry EV
