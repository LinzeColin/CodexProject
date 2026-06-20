# MODEL_SPEC

Project: `Serenity-Alipay`
Governance spec version: `1.0.0`

machine_summary:

- model_count: 5
- formula_count: 12
- parameter_count: 49

Fact levels follow `docs/governance/STANDARD.md`.

## A. Model Overview

| Model ID | Name | kind | Purpose | Status | Version | Implementation reference |
|---|---|---|---|---|---|---|
| MOD-001 | Candidate scoring and action rule engine | deterministic scoring and hard-gate rule engine | Score fund candidates and derive research action labels | active | serenity-scoring-v1 | `app/core/scoring.py::score_candidate` |
| MOD-002 | Recommendation ranking and Top5 allocation | deterministic ranking and allocation heuristic | Rank eligible candidates, select Top5, compute target weights and deviation actions | active | serenity-ranking-v1 | `app/core/pipeline.py::_ranked_recommendation_rows`, `_target_weights`, `_action_with_deviation` |
| MOD-003 | Metrics and time-window calculation | mathematical return and drawdown calculation | Compute return windows, max drawdown, recovery time, and recent drawdown | active | serenity-metrics-v1 | `app/core/metrics.py` |
| MOD-004 | Comparison and discipline gate engine | deterministic review-trigger rule engine | Detect Top5 drift, score sigma changes, deviations, and overexpansion events | active | serenity-discipline-v1 | `app/core/comparison.py`, `app/core/discipline.py` |
| MOD-005 | Automation time-slot and dry-run safety gate | deterministic schedule and safety gate | Determine due Beijing slots and safe dry-run/mail behavior | active | serenity-scheduler-v1 | `app/scheduler.py`, `app/core/scheduler_runner.py`, `app/core/automation_tick.py` |

### Inputs

- Candidate inputs: `Candidate` fields from `app/adapters/manual_sources.py:9`.
- Fund-rule inputs: `FundRule` fields from `app/adapters/manual_sources.py:34`.
- Price inputs: `PricePoint` daily close rows from `app/adapters/manual_sources.py:64`.
- Runtime defaults: `Settings` from `app/config.py:15`.
- Prior run state: SQLite `run_log`, `score_snapshot`, `recommendation_snapshot`, and `baseline_snapshot`.

### Outputs

- `ScoreResult` fields from `app/core/scoring.py:13`.
- Top5 `recommendation_snapshot` rows from `app/core/pipeline.py:536`.
- `ComparisonSummary` and `DisciplineEvent` from `app/core/comparison.py:16` and `app/core/discipline.py:9`.
- Scheduler action outputs from `app/core/scheduler_runner.py:28`.

### Use Cases

- Research ranking, review queues, reports, local notifications, dry-run automation, and production-readiness evidence.

### Non-Use Cases

- Automatic buying, selling, platform bypass, broker control, or promise of future benchmark outperformance. Evidence: `README.md:20` and `README.md:23`.

## B. Assumptions

| Assumption ID | Statement | Why needed | Evidence | Scope | Violation impact | Verification | Status |
|---|---|---|---|---|---|---|---|
| ASM-001 | Outputs are research and draft notifications, not trades. | Keeps model decisions non-executing. | `README.md:5`, `README.md:20` | All models | Misuse could treat research labels as orders. | Completion audit and no-trade tests. | active |
| ASM-002 | Candidate order carries Serenity priority before score tie-breaks. | Ranking code sorts by candidate_index before score. | `pipeline.py:182`, `tests/test_pipeline_serenity_priority.py:62` | MOD-002 | Higher score could incorrectly override Serenity priority. | Focused ranking tests. | active |
| ASM-003 | Daily close history is sorted and sufficient for returns/drawdown. | Metrics calculate from sorted `PricePoint` rows. | `manual_sources.py:151`, `metrics.py:39` | MOD-003 | Return/MDD windows become invalid. | `tests/test_metrics.py`. | active |
| ASM-004 | Source count, conflicts, fallback, and missing fields proxy evidence confidence. | Scoring uses them directly. | `scoring.py:81`, `scoring.py:110`, `scoring.py:183` | MOD-001 | Weak evidence could become Action-Ready. | `tests/test_scoring.py`. | active |
| ASM-005 | Beijing business-day slots define automation eligibility. | Scheduler gates slots and weekends. | `scheduler.py:8`, `scheduler.py:71` | MOD-005 | Automation could run outside intended window. | `tests/test_timezones.py`, `tests/test_scheduler.py`. | active |
| ASM-006 | Incomplete evidence fails closed. | Gates force Block, Pause New, Manual Review, draft, or dry-run. | `scoring.py:177`, `tests/test_automation_tick.py:8` | All models | Incomplete evidence could become actionable. | Risk-gate and automation tests. | active |

## C. Functions and Formulas

Machine-readable formulas live in `formula_registry.yaml`. Key exact logic:

- FORM-001 return windows: `return_w = close_last / close_start(w) - 1.0`; 1m uses 31 calendar days, 3m uses 93 calendar days, 10d uses 11 price points. Missing start or zero start returns `None`.
- FORM-002 MDD and recovery: track running peak, compute `(peak.close - close) / peak.close`, keep the worst drawdown, and count days from worst trough until later close is at least the prior peak.
- FORM-003 score: `total = data + timeliness + source + return + risk + executable`; component caps are 25, 15, 15, 15, 20, and 10.
- FORM-004 grades: `>=85 Action-Ready`, `>=70 Watch`, `>=55 Manual Review`, otherwise `Block`.
- FORM-005 hard-gate decision table: conservative/excluded blocks; MDD `>=0.40` blocks and clears; recovery `>=365` forces Manual Review or Block; stale days `>2`, conflicts, low source count, fallback, and execution gaps cap or review.
- FORM-006 benchmark wins: strict `>` comparisons across 1m, 3m, and 10d versus Shanghai Composite and S&P 500; denominator is 6.
- FORM-007 ranking: non-Block rows sorted by manual-review flag, candidate priority, descending score, then asset code; limit 5.
- FORM-008 Top5 weights: `0.82^rank_index * (0.85 + 0.15*clamp(score/100,0,1))`, normalize, cap at 0.30, renormalize.
- FORM-009 action mapping: deviation within `<=0.01` maintains; positive deviation increases or pauses; negative deviation reduces.
- FORM-010 comparison triggers: alert on Top5 change rate `>0.20`, any new asset, at least 2 replacements, or score sigma `>1.0`.
- FORM-011 discipline triggers: absolute deviation `>0.01` and overexpansion `consecutive > 2`.
- FORM-012 scheduler gate: Beijing business day, slot tolerance `<=3` minutes, and dry-run forced when preflight blocks.

Variables, units, input domains, output ranges, boundary inclusivity, missing
policy, fallback behavior, code refs, and test refs are specified per formula in
`formula_registry.yaml`.

## D. Parameters

The canonical parameter catalog is `parameter_registry.csv`.

Parameter classes:

- Metric windows: PARAM-001 through PARAM-004.
- Scoring and hard-gate constants: PARAM-005 through PARAM-025.
- Ranking and Top5 allocation constants: PARAM-026 through PARAM-033.
- Comparison and discipline constants: PARAM-034 through PARAM-042.
- Scheduler and safety defaults: PARAM-043 through PARAM-049.

No runtime parameter value is changed by this governance baseline. Non-weight
parameters explicitly use `weight=NOT_APPLICABLE`. Score component point caps use
`weight_group=WG-SCORE-POINTS` with target `100.0` and tolerance `0.0001`.

## E. Methodology

- Current method: deterministic scoring and rule gates extracted from code and tests.
- Why this method: project README and HANDOFF describe local-first, auditable, fail-closed research automation with no automatic trading.
- Objective: produce explainable research ranking, review labels, and dry-run-safe recommendations.
- Calibration method: current constants are EXTRACTED from code. Empirical calibration evidence is UNKNOWN and linked to `TASK-B-001`.
- Training/backtest: no ML training pipeline is implemented in the inspected evidence. NOT_APPLICABLE for current active models.
- Baseline: current manual CSV and SQLite run evidence support research baseline behavior; exact baseline quality evaluation remains task-linked.
- Data split and out-of-sample: UNKNOWN for empirical model quality; linked to `TASK-B-001`.
- Sensitivity analysis: focused unit tests cover boundary behavior; full parameter sensitivity is UNKNOWN and linked to `TASK-B-002`.
- Known bias: manual candidate ordering is a primary ranking signal, so selection depends on upstream curated candidate order.

## F. Strategy Logic

- Signal formation: candidate evidence, source count, fee/status completeness, price returns, drawdown, recovery, and benchmark wins feed `ScoreResult`.
- Gate filtering: `Block` candidates are excluded from Top5 ranking; hard MDD and recovery gates override numeric score.
- Score-to-decision mapping: grade and deviation produce Maintain, Increase, Pause New, Reduce, Clear, or Manual Review.
- Risk limits: MDD `>=40%`, recovery `>=365 days`, per-asset target cap `30%`, deviation trigger `1%`, and dry-run/mail-disabled defaults.
- Fallback: missing values reduce score, create missing-data logs, cap grade, or force review. Aggregated fallback cannot make a candidate Action-Ready.
- Stop conditions: no due Beijing slot, weekend, duplicate slot, preflight blocker, production evidence blocker, hard risk gate, or missing execution evidence.
- Human approval: Manual Review queue and notification drafts are the approval points; no code path places trades.
- Failure behavior: degrade to draft, manual review, Pause New, Block, no_due_slot, non_business_day, or dry-run.

## G. Validation

Focused validation evidence:

- `tests/test_scoring.py`: MDD block, recovery downgrade, aggregated fallback cap, platform trade status advisory-only.
- `tests/test_pipeline_serenity_priority.py`: Serenity priority before score, manual-review demotion, target weight normalization and tie-breaks.
- `tests/test_risk_gate_regression.py`: repeatable MDD and recovery hard-gate regression evidence.
- `tests/test_metrics.py`: required return windows are `None` when uncovered and present when covered.
- `tests/test_discipline.py`: deviation `>1%` alerts and exactly `1%` maintains.
- `tests/test_timezones.py` and `tests/test_scheduler.py`: Beijing slot schedule and weekend gating.

Release gate for this baseline:

- `python scripts/validate_project_governance.py --project Serenity-Alipay`
- Focused Serenity tests listed in `DELIVERY_PLAN.md`
- `git diff --check`

Uncovered scenarios:

- Empirical calibration and out-of-sample performance evidence are UNKNOWN and linked to `TASK-B-001`.
- Full sensitivity analysis for all active parameters is UNKNOWN and linked to `TASK-B-002`.
