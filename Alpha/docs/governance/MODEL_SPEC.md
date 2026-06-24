# Alpha Model Specification

Project: `Alpha`
Governance spec version: `1.0.0`
Fact discipline: `EXTRACTED`, `RECONSTRUCTED`, `PROPOSED`, `UNKNOWN`, `NOT_APPLICABLE`

Machine counts below are controlled by the registries:

- model_count: 9
- formula_count: 9
- parameter_count: 55

## Canonical Sources

- Models: `docs/governance/model_registry.yaml`
- Formulas: `docs/governance/formula_registry.yaml`
- Parameters: `docs/governance/parameter_registry.csv`
- Delivery tasks: `docs/governance/delivery_tasks.yaml`
- Traceability: `docs/governance/TRACEABILITY_MATRIX.csv`

Legacy files `功能清单`, `开发记录`, and `模型参数文件` are compatibility indexes only.

## A. Model Overview

| ID | Name | Kind | Status | Version | Evidence |
|---|---|---|---|---|---|
| MOD-001 | Momentum strategy tournament ranking | ranking_model | active | strategy-tournament-v0 | `Alpha/backend/app/services/strategy_iteration.py:28` |
| MOD-002 | Research risk score | risk_model | active | risk-score-v0 | `Alpha/backend/app/services/risk.py:22` |
| MOD-003 | Pre-trade owner-review gate | deterministic_rule_engine | active | pre-trade-gate-v0 | `Alpha/backend/app/services/risk.py:40` |
| MOD-004 | Live order policy and fail-closed broker | risk_model | active | live-policy-fail-closed-v0 | `Alpha/backend/app/services/policy.py:38`; `Alpha/backend/app/services/live_broker.py:19` |
| MOD-005 | Paper trading loop | deterministic_workflow_model | active | paper-loop-v0.0.1-atomic-storage | `Alpha/backend/app/services/paper_trading_loop.py:42`; `Alpha/backend/app/services/paper_trading_loop.py:59` |
| MOD-006 | Paper broker accounting | business_calculation_model | active | paper-broker-v0.0.1-atomic-storage | `Alpha/backend/app/services/paper_broker.py:44`; `Alpha/backend/app/services/atomic_json_store.py:31` |
| MOD-007 | Approval queue freshness | deterministic_rule_engine | active | approval-freshness-v0.0.1-atomic-storage | `Alpha/backend/app/services/approval_queue.py:19`; `Alpha/backend/app/services/atomic_json_store.py:31` |
| MOD-008 | Strategy DSL safety validation | deterministic_rule_engine | active | strategy-dsl-v0 | `Alpha/backend/app/schemas/strategy_dsl.py:22` |
| MOD-009 | Equal-weight buy-and-hold fixture benchmark | backtest_strategy | active | buy-hold-fixture-v0 | `Alpha/backend/app/services/backtest.py:14` |

Use cases are research, fixture backtest, paper trading, owner-review tickets, local dashboard visibility, and safety gates. Non-use cases are autonomous real-money broker order submission, public buy/sell advice, external capital management, leverage, margin, options, short selling, and crypto withdrawals.

## B. Assumptions

| ID | Fact level | Assumption | Validation or falsification |
|---|---|---|---|
| ASM-001 | EXTRACTED | Alpha committed defaults are research/paper/review-only and do not enable unattended real-money submission. | `Alpha/configs/trading_governor_policy.yaml:5`; `Alpha/tests/test_policy.py:5` |
| ASM-002 | EXTRACTED | Current strategy and paper-trading evidence uses fixture prices. | `Alpha/backend/app/services/paper_trading_loop.py:138`; `Alpha/data/sample_prices.csv` |
| ASM-003 | EXTRACTED | Live broker adapter remains fail-closed. | `Alpha/backend/app/services/live_broker.py:27`; `Alpha/tests/test_live_broker_fail_closed.py:6` |
| ASM-004 | UNKNOWN | Production market data, broker paper integration, live execution policy, multi-year validation, slippage model, and cost-model calibration are not fully evidenced in this repository snapshot. | Open task `TASK-ALPHA-B-001` |

## C. Functions And Rules

Formula details live in `formula_registry.yaml`. The active rules include:

- `FORM-001`: deterministic momentum candidate ranking with lookbacks `(5, 10, 20)`, score `total_return + 0.5*oos_return + 0.01*hit_rate - abs(drawdown)`, and decision-priority sort.
- `FORM-002`: risk score starts at 100 and subtracts penalties for drawdown, low trade count, and high turnover.
- `FORM-003`: pre-trade gate rejects kill-switch, missing idempotency, invalid side, non-positive quantity/price/notional, missing max notional, and excessive notional.
- `FORM-004`: live policy rejects unless every required live safety gate passes; `FailClosedLiveBroker` still rejects rather than submitting.
- `FORM-005`: paper loop composes tournament, order intent, risk check, locked ticket queue enqueue, optional locked persisted paper fill, portfolio snapshot, and audit event. S3PBT02 records app-runtime lifecycle truth under MOD-005 without changing trading formula values.
- `FORM-006`: paper broker updates cash and positions deterministically, rejects duplicate or invalid paper orders, and serializes persisted submit/save through locked atomic JSON writes.
- `FORM-007`: approval freshness maps expiry timestamps to fresh/expired/unknown actionability.
- `FORM-008`: strategy DSL validates payload ranges and MVP prohibitions.
- `FORM-009`: buy-and-hold fixture benchmark uses equal-weight returns and one-time cost/slippage.

## D. Parameters

The parameter registry separates default values, prior values, active values, weights, source/rationale, code references, config references, and tests. No live secret, credential, account identifier, or environment value is recorded.

Important safety parameters:

- `PARAM-023 live_trading.enabled`: active value `false`, from `Alpha/configs/trading_governor_policy.yaml:5`.
- `PARAM-030 fail_closed_live_broker`: adapter always returns rejected, from `Alpha/backend/app/services/live_broker.py:27`.
- `PARAM-031 DEFAULT_REFRESH_INTERVAL_SECONDS`: active value `300`, from `Alpha/backend/app/services/paper_trading_loop.py:19`.
- `PARAM-017 max_order_value_aud`: active value `100`, from `Alpha/configs/trading_governor_policy.yaml:33`.

## E. Methodology

Current methodology is deterministic and fixture-based:

- Strategy candidates are simple momentum candidates across fixture symbols and lookbacks.
- Risk scoring is threshold and penalty based.
- Paper trading is deterministic workflow execution over fixture data and a local paper broker; S3PBT01 makes the persisted queue and paper broker files atomic and serialized.
- Live order submission is intentionally not implemented; fail-closed behavior is the active safety design.
- Current validation is unit/fixture testing, not production broker or real-market validation.

Alternative methods such as multi-year walk-forward, cost/slippage calibration, broker paper API integration, or live execution policy remain `UNKNOWN` and are linked to `TASK-ALPHA-B-001`.
S3PBT01 covers persisted queue/broker atomicity; S3PBT02 covers AutoPaperAgent stop truthfulness and dashboard PID cleanup. Disk-error, crash-recovery, stale-PID process-reuse, force-termination corruption, and full write-after-stop fault injection remain S3PBT03 evidence.

## F. Strategy And Safety Logic

Signal formation:

1. Read fixture close prices.
2. For each symbol/lookback, calculate momentum and walk-forward validation.
3. Score and rank candidates.
4. Select a tradable winner whose latest close does not exceed `max_order_value_aud`.

Gate logic:

1. `pre_trade_risk_check` rejects unsafe paper/live candidates.
2. `BrokerReadyOrderTicket` always requires human action.
3. `ApprovalQueue` separates fresh pending tickets from expired tickets.
4. `GovernorPolicy` and `FailClosedLiveBroker` reject live trading by default.

Failure behavior is fail-closed: missing policy raises, disabled live trading rejects, invalid order values reject, duplicate paper idempotency rejects, expired tickets lose owner-actionability.

## G. Verification

Focused verification commands:

- `python -m pytest tests/test_policy.py tests/test_live_broker_fail_closed.py tests/test_strategy_iteration.py tests/test_paper_trading_loop.py -q`
- `python scripts/validate_project_governance.py --project Alpha`

Known uncovered scenarios:

- Production market data.
- Broker paper API.
- Real-money execution policy decision.
- Multi-year out-of-sample validation.
- Cost and slippage calibration beyond fixture benchmark defaults.

Release gate: Alpha must not be promoted as real-money release-ready until `DECISION-ALPHA-EXECUTION-POLICY` is explicitly resolved.
