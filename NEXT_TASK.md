## Task ID

RX-004 — Per-Venue Observation and Route Snapshot Contracts

## Objective

Define the offline contracts that turn normalized per-venue observations into one route-aligned `VenueSnapshot` for the existing single `evaluate_route(route, snapshot, mode)` path, without implementing scanning orchestration or real adapters.

## Allowed scope

- Add fake-data-compatible per-venue observation contracts for normalized order books and source-aware economics inputs.
- Add one route snapshot assembly contract that verifies required RiseX and hedge observations are present before creating a `VenueSnapshot`.
- Keep all behavior deterministic, offline, read-only, and non-trading.
- Reuse the existing `RouteCandidate`, `VenueSnapshot`, economics modules, risk gates, and `evaluate_route()` pipeline.
- Add focused unit and invariant tests for contract construction, missing data, and route alignment compatibility.

## Forbidden scope

- Do not implement Broad Scan.
- Do not implement Focused Refresh.
- Do not implement real RiseX, Hyperliquid, network, API, authentication, or production adapters.
- Do not implement paper execution, order placement, persistence, migrations, dashboard code, or live trading.
- Do not add a second route model, second EV path, second route decision function, canary architecture, hold-next-cycle logic, artificial filters, secrets, or production credentials.

## Required files

- `core/domain/contracts.py`
- `core/venues/base.py`
- `apps/research_runner/fake_data.py`
- `tests/unit/`
- `tests/invariant/`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `STATUS.md`
- `NEXT_TASK.md`

## Required tests

- Contract tests for per-venue observation inputs.
- Contract tests for route snapshot assembly with complete fake observations.
- Fail-closed tests for missing RiseX observation, missing hedge observation, missing funding input, missing fee input, and quote/route mismatch.
- Invariant tests proving `evaluate_route()` remains the only route decision function and `VenueAdapter` remains per-venue.
- Invariant tests proving no Broad Scan, Focused Refresh, real adapter, paper execution, persistence, dashboard, live trading, canary, hold-next-cycle, artificial filter, secret, or order-placement code is introduced.

## Required report format

- Task ID
- Branch
- Starting HEAD
- Final HEAD
- Changed files
- What was implemented
- Tests run
- Test results
- Known limitations
- Risk impact
- Next suggested task
