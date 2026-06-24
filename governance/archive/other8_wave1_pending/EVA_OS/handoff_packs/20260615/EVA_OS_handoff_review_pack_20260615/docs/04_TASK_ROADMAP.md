# EVA_OS 任务清单与开发路线图

## Work Sequencing Principle

Do not upgrade all systems at once. Continue one subsystem per run to reduce confusion, testing risk, and token/context pressure.

## Current Open Work

| Priority | Task | Goal | Suggested Acceptance |
| --- | --- | --- | --- |
| P0 | Rebuild full dev environment | Restore reliable full-suite validation | `.venv` exists, dependencies installed, smoke tests pass |
| P0 | Vectorized Research Mode MVP | Use replay batches for fast deterministic research | Replay JSON -> OHLCV DataFrame -> parameter scan test |
| P0 | Hotspot analysis performance | Reduce slow button-trigger behavior | Cached/precomputed path, user-visible latency reduced |
| P1 | Replay cursor pagination | Correct replay when timestamps collide | Cursor includes timestamp + event_id |
| P1 | Bar cache replay | Replay from structured cache files | CSV/parquet input covered by tests |
| P1 | Multi-asset replay | Synchronize multiple symbols/intervals | Deterministic merge order and tests |
| P1 | Workbench consolidation | Reduce context/token pressure | Summary-first command surface and fewer overlapping views |
| P1 | 52ETF integration | Make read-only ETF reference path useful | Source log, cache, failure mode, docs |
| P2 | Discrete Event Simulation Mode | Event-by-event simulation with costs/risk | Portfolio state, slippage/cost model, audit log |
| P2 | Agent Market Simulation Mode | Research-only agent loop | No real orders, deterministic input, audit output |
| P2 | TradingView-like UX | Chart/indicator/strategy controls | Stable core first, then UI |
| P2 | Moomoo realtime research | Read-only OpenD quote ingestion | Fail-closed readiness, no trading |
| P2 | Business evidence completion | Productize cashflow/policy/consumption | Real reviewed evidence snapshots and action gates |
| P3 | Formal audit pack regeneration | Create new `eva_os_dev_audit_pack` | Only after next stable subsystem run |

## Suggested Iteration Plan

### Iteration 1: Environment and Smoke Gate

Goal: make future development repeatable.

Steps:

1. Recreate `.venv`.
2. Install test/app/data extras.
3. Run focused tests.
4. Split test commands into smoke, target, integration, and full.
5. Update `docs/Testing.md`.

### Iteration 2: Vectorized Research Mode MVP

Goal: turn Event Replay into practical research input.

Steps:

1. Add replay-to-OHLCV conversion module.
2. Add DataFrame validation rules.
3. Add parameter scan adapter.
4. Add tests for sample replay.
5. Add CLI smoke script.
6. Update docs.

### Iteration 3: Hotspot Analysis Optimization

Goal: reduce slow UI actions and token pressure.

Steps:

1. Profile current hotspot button path.
2. Identify repeated expensive calls and generated text paths.
3. Add cache/precompute layer.
4. Add progress/status UI.
5. Validate no stale or fabricated conclusion.

### Iteration 4: 52ETF Productization

Goal: convert 52ETF from initial integration into a reviewed research reference.

Steps:

1. Define allowed data and request boundaries.
2. Add source log and cache.
3. Add freshness and failure-state display.
4. Add tests with mocked response.
5. Add user guidance and risk note.

### Iteration 5: Business Subsystems Evidence Gate

Goal: move Token ROI, CashFlow, Policy, and Consumption closer to fully productized state.

Steps:

1. Define evidence input templates.
2. Add manual review queue.
3. Add missing evidence log.
4. Add value and decision records.
5. Update Command Center scoring.

## Stop Conditions

Stop and report instead of expanding scope when:

- full environment cannot be built;
- tests fail due to unclear dependency mismatch;
- a feature would require private credentials or external account access;
- a requested change risks enabling live trading or real payments;
- evidence is missing but output would look actionable.
