# Phase B Strategy Lab Vertical Slice

Schema: `PFIOSPhaseBStrategyLabContractV1`

Status: Strategy Lab vertical slice complete with PFI-009 Gate 3 evidence.

As of: 2026-06-19 Australia/Sydney

## Goal

Make Strategy Lab the first operational Phase B workflow after the Phase A
data-foundation completion gate. This slice keeps strategy backtesting as a
core workflow and preserves market-feel training as a training mode without
turning either output into a live order path.

## Current Slice

- Adds `pfi_os.application.strategy_lab_workflow`.
- Declares workflow schema `PFIOSPhaseBStrategyLabWorkflowV1`.
- Runs approved strategy backtests through the existing deterministic
  `BacktestEngine`.
- Records strategy version, parameters, cost model, data window, bar checksum,
  and reproducibility hash.
- Preserves market-feel training by building a training case that hides future
  bars before answer reveal.
- Emits a decision-support object with thesis, catalysts, counter-evidence,
  invalidation conditions, risks, portfolio effect, model versions, source
  ids, and `human_review_required: true`.
- Enforces research-only safety fields:
  `no_live_trading`, `no_broker_calls`, and `no_order_execution`.
- Writes Strategy Lab source, evidence, job, and review-task records into the
  Operational Store.

## PFI-009 Promotion

PFI-009 promotes this Phase B workflow into a Gate 3 Strategy acceptance
contract:

- `src/pfi_os/application/pfi009_strategy_acceptance.py`
- `tests/contract/test_pfi009_strategy_vertical_acceptance.py`
- `scripts/pfi009StrategyAcceptance.sh`
- `docs/development/PFI009_STRATEGY_VERTICAL_ACCEPTANCE.md`

The promotion adds deterministic PIT bars, corporate-action adjustment,
delisted-symbol exclusion, train/test validation, walk-forward validation,
model registry, Durable Job Store cancel/resume proof, same-shell Chinese Web
Shell controls, and rollback proof. The acceptance remains research-only: it
does not connect to brokers, mutate holdings, create live signals, or submit
orders.

## Contract Tests

- `tests/contract/test_phase_b_strategy_lab_workflow.py`
- `tests/contract/test_pfi009_strategy_vertical_acceptance.py`

The tests verify:

1. Strategy backtesting remains a core non-regression constraint.
2. Market-feel training remains retained and hides future bars.
3. Workflow output contains the full decision-support contract.
4. Reproducibility hashes are stable for identical bars, strategy version,
   parameters, and cost model.
5. Operational Store receives source, evidence, job, and human-review task
   records.
6. No live trading, broker call, or order execution path is exposed.
7. PFI-009 PIT backtest, train/test, walk-forward, no-future-data, model
   registry, cancel/resume, same-shell UI, script, target-gate, and rollback
   contracts are wired.

## Out Of Scope

- Migrating every legacy Strategy Lab UI panel into the Web Shell.
- Building Phase C worker/SSE reliability.
- Building Phase D deployment, backup/restore, local LLM, and final MVP
  acceptance.

## Next Iterations

1. Continue Gate 4 with PFI-010 Minute Fast Path evidence.
2. Re-run all four Gate 3 vertical slices during the final Gate 7 release
   package.
