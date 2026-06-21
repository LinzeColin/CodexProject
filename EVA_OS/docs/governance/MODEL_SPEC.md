# EVA_OS Model Specification

- model_count: 16
- formula_count: 16
- parameter_count: 189
- task_count: 13
- Evidence level: EXTRACTED for current code/config/tests; RECONSTRUCTED only for scoped Git events; UNKNOWN items are linked to blocked tasks.

## A. Model Overview

### MOD-001 Built-in Research Strategy Signal Library

- fact_level: EXTRACTED
- kind: deterministic signal/rule model
- purpose: Generate target weights or order intent for built-in research strategies across trend, mean reversion, momentum and Alipay-style behavioral rules.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/strategies/trend/ma_crossover.py:1; EVA_OS/src/quantlab/strategies/behavioral/alipay.py:11; EVA_OS/src/quantlab/strategies/profiles.py:322`
- test reference: `EVA_OS/tests/test_backtest.py; EVA_OS/tests/test_alipay_strategy.py; EVA_OS/tests/test_strategy_profiles.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-001`
- parameter_ids: `PARAM-001..PARAM-030`

### MOD-002 Backtest Execution and Performance Metrics

- fact_level: EXTRACTED
- kind: backtest execution and performance calculation model
- purpose: Execute target-weight or order-value signals with modeled costs and compute return, risk, drawdown, turnover, win rate and cost metrics.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/backtest/engine.py:13; EVA_OS/src/quantlab/backtest/metrics.py:22`
- test reference: `EVA_OS/tests/test_backtest.py; EVA_OS/tests/test_alipay_strategy.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-002`
- parameter_ids: `PARAM-031..PARAM-040`

### MOD-003 Research Risk Gate

- fact_level: EXTRACTED
- kind: risk scoring and gate model
- purpose: Score data quality, return, drawdown, trading friction and validation evidence into ContinueResearch, WatchOnly, NeedsMoreEvidence or DoNotUse.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/risk/gates.py:16`
- test reference: `EVA_OS/tests/test_risk_gates.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-003`
- parameter_ids: `PARAM-041..PARAM-052`

### MOD-004 Decision Quality Score

- fact_level: EXTRACTED
- kind: multi-dimension research quality score
- purpose: Score thesis clarity, evidence quality, risk identification, exit conditions, exposure discipline, emotional risk, counterarguments, liquidity and validation sufficiency.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/risk/decision_quality.py:36`
- test reference: `EVA_OS/tests/test_decision_quality.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-004`
- parameter_ids: `PARAM-053..PARAM-068`

### MOD-005 Data Quality and Cross-source Close Validation

- fact_level: EXTRACTED
- kind: data quality and cross-source validation model
- purpose: Assess OHLCV bars, checksum canonical data, and compare close prices across at least two providers using percentage tolerance.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/data/quality.py:34; EVA_OS/src/quantlab/data/validation.py:34`
- test reference: `EVA_OS/tests/test_data_quality.py; EVA_OS/tests/test_validation_execution.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-005`
- parameter_ids: `PARAM-069..PARAM-076`

### MOD-006 Validation Priority and Execution Gate

- fact_level: EXTRACTED
- kind: validation task prioritization and execution gate
- purpose: Rank evidence-repair tasks, route missing-input blockers, and execute supported CrossSourceValidation tasks fail-closed.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/research/validation_priority.py:52; EVA_OS/src/quantlab/research/validation_execution.py:37`
- test reference: `EVA_OS/tests/test_validation_priority.py; EVA_OS/tests/test_validation_execution.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-006`
- parameter_ids: `PARAM-077..PARAM-091`

### MOD-007 Data Trust Audit

- fact_level: EXTRACTED
- kind: evidence classification and trust gate
- purpose: Classify local project, provider, strategy, holdings, ResearchBus, validation, experiment and report artifacts into trust states and audit status.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/system/data_trust.py:48`
- test reference: `EVA_OS/tests/test_data_trust_audit.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-007`
- parameter_ids: `PARAM-092..PARAM-098`

### MOD-008 Integration, Daily Readiness and Command Center Status

- fact_level: EXTRACTED
- kind: system readiness gate aggregation model
- purpose: Aggregate data trust, integration audit, health, provider, report and Token ROI evidence into readiness and command-center status/action queues.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/system/integration_audit.py:27; EVA_OS/src/quantlab/system/daily_readiness.py:16; EVA_OS/src/quantlab/executive/command_center.py:208`
- test reference: `EVA_OS/tests/test_integration_audit.py; EVA_OS/tests/test_daily_readiness.py; EVA_OS/tests/test_command_center.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-008`
- parameter_ids: `PARAM-099..PARAM-105`

### MOD-009 Report Decision Support and Evidence Gap Tasks

- fact_level: EXTRACTED
- kind: report readiness score and task generator
- purpose: Classify RunMetadata/report evidence into ContinueResearch, WatchOnly, NeedsMoreEvidence or DoNotUse and split missing evidence into validation tasks.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/reports/decision_support.py:28; EVA_OS/src/quantlab/research/report_gap_tasks.py:22`
- test reference: `EVA_OS/tests/test_report_decision_support.py; EVA_OS/tests/test_report_gap_tasks.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-009`
- parameter_ids: `PARAM-106..PARAM-116`

### MOD-010 Market Hotspot Heat and Evidence Gate

- fact_level: EXTRACTED
- kind: market heat scoring and evidence gate model
- purpose: Compute cross-asset heat scores, stabilize heat history, classify hotspot states and gate hotspot evidence quality.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/analysis/market_hotspots.py:14; EVA_OS/src/quantlab/analysis/market_hotspots.py:831`
- test reference: `EVA_OS/tests/test_market_hotspots.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-010`
- parameter_ids: `PARAM-117..PARAM-142`

### MOD-011 Company CashFlow Command

- fact_level: EXTRACTED
- kind: business cashflow calculation and gate model
- purpose: Count reviewed evidence-backed cashflow entries, compute balance, inflow, outflow, net cashflow, daily burn, runway and runtime gates.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/business/cashflow.py:118`
- test reference: `EVA_OS/tests/test_cashflow_command.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-011`
- parameter_ids: `PARAM-143..PARAM-149`

### MOD-012 Consumption Guard

- fact_level: EXTRACTED
- kind: behavioral spending risk score and gate model
- purpose: Normalize reviewed consumption events, score impulse/regret/necessity risk, compute pressure and produce guard/runtime status.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/consumption/guard.py:103; EVA_OS/src/quantlab/consumption/guard.py:532`
- test reference: `EVA_OS/tests/test_consumption_guard.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-012`
- parameter_ids: `PARAM-150..PARAM-159`

### MOD-013 Policy Intelligence Radar

- fact_level: EXTRACTED
- kind: policy opportunity weighted scoring and gate model
- purpose: Score policy opportunities by authority, relevance, urgency and feasibility, enforce authoritative evidence gates and produce action queues.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/policy/radar.py:109; EVA_OS/src/quantlab/policy/radar.py:351`
- test reference: `EVA_OS/tests/test_policy_radar.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-013`
- parameter_ids: `PARAM-160..PARAM-167`

### MOD-014 Token ROI Ledger

- fact_level: EXTRACTED
- kind: value accounting and ROI gate model
- purpose: Collect artifact/manual value evidence, prevent fabricated financial value and compute reviewed Token ROI only when costs and benefits are supplied.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/value/token_roi.py:33`
- test reference: `EVA_OS/tests/test_token_roi_ledger.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-014`
- parameter_ids: `PARAM-168..PARAM-173`

### MOD-015 Custom Strategy Template and Readiness Gate

- fact_level: EXTRACTED
- kind: strategy profile/code/smoke/approval gate
- purpose: Score custom strategy code/profile readiness, smoke-test signal frames and gate approval status before research use.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/strategies/templates.py:136; EVA_OS/src/quantlab/strategies/templates.py:257`
- test reference: `EVA_OS/tests/test_strategy_templates.py; EVA_OS/tests/test_strategy_profiles.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-015`
- parameter_ids: `PARAM-174..PARAM-180`

### MOD-016 Development Readiness Gate

- fact_level: EXTRACTED
- kind: lightweight syntax/runtime/cache/git readiness gate
- purpose: Check required launch scripts, shell/Python syntax, runtime status, cache dry-run, git status and excluded heavy-gate policy.
- owner: EVA_OS governance baseline
- status: active
- model_version: 0.0.0-provisional
- implementation reference: `EVA_OS/src/quantlab/system/dev_readiness.py:16`
- test reference: `EVA_OS/tests/test_dev_readiness.py`
- inputs: implementation-specific local data frames, JSON files, command payloads, strategy parameters or report metadata
- outputs: research-only signals, scores, statuses, gates, action queues or metrics; no live order output
- use cases: research validation, evidence review, backtesting, reporting and local governance
- non-use cases: live trading, real orders, bank/payment/government portal actions, legal/tax/financial advice automation
- formula_id: `FORM-016`
- parameter_ids: `PARAM-181..PARAM-189`

## B. Assumptions

### ASM-001
- fact_level: EXTRACTED
- assumption: EVA_OS and QuantLab are research, validation, backtesting, reporting and evidence systems only; no live trading, no real orders, and no broker password storage are permitted.
- why_needed: All scoring and gate models must preserve the safety boundary.
- evidence/source: `EVA_OS/README.md:9; EVA_OS/AGENTS.md:9`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-002
- fact_level: EXTRACTED
- assumption: Research outputs may inform real-world trading decisions, so every promoted result requires traceable data quality, cross-source validation, cost assumptions and risk gate status.
- why_needed: Prevents unverified research artifacts from becoming decision evidence.
- evidence/source: `EVA_OS/README.md:13; EVA_OS/README.md:134`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-003
- fact_level: EXTRACTED
- assumption: Built-in strategies are approved for research use only; parameter or formula changes require report review and governance update.
- why_needed: Strategy signals are research models, not autonomous trading permissions.
- evidence/source: `EVA_OS/src/quantlab/strategies/profiles.py:322; EVA_OS/src/quantlab/approvals/registry.py:46`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-004
- fact_level: EXTRACTED
- assumption: Only reviewed records with evidence are counted in cashflow and consumption guard totals.
- why_needed: Business calculations must not treat unreviewed local notes as verified facts.
- evidence/source: `EVA_OS/src/quantlab/business/cashflow.py:144; EVA_OS/src/quantlab/consumption/guard.py:144`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-005
- fact_level: EXTRACTED
- assumption: Policy opportunities require reviewed authoritative evidence before Actionable status.
- why_needed: Policy radar must avoid turning news/manual notes into compliance or subsidy conclusions.
- evidence/source: `EVA_OS/src/quantlab/policy/radar.py:137; EVA_OS/src/quantlab/policy/radar.py:499`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-006
- fact_level: EXTRACTED
- assumption: Historical Git path commits are reconstructed events only and are not counted as confirmed iterations.
- why_needed: Governance must not invent development iteration count from commit count.
- evidence/source: `AGENTS.md; EVA_OS/docs/governance/DEVELOPMENT_LEDGER.md`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

### ASM-007
- fact_level: EXTRACTED
- assumption: Provider sample data and cached hotspot rows are demonstration or derived evidence and do not prove market conclusions without fresh data checks.
- why_needed: Hotspot and data validation gates must preserve data provenance limits.
- evidence/source: `EVA_OS/src/quantlab/analysis/market_hotspots.py:551; EVA_OS/src/quantlab/data/quality.py:34`
- scope: EVA_OS/QuantLab current governance baseline
- impact_if_violated: research artifacts could be over-promoted or used outside verified boundary
- falsification/validation: focused tests, code inspection, evidence gates and governance tasks
- status: active

## C. Functions And Formulas

### FORM-001 (MOD-001)
- fact_level: EXTRACTED
- precise algorithm: Strategy rules: MA target=1 if SMA(short)>SMA(long) else 0 or -1 if long_only=false; RSI invest after RSI<entry until RSI>exit; Bollinger invest when z<=-num_std until z>=exit_z; Breakout invest after close>prior rolling_high until close<prior rolling_low; Momentum select top_n by pct_change(lookback) and equal weight; Alipay buy floor(abs(daily_return)*buy_base_amount), sell by highest return threshold; Enhanced Alipay modifies buy amount by oversold/weak/trend multipliers and max_position_weight cap.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/strategies/trend/ma_crossover.py:1; EVA_OS/src/quantlab/strategies/behavioral/alipay.py:11; EVA_OS/src/quantlab/strategies/profiles.py:322`
- tests: `EVA_OS/tests/test_backtest.py; EVA_OS/tests/test_alipay_strategy.py; EVA_OS/tests/test_strategy_profiles.py`

### FORM-002 (MOD-002)
- fact_level: EXTRACTED
- precise algorithm: Target-weight path executes prior-bar target_weight at next open; slip_price=open*(1+side*(slippage_bps+market_impact_bps)/10000); commission=max(abs(notional)*commission_rate,min_commission); equity=cash+quantity*close; total_return=end_equity/initial_cash-1; annualized=(1+total_return)^(annualization/periods)-1; sharpe=mean_return*annualization/volatility; cost_total=sum(execution_cost).
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/backtest/engine.py:13; EVA_OS/src/quantlab/backtest/metrics.py:22`
- tests: `EVA_OS/tests/test_backtest.py; EVA_OS/tests/test_alipay_strategy.py`

### FORM-003 (MOD-003)
- fact_level: EXTRACTED
- precise algorithm: score starts 0; missing data quality +2; bad data quality +3; total_return<=0 +3; max_drawdown<limit +3; cost_ratio>max_cost_ratio +2; fragile stability +2; failed train-test +3 or watch +1; failed walk-forward +6 or watch +2; missing evidence forces NeedsMoreEvidence; otherwise score>=6 DoNotUse, score>=2 WatchOnly, else ContinueResearch.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/risk/gates.py:16`
- tests: `EVA_OS/tests/test_risk_gates.py`

### FORM-004 (MOD-004)
- fact_level: EXTRACTED
- precise algorithm: dimension scores are clamped 0..10; overall score=round(mean(dimension_scores)*10). Status: missing evidence -> NeedsMoreEvidence; risk_gate DoNotUse -> DoNotUse; score>=80 ContinueResearch; >=60 WatchOnly; >=40 NeedsMoreEvidence; else DoNotUse.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/risk/decision_quality.py:36`
- tests: `EVA_OS/tests/test_decision_quality.py`

### FORM-005 (MOD-005)
- fact_level: EXTRACTED
- precise algorithm: Data quality status Pass when required datetime/open/high/low/close/volume have zero missing values and zero duplicate datetimes, else Review; checksum=sha256(sorted required columns CSV). Cross-source close_diff_pct=(max_close-min_close)/mean_close; status Pass if max_diff<=tolerance_pct, Review otherwise; fewer than two provider frames yields InsufficientData.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/data/quality.py:34; EVA_OS/src/quantlab/data/validation.py:34`
- tests: `EVA_OS/tests/test_data_quality.py; EVA_OS/tests/test_validation_execution.py`

### FORM-006 (MOD-006)
- fact_level: EXTRACTED
- precise algorithm: priority_score=clamp(20+status_score+gap_score+foundational_bonus+report_gap_bonus+source_report_bonus+symbol_market_bonus-blocker_penalties+recency_score,0,100). Execution supports CrossSourceValidation only; unsupported/missing inputs/fewer than two providers return Blocked and NeedsMoreEvidence.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/research/validation_priority.py:52; EVA_OS/src/quantlab/research/validation_execution.py:37`
- tests: `EVA_OS/tests/test_validation_priority.py; EVA_OS/tests/test_validation_execution.py`

### FORM-007 (MOD-007)
- fact_level: EXTRACTED
- precise algorithm: Each inspected artifact receives trust_status; audit_status=Blocked if rejected_count>0, Review if review_count>0, else Pass. REJECTED maps Reject, NEEDS_REVIEW/PARSED_CANDIDATE/RAW_IMPORTED map Watch, ARCHIVED maps Observe, otherwise Actionable.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/system/data_trust.py:48`
- tests: `EVA_OS/tests/test_data_trust_audit.py`

### FORM-008 (MOD-008)
- fact_level: EXTRACTED
- precise algorithm: Integration status Fail if any layer Fail, Review if any layer Review, else Pass. Daily readiness Blocked if any core gate Fail/Blocked, NeedsReview if any gate not Pass, else ReadyForResearch. Command center Blocked if daily readiness blocked or integration fail or business subsystem fail; NeedsReview for non-ready gaps; else ReadyForResearch.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/system/integration_audit.py:27; EVA_OS/src/quantlab/system/daily_readiness.py:16; EVA_OS/src/quantlab/executive/command_center.py:208`
- tests: `EVA_OS/tests/test_integration_audit.py; EVA_OS/tests/test_daily_readiness.py; EVA_OS/tests/test_command_center.py`

### FORM-009 (MOD-009)
- fact_level: EXTRACTED
- precise algorithm: Evidence score starts 0: schema +20, linked Word report +10, data quality pass/info +20 or present-but-not-pass +8, cross validation pass/info +20 or present-but-not-pass +8, risk status +15, decision quality status +15, minus min(30,3*missing_count), clamped 0..100. Readiness follows DoNotUse first, then missing evidence, NeedsMoreEvidence, WatchOnly, ContinueResearch.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/reports/decision_support.py:28; EVA_OS/src/quantlab/research/report_gap_tasks.py:22`
- tests: `EVA_OS/tests/test_report_decision_support.py; EVA_OS/tests/test_report_gap_tasks.py`

### FORM-010 (MOD-010)
- fact_level: EXTRACTED
- precise algorithm: Hotspot raw score base 50 plus clipped one/five/twenty-step return, RSI, volatility penalty and drawdown terms; volatility symbols invert return terms. Stable heat applies EMA alpha=2/(span+1) with max per-slice step cap. State thresholds: >=72 strong diffusion, >=58 locally strong, >=43 neutral, >=28 locally weak, else risk cooling. Evidence gates enforce source, coverage, failure rate, sample length, slice count, cadence, freshness and concentration.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/analysis/market_hotspots.py:14; EVA_OS/src/quantlab/analysis/market_hotspots.py:831`
- tests: `EVA_OS/tests/test_market_hotspots.py`

### FORM-011 (MOD-011)
- fact_level: EXTRACTED
- precise algorithm: Only Reviewed+Pass entries count. Window inflow/outflow are sums by direction; net_cashflow=inflow-outflow; daily_burn=outflow/lookback_days if outflow>0 else 0; runway_days=latest_balance/daily_burn if available. Status MissingBalance, NeedsEvidence, Critical if runway<14, Watch if runway<30, NeedsReview if net<0, StableWithPendingReview if pending, else Stable.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/business/cashflow.py:118`
- tests: `EVA_OS/tests/test_cashflow_command.py`

### FORM-012 (MOD-012)
- fact_level: EXTRACTED
- precise algorithm: risk_score=clip(impulse_score*0.45 + regret_score*0.25 + (100-necessity_score)*0.20 + (0 if planned else 10),0,100). HighImpulse if event_type Impulse or score>=70, Watch if score>=40 else Controlled. Guard MissingConsumptionEvidence if no events, NeedsEvidence if reviewed missing evidence, StopBleeding if high_risk_count>=3 or pressure>1.0, Watch if high risk or pressure>0.6, StableWithPendingReview if pending, else Stable.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/consumption/guard.py:103; EVA_OS/src/quantlab/consumption/guard.py:532`
- tests: `EVA_OS/tests/test_consumption_guard.py`

### FORM-013 (MOD-013)
- fact_level: EXTRACTED
- precise algorithm: impact_score=authority*0.30+relevance*0.30+urgency*0.20+feasibility*0.20. Reviewed authoritative evidence and impact>=70 -> Actionable; impact>=50 -> Watch; missing/non-authoritative evidence -> NeedsEvidence; pending review -> PendingReview; no records -> MissingPolicyEvidence.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/policy/radar.py:109; EVA_OS/src/quantlab/policy/radar.py:351`
- tests: `EVA_OS/tests/test_policy_radar.py`

### FORM-014 (MOD-014)
- fact_level: EXTRACTED
- precise algorithm: manual value benefit=revenue_generated+cost_saved+loss_avoided+asset_reuse_value; cost=ai_cost+human_time_cost; roi_score=(benefit-cost)/cost when cost>0 else null. Quantified only when review_status Reviewed and a real financial field is supplied; aggregate ROI uses reviewed totals only; no fabricated values.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/value/token_roi.py:33`
- tests: `EVA_OS/tests/test_token_roi_ledger.py`

### FORM-015 (MOD-015)
- fact_level: EXTRACTED
- precise algorithm: Code quality score=round(passed_checks/8*100); CodeReadyForReview if no findings. SmokePass when signal frame exists, has required columns and target_weight in [-1,1]. Readiness ApprovedForResearch only when profile ReadyForReview, code CodeReadyForReview, smoke SmokePass and approval Approved; otherwise ReadyForReview or NotReady.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/strategies/templates.py:136; EVA_OS/src/quantlab/strategies/templates.py:257`
- tests: `EVA_OS/tests/test_strategy_templates.py; EVA_OS/tests/test_strategy_profiles.py`

### FORM-016 (MOD-016)
- fact_level: EXTRACTED
- precise algorithm: Dev readiness checks required executable bits, zsh -n, ast.parse, status script, cache dry-run, git status and heavy-gate policy. status=Pass if fail count is 0 else Blocked. Dirty worktree is recorded but not failure; heavy release gates, market refresh, browser automation and broker/order flow are excluded by default.
- variables: see `formula_registry.yaml` for machine-readable variable rows.
- data types and units: mixed floats, ints, booleans, strings, data frames and local JSON/CSV paths as implemented.
- input domain: valid local project inputs satisfying code checks; unsupported/missing evidence is downgraded.
- output range: status enum, score, metric, action queue or research-only signal; never live execution.
- normalization: as implemented by code; clamping and status thresholds are in `parameter_registry.csv`.
- constraints: research-only boundary, no fabricated pass, fail closed on missing evidence.
- missing data handling: Review, Blocked, NeedsMoreEvidence, Missing, empty output, or ValueError according to code.
- boundary conditions/fallback: empty frames, corrupt JSON, insufficient providers and missing evidence block promotion.
- implementation: `EVA_OS/src/quantlab/system/dev_readiness.py:16`
- tests: `EVA_OS/tests/test_dev_readiness.py`

## D. Parameters

Machine source of truth: `parameter_registry.csv`. Defaults, priors and active values are separated. UNKNOWN calibration/source rationale is linked to `TASK-EVA-B-*` tasks, not written as active evidence.

## E. Methodology

EVA_OS currently uses deterministic rules, scorecards, local evidence gates, backtest metrics and heuristic scoring. The method is pragmatic and auditable, but not statistically calibrated unless a future task supplies empirical calibration. Alternatives include learned ranking models, Bayesian calibration, formal portfolio optimization and external experiment tracking; those are not active in this baseline.

## F. Strategy Logic

Signals form from strategy rules, data-quality checks, validation queues, report metadata, cashflow/consumption/policy records and runtime audits. Gates filter missing evidence, insufficient provider coverage, corrupt files, high drawdown/cost risk and unsupported external execution. Score/status outputs map to research actions only. Fallback is fail-closed: Blocked, NeedsMoreEvidence, WatchOnly, DoNotUse, Review, Missing or zero/empty output.

## G. Validation

- metrics: validator errors/warnings, focused pytest results, code compile checks, governance traceability completeness.
- baseline: current extracted implementation at commit 9516776 before this governance-only run.
- dataset/fixture: project test fixtures and temporary pytest fixtures only; no large raw data read.
- current result: PENDING until P12 commands are run in this task.
- uncovered scenarios: full macOS release acceptance, live provider data refresh, external system availability and empirical calibration are not covered by this governance-only baseline.
- release gate: EVA_OS may move to required only after `python3 scripts/validate_project_governance.py --project EVA_OS` and focused tests pass.
