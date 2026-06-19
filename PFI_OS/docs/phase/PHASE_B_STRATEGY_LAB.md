# Phase B Strategy Lab Vertical Slice

Schema: `PFIOSPhaseBStrategyLabContractV1`

Status: first Strategy Lab vertical slice complete.

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

## Contract Tests

- `tests/contract/test_phase_b_strategy_lab_workflow.py`

The tests verify:

1. Strategy backtesting remains a core non-regression constraint.
2. Market-feel training remains retained and hides future bars.
3. Workflow output contains the full decision-support contract.
4. Reproducibility hashes are stable for identical bars, strategy version,
   parameters, and cost model.
5. Operational Store receives source, evidence, job, and human-review task
   records.
6. No live trading, broker call, or order execution path is exposed.

## Out Of Scope

- Migrating every legacy Strategy Lab UI panel into the Web Shell.
- The other three Phase B vertical slices are covered by their workflow docs.
- Building Phase C worker/SSE reliability.
- Building Phase D deployment, backup/restore, local LLM, and final MVP
  acceptance.

## Next Iterations

1. Connect Strategy Lab workflow read models to the Web Shell when the Phase B
   workflow set is stable.
2. Start Phase C worker/SSE reliability from the completed Phase B contracts.
