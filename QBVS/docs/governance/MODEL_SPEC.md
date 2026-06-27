# PFI Big Data Simulator Model Specification

- project_id: PFI_BIG_DATA_SIMULATOR
- evidence_level: EXTRACTED unless stated otherwise
- model_count: 15
- formula_count: 15
- parameter_count: 213
- machine sources: `model_registry.yaml`, `formula_registry.yaml`, `parameter_registry.csv`, `delivery_tasks.yaml`

## A. Model Overview

### MOD-001 - Behavior Strategy Catalog and Signal Rule Engine

- fact_level: EXTRACTED
- kind: deterministic strategy rule engine
- purpose: Generate behavior strategy specifications and convert OHLCV bars into target weights using dip, trend, sell and risk rules.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/strategies.py:13, PFI/modules/qbvs_lab/qbvs/strategies.py:31, PFI/modules/qbvs_lab/qbvs/strategies.py:77
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002, ASM-003
- formula: FORM-001 - target_weight starts at base_weight; dip rule may set 1.0; trend rule may set 1.0; sell rule multiplies selected targets by 0.85; risk rules cap target to 0.96 or 0.90; final target is forward-filled and clipped to [0,1].
- parameter range: PARAM-001..PARAM-036
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:61, PFI/modules/qbvs_lab/tests/test_core.py:65
- unresolved governance task: TASK-PFI-B-001
### MOD-002 - Technical Indicator Transform Library

- fact_level: EXTRACTED
- kind: technical indicator formula library
- purpose: Compute SMA, RSI, Bollinger bands, MACD and ATR transforms used by strategy rules.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/indicators.py:6, PFI/modules/qbvs_lab/qbvs/indicators.py:10, PFI/modules/qbvs_lab/qbvs/indicators.py:18, PFI/modules/qbvs_lab/qbvs/indicators.py:25, PFI/modules/qbvs_lab/qbvs/indicators.py:35
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-002, ASM-003
- formula: FORM-002 - SMA is rolling mean; RSI=100-100/(1+avg_gain/avg_loss) with neutral fill 50; Bollinger upper/lower=mid +/- num_std*std; MACD=EMA_fast-EMA_slow with signal EMA; ATR is rolling mean true range.
- parameter range: PARAM-037..PARAM-045
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:65
- unresolved governance task: TASK-PFI-B-001
### MOD-003 - Exact Target-Weight Backtest and Metrics Engine

- fact_level: EXTRACTED
- kind: deterministic backtest and performance metric model
- purpose: Normalize OHLCV data, execute shifted target weights with cost/slippage assumptions, compute equity, drawdown and performance metrics.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/backtest.py:11, PFI/modules/qbvs_lab/qbvs/backtest.py:19, PFI/modules/qbvs_lab/qbvs/backtest.py:49, PFI/modules/qbvs_lab/qbvs/backtest.py:134
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002
- formula: FORM-003 - Execution uses previous-day target weight. trade_value=equity_before*target_weight-current_position_value; slip_price=open*(1+side*(slippage_bps+market_impact_bps)/10000); equity=cash+quantity*close; metrics derive total return, annualized return, drawdown, volatility, Sharpe, VaR and CVaR.
- parameter range: PARAM-046..PARAM-066
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:65
- unresolved governance task: TASK-PFI-B-002
### MOD-004 - Buy-Hold Comparison and User-Floor Gate

- fact_level: EXTRACTED
- kind: candidate acceptance gate
- purpose: Compare strategy metrics with buy-and-hold and decide whether user return/drawdown floors are satisfied.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/backtest.py:122, PFI/modules/qbvs_lab/qbvs/backtest.py:163, PFI/modules/qbvs_lab/qbvs/validation.py:133
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-004
- formula: FORM-004 - total_gap=strategy_total_return-buy_hold_total_return; annualized_gap=strategy_annualized_return-buy_hold_annualized_return; drawdown_improvement=strategy_max_drawdown-buy_hold_max_drawdown; passes when gaps meet configured floors.
- parameter range: PARAM-067..PARAM-069
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:76, PFI/modules/qbvs_lab/tests/test_core.py:625
- unresolved governance task: TASK-PFI-B-002
### MOD-005 - Random Path Stress Simulator

- fact_level: EXTRACTED
- kind: stochastic stress path generator
- purpose: Generate synthetic OHLCV paths across bull, bear, sideways, crash, high-vol and rotation regimes for stress testing.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/simulation.py:10, PFI/modules/qbvs_lab/qbvs/simulation.py:17, PFI/modules/qbvs_lab/qbvs/simulation.py:27
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-002, ASM-004
- formula: FORM-005 - For each path choose regime; daily return=normal(mu,sigma)+jump_mask*normal(jump_mu,jump_sigma), clipped to [-0.35,0.35]; close=start_price*exp(cumulative returns); OHLC generated around close/open.
- parameter range: PARAM-070..PARAM-105
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:76, PFI/modules/qbvs_lab/tests/test_core.py:84
- unresolved governance task: TASK-PFI-B-003
### MOD-006 - Universe Validation, Rolling Windows and Summary Ranking

- fact_level: EXTRACTED
- kind: validation orchestration and ranking model
- purpose: Run full, rolling or event-window validation over universes and rank strategy summaries by pass rate and return/drawdown gaps.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/validation.py:33, PFI/modules/qbvs_lab/qbvs/validation.py:88, PFI/modules/qbvs_lab/qbvs/validation.py:103, PFI/modules/qbvs_lab/qbvs/windows.py:19, PFI/modules/qbvs_lab/qbvs/windows.py:56
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002, ASM-004
- formula: FORM-006 - Validation runs each strategy and symbol/window, records metrics and errors, then groups by strategy_id and sorts by pass_rate, avg_annualized_gap, avg_drawdown_improvement and avg_total_gap descending.
- parameter range: PARAM-056..PARAM-110
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:84, PFI/modules/qbvs_lab/tests/test_core.py:95
- unresolved governance task: TASK-PFI-B-002
### MOD-007 - Fast Screening Approximation and Exact Benchmark

- fact_level: EXTRACTED
- kind: vectorized approximation and benchmark model
- purpose: Approximate target-weight returns for large-scale screening, compare against exact backtest, and mark fast candidates as requiring exact validation.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/fast.py:14, PFI/modules/qbvs_lab/qbvs/fast.py:25, PFI/modules/qbvs_lab/qbvs/fast.py:150, PFI/modules/qbvs_lab/qbvs/fast.py:215
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002, ASM-005
- formula: FORM-007 - Fast returns use shifted target_weight*close_return minus turnover*(commission_rate+(slippage_bps+market_impact_bps)/10000), cumprod equity, and same comparison floor; benchmark summary reports abs differences versus exact engine.
- parameter range: PARAM-051..PARAM-113
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:359, PFI/modules/qbvs_lab/tests/test_core.py:418
- unresolved governance task: TASK-PFI-B-004
### MOD-008 - OHLCV Quality and Tradability Classification Gate

- fact_level: EXTRACTED
- kind: data quality score and classification model
- purpose: Score OHLCV data quality, assign grades, infer asset class and infer tradability labels for validation inputs.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/quality.py:12, PFI/modules/qbvs_lab/qbvs/quality.py:28, PFI/modules/qbvs_lab/qbvs/quality.py:94, PFI/modules/qbvs_lab/qbvs/quality.py:111
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-002, ASM-006
- formula: FORM-008 - Quality starts at 100 and subtracts penalties for too few bars, missing close, duplicate datetime, non-positive close, extreme daily return and calendar gaps; score is clamped [0,100] and mapped to grade A/B/C/D/F.
- parameter range: PARAM-114..PARAM-133
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:219, PFI/modules/qbvs_lab/tests/test_core.py:273
- unresolved governance task: TASK-PFI-B-005
### MOD-009 - Resumable Task Manifest and Quality Skip Gate

- fact_level: EXTRACTED
- kind: task hashing, resume and quality gate model
- purpose: Build deterministic task manifests, run/cached/skipped task states, aggregate task results and enforce optional minimum quality score skip logic.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/tasks.py:18, PFI/modules/qbvs_lab/qbvs/tasks.py:110, PFI/modules/qbvs_lab/qbvs/tasks.py:189, PFI/modules/qbvs_lab/qbvs/tasks.py:209, PFI/modules/qbvs_lab/qbvs/tasks.py:269
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002
- formula: FORM-009 - task_id is first 24 hex chars of sha256 over source/window/strategy payload; run_task_manifest returns cached if result exists, skipped_quality if quality score is below minimum and skip flag is enabled, otherwise completed or failed.
- parameter range: PARAM-134..PARAM-142
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:95, PFI/modules/qbvs_lab/tests/test_core.py:273
- unresolved governance task: TASK-PFI-B-005
### MOD-010 - Long-Run Campaign, Budget and Promotion Gate

- fact_level: EXTRACTED
- kind: campaign planning and candidate promotion model
- purpose: Split large manifests, estimate runtime budget, generate manual run commands, verify campaign artifacts, and promote external candidates using floor thresholds.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/campaign.py:18, PFI/modules/qbvs_lab/qbvs/campaign.py:41, PFI/modules/qbvs_lab/qbvs/campaign.py:92, PFI/modules/qbvs_lab/qbvs/campaign.py:139, PFI/modules/qbvs_lab/qbvs/planning.py:9
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-004
- formula: FORM-010 - Campaign splits manifest by chunk_size, estimates total_seconds=tasks*million_test_multiplier*seconds_per_task and wall_seconds=total_seconds/workers, writes manual commands; promotion filters candidate summaries by sample/pass/return/drawdown thresholds.
- parameter range: PARAM-143..PARAM-157
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:219, PFI/modules/qbvs_lab/tests/test_core.py:625
- unresolved governance task: TASK-PFI-B-006
### MOD-011 - Finalist Strategy Selection and Pair Manifest Builder

- fact_level: EXTRACTED
- kind: ranked finalist selection model
- purpose: Filter strategy summaries by sample/pass/return/drawdown thresholds and build ranked finalist cache-pair manifests.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/finalists.py:13, PFI/modules/qbvs_lab/qbvs/finalists.py:22, PFI/modules/qbvs_lab/qbvs/finalists.py:48
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-004
- formula: FORM-011 - Finalists require samples, pass_rate, avg_total_gap, avg_annualized_gap and avg_drawdown_improvement above thresholds; sorted by pass_rate and gaps; top_n assigned finalist_rank and expanded to cache-pair manifest windows.
- parameter range: PARAM-158..PARAM-167
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:912
- unresolved governance task: TASK-PFI-B-006
### MOD-012 - Alipay Fund NAV and Trading Rule Execution Model

- fact_level: EXTRACTED
- kind: fund execution and fee model
- purpose: Normalize Alipay fund NAV CSVs and backtest target weights with subscription/redemption fees, confirmation delays, settlement delays and holding rules.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/datasources.py:63, PFI/modules/qbvs_lab/qbvs/datasources.py:96, PFI/modules/qbvs_lab/qbvs/fund_rules.py:14, PFI/modules/qbvs_lab/qbvs/fund_rules.py:53
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-002
- formula: FORM-012 - Fund buy subscription invests gross_cash/(1+subscription_fee_rate) after buy_confirmation_days; redemptions sell eligible lots with short/long redemption fee, settle cash after sell_cash_delay_days, and compute normal performance metrics plus fee totals.
- parameter range: PARAM-168..PARAM-181
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:572, PFI/modules/qbvs_lab/tests/test_core.py:592, PFI/modules/qbvs_lab/tests/test_core.py:615
- unresolved governance task: TASK-PFI-B-007
### MOD-013 - QuantLab Evidence Bundle, Handshake and ReadOnly Adapter Gate

- fact_level: EXTRACTED
- kind: interoperability contract and artifact validation model
- purpose: Export/verify QuantLab external evidence bundles, verify handshake ACKs, and generate read-only adapter packs with no database/source writes.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/quantlab_bundle.py:19, PFI/modules/qbvs_lab/qbvs/quantlab_bundle.py:27, PFI/modules/qbvs_lab/qbvs/quantlab_bundle.py:73, PFI/modules/qbvs_lab/qbvs/handshake.py:9, PFI/modules/qbvs_lab/qbvs/handshake.py:115, PFI/modules/qbvs_lab/qbvs/quantlab_adapter.py:10, PFI/modules/qbvs_lab/qbvs/quantlab_adapter.py:53
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-005
- formula: FORM-013 - Bundle verification requires manifest/payload/candidate artifacts, schema match, writes_quantlab_database=false, writes_quantlab_source=false, ingestion_mode=external_evidence_only; handshake ACK must match protocol/source/target and accepted=true.
- parameter range: PARAM-182..PARAM-190
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:307, PFI/modules/qbvs_lab/tests/test_core.py:375, PFI/modules/qbvs_lab/tests/test_core.py:681
- unresolved governance task: TASK-PFI-B-008
### MOD-014 - Goal Readiness Audit Scoring Model

- fact_level: EXTRACTED
- kind: goal completion and readiness scorecard
- purpose: Score original strategy-validation goal readiness across scope, user floors, data-provider gates, handshake and scale targets.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/goal_audit.py:17, PFI/modules/qbvs_lab/qbvs/goal_audit.py:26, PFI/modules/qbvs_lab/qbvs/goal_audit.py:82, PFI/modules/qbvs_lab/qbvs/goal_audit.py:248
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-004, ASM-007
- formula: FORM-014 - Goal audit builds requirement items with statuses passed/partial/blocked/missing; readiness_score=sum(status_weight)/item_count where passed=1, partial=0.5, blocked=0.25, missing=0.
- parameter range: PARAM-191..PARAM-200
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:701
- unresolved governance task: TASK-PFI-B-009
### MOD-015 - Universe Seed, Provider Probe and Moomoo Batch Cache Gate

- fact_level: EXTRACTED
- kind: data-source planning and provider readiness model
- purpose: Build/validate tradable-candidate universes, generate cache plans, probe Moomoo/OpenD readiness and record batch cache attempts.
- owner: PFI_BIG_DATA_SIMULATOR governance baseline
- status: active
- model version: 0.0.0-provisional
- implementation reference: PFI/modules/qbvs_lab/qbvs/universe_seed.py:13, PFI/modules/qbvs_lab/qbvs/universe_seed.py:43, PFI/modules/qbvs_lab/qbvs/universe_seed.py:55, PFI/modules/qbvs_lab/qbvs/datasources.py:32, PFI/modules/qbvs_lab/qbvs/moomoo_batch.py:16, PFI/modules/qbvs_lab/qbvs/moomoo_batch.py:31
- inputs: OHLCV, manifests, summaries, configs, provider/bundle payloads as applicable
- outputs: metrics, target weights, candidate states, evidence artifacts, readiness/audit states
- use cases: ReviewOnly strategy validation, stress testing, evidence packaging and governance gates
- non-use cases: live trading, automatic order placement, QuantLab DB/source writes, approved strategy insertion
- assumptions: ASM-001, ASM-006, ASM-007
- formula: FORM-015 - Seed validation requires columns and symbol count, warns on market/asset coverage below thresholds; Moomoo probe is ready only if socket is reachable and futu or moomoo SDK is available; batch cache records success/failure counts without QuantLab writes.
- parameter range: PARAM-201..PARAM-213
- fallback/failure behavior: invalid inputs fail closed through error rows, skipped_quality, invalid artifact, blocked/missing audit item, or review-only state.
- verification: PFI/modules/qbvs_lab/tests/test_core.py:504, PFI/modules/qbvs_lab/tests/test_core.py:772, PFI/modules/qbvs_lab/tests/test_core.py:975
- unresolved governance task: TASK-PFI-B-010

## B. Assumptions

### ASM-001 - ReviewOnly boundary

- fact_level: EXTRACTED
- content: QBVS/PFI_BIG_DATA_SIMULATOR artifacts are external evidence only; they must not write QuantLab source, QuantLab database, approved strategy libraries, or execute live trading.
- why needed: README.md boundary, AGENTS.md, QUANTLAB_INTEGRATION_CONTRACT.json, HANDSHAKE_PROTOCOL.json
- evidence/source: All models in this governance baseline
- scope: If violated, validation outputs could be misused as production trading actions.
- violation impact: Verify bundle/adapter/campaign manifests keep writes_quantlab_database=false and external_evidence_only.
- falsification/validation: active
- status: active

### ASM-002 - OHLCV input adequacy

- fact_level: EXTRACTED
- content: Backtests and validation windows require normalized OHLCV-like bars with datetime and close, at least 30 bars for normalization and longer windows for rolling validation.
- why needed: qbvs/backtest.py normalize_ohlcv and window code
- evidence/source: Backtest, validation, quality and task models
- scope: Insufficient or malformed bars fail validation or return error rows.
- violation impact: Run tests/test_core.py backtest, rolling and quality cases.
- falsification/validation: active
- status: active

### ASM-003 - Deterministic strategy catalog

- fact_level: EXTRACTED
- content: Behavior strategy IDs are deterministic products of enumerated base weights, dip triggers, sell triggers, trend rules and risk rules.
- why needed: qbvs/strategies.py generate_strategy_specs
- evidence/source: Behavior strategy generation and all validation modes
- scope: Changing enumeration changes strategy universe and traceability IDs.
- violation impact: Run test_strategy_factory_has_at_least_200_specs.
- falsification/validation: active
- status: active

### ASM-004 - User acceptance floor

- fact_level: EXTRACTED
- content: User-facing acceptance floor is total-return gap >= -8%, annualized gap >= -3%, and drawdown improvement >= -0.005 versus buy-and-hold.
- why needed: README.md and compare_to_buy_hold/promotion configs
- evidence/source: Candidate selection, bundle export and readiness audit
- scope: Changing thresholds changes external candidate promotion.
- violation impact: Run promotion, bundle and goal audit tests.
- falsification/validation: active
- status: active

### ASM-005 - Fast screening is not final evidence

- fact_level: EXTRACTED
- content: Fast vectorized screening may rank candidates but finalists require exact backtest rerun before approval.
- why needed: README.md fast-screening boundary and quantlab_bundle.py requires_exact_validation
- evidence/source: Fast screening and QuantLab bundle export
- scope: Fast results could be misread as final approval if exact rerun gate is removed.
- violation impact: Run fast bundle exact-required tests.
- falsification/validation: active
- status: active

### ASM-006 - Public data is not tradability proof

- fact_level: EXTRACTED
- content: Yahoo public history and fallback universes are validation inputs, not proof of account-level tradability.
- why needed: README.md, BACKUP_MANIFEST.md, universe_seed.py summaries
- evidence/source: Data-source and universe seed models
- scope: Overclaiming tradability could cause invalid deployment decisions.
- violation impact: Check universe summaries and Moomoo readiness gates.
- falsification/validation: active
- status: active

### ASM-007 - Moomoo/OpenD readiness gate

- fact_level: EXTRACTED
- content: Moomoo history fetch requires reachable OpenD socket and futu/moomoo SDK availability.
- why needed: qbvs/datasources.py probe_moomoo_opend and cache_moomoo_history
- evidence/source: Moomoo cache and goal audit models
- scope: Unavailable provider must block account-level validation claims.
- violation impact: Run datasource probe tests or probe command.
- falsification/validation: active
- status: active

### ASM-008 - Historical iteration count discipline

- fact_level: RECONSTRUCTED
- content: The single scoped git commit for this imported path is reconstructive evidence only, not a confirmed iteration count.
- why needed: git log --max-count=50 -- PFI/modules/qbvs_lab
- evidence/source: Development ledger
- scope: Counting commits as iterations would fabricate development history.
- violation impact: Keep Confirmed iterations separate from reconstructed events.
- falsification/validation: active
- status: active

## C. Functions And Formulas

Formula details are canonical in `formula_registry.yaml`. Conditional branches have been transcribed into exact pseudocode expressions rather than described only as deterministic rules.

## D. Parameters

Parameter defaults, prior/initial values, active values, ranges, source rationale, calibration evidence and code/test refs are canonical in `parameter_registry.csv`. Unknown calibration evidence is linked to blocked B-stage tasks.

## E. Methodology

The project uses deterministic behavior strategy rules, exact target-weight backtesting, stochastic stress scenarios, vectorized fast screening, data quality scorecards, external evidence bundle validation and goal-readiness scorecards. Fast screening is explicitly a candidate narrowing method and does not replace exact validation.

## F. Strategy Logic

Signals form from dip/trend/sell/risk rules; gates filter by OHLCV quality, provider readiness, user floors, exact-rerun requirements, ReviewOnly boundaries and QuantLab handshake validity. Failed gates produce blocked/missing/invalid/skipped states rather than approved strategy writes.

## G. Validation

- validator: `python3 scripts/validate_project_governance.py --project 'PFI/modules/qbvs_lab'`
- focused tests: `PYTHONPATH=. python3 -m pytest tests/test_core.py -q`
- release gate: P13 required promotion only after validator passes and focused test result is recorded.
