# FIFA Model Specification

fact_level: EXTRACTED
model_count: 11
formula_count: 11
parameter_count: 118

This document is the human-readable specification. Machine facts are maintained in:

- `model_registry.yaml`
- `formula_registry.yaml`
- `parameter_registry.csv`
- `TRACEABILITY_MATRIX.csv`

The original governance baseline did not change runtime behavior. Other8 S3PDT02 changes only the default output failure contract: parse or validation/automation gate failure now fails closed and does not publish recommendation, report, or baseline success deliverables. No probability scoring, stake, refresh, provider, browser, safety scan, TAB access, Bet Slip, wagering, or betting-value behavior is approved by that change.

## A. Model Overview

| Model ID | Name | Kind | Status | Version | Implementation |
| --- | --- | --- | --- | --- | --- |
| MOD-001 | Decimal Odds Validation and No-vig Probability Transform | deterministic validation and probability transform | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/odds.py` |
| MOD-002 | Market Probability, Poisson xG, Candidate Score and Stake Gate | heuristic scoring and deterministic gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/model.py` |
| MOD-003 | Bankroll Plan and Time-adjusted Stake Allocation | risk allocation heuristic | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/bankroll.py` |
| MOD-004 | Recommendation Model Consensus Enrichment | model-comparison routing and explanation rule | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/recommendations.py` |
| MOD-005 | Raw Refresh Health and Access-policy Fail-closed Gate | deterministic safety gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/raw_refresh.py` |
| MOD-006 | Live Board Discovery and Unavailable Review Queue | deterministic coverage and routing gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/live_board_discovery.py` |
| MOD-007 | Public Artifact and Private-data Safety Scanner | deterministic content safety gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/safety.py` |
| MOD-008 | Provider Coverage, KPI, Credit, and Alternate-market Plan | coverage scoring and operational decision gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/provider_kpi.py`, `provider_alternate_plan.py` |
| MOD-009 | Manual Team Total Verification, Hash Gate, and Overlay Publish Preflight | manual verification and deterministic publish gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/provider_manual_verification.py` |
| MOD-010 | Automation Readiness and Research-only Candidate Gate | release-readiness and automation authorization gate | active | 0.0.0-provisional | `FIFA/tab-research-pipeline/tab_research/automation_readiness.py`, `automation_candidate.py` |
| MOD-011 | Legacy Rules Softmax Football Prediction MVP | deprecated explainable softmax prediction model | deprecated | rules-v1.0.0 | `FIFA/legacy/fifa-analysis-system/app/services.py` |

### Use and Non-use

The active models support read-only research reports, dashboard diagnostics, provider/manual verification, public artifact safety, and automation readiness checks. They must not be used to place bets, click odds, mutate Bet Slip, bypass TAB access restrictions, or present guaranteed-profit claims.

MOD-011 is preserved as an implemented legacy model, but it is not the active TAB research execution path.

## B. Assumptions

Assumptions are canonical in `model_registry.yaml`.

| Assumption ID | Summary | Status | Evidence |
| --- | --- | --- | --- |
| ASM-001 | TAB/public odds snapshots are read-only research inputs and do not authorize automated wagering. | active | `FIFA/README.md`, `FIFA/AGENTS.md` |
| ASM-002 | Decimal odds must be finite numeric values greater than 1.0. | active | `odds.py:12`, `tests/test_pipeline.py:1013` |
| ASM-003 | Candidate edges are heuristic research signals requiring curated support or manual review. | active | `model.py:25`, `model.py:143` |
| ASM-004 | Execution stake remains AUD 0 when formal raw, private-position, or manual approval gates are blocked. | active | `provider_manual_verification.py:502`, `automation_candidate.py:169` |
| ASM-005 | Public artifacts must not expose account, session, private position, local private path, or TAB UI sensitive markers. | active | `safety.py:9`, `safety.py:128` |
| ASM-006 | Provider coverage and credit policies are operational gates, not proof of value or profitability. | active | `provider_kpi.py:98`, `provider_alternate_plan.py:556` |
| ASM-007 | Legacy softmax prediction MVP is implemented under `legacy` and not active for TAB execution. | active | `legacy/fifa-analysis-system/README.md:140` |

## C. Functions and Formulas

Canonical formulas are in `formula_registry.yaml`.

| Formula ID | Model ID | Precise Definition | Missing Data and Fallback |
| --- | --- | --- | --- |
| FORM-001 | MOD-001 | Validate decimal odds, compute `1/odds`, and normalize inverse odds by total inverse odds. | Invalid odds return `None` or raise `ValueError`; no numeric fallback. |
| FORM-002 | MOD-002 | Estimate total goals and xG from market probabilities, build Poisson score probabilities, calculate breakeven, edge, EV, and stake gate decisions. | Invalid odds fail closed; unsupported/uncurated selections become zero-stake watch or reject. |
| FORM-003 | MOD-003 | Calculate uncommitted budgets, current-window exposure target, EV-weighted stake allocation, rounding, rebalance, and cap. | Missing position fields fall back to 0; allocation returns zero stakes if target cannot allocate. |
| FORM-004 | MOD-004 | Map selection to probability key, collect three model-source probabilities, compare consensus alignment, and append Chinese divergence summary. | Unmapped pairs return empty key but still report available consensus. |
| FORM-005 | MOD-005 | Aggregate raw refresh blocker codes and access-policy diagnostics; block automated public raw refresh on `ai_controlled_access_rejected`; S3PDT02 also makes blocked default exports publish explicit failed-closed evidence instead of fake success deliverables. | Missing raw/driver or access denied adds blockers and safe recovery text; parse or validation failure publishes no recommendation/report/baseline success deliverables unless explicit legacy mode is requested. |
| FORM-006 | MOD-006 | Compare expected TAB FIFA boards with observed live navigation and route missing boards to retry/unavailable queues. | Discovery failure blocks executable current-board use. |
| FORM-007 | MOD-007 | Scan public/private artifacts for sensitive markers, private fields, unsafe paths, missing artifacts, and permission issues. | Missing/unreadable artifacts are issues; readiness requires zero issues. |
| FORM-008 | MOD-008 | Score provider market coverage, credit runway, alternate-market queues, and operational routing. | Missing credit ratio becomes watch; zero or low-yield Team Total routes to manual/official path. |
| FORM-009 | MOD-009 | Validate manual Team Total rows, require Over/Under complete pairs, canonicalize rows, SHA256 hash, and require matching approval fields. | Missing import/signature waits; invalid rows block; formal publish remains false. |
| FORM-010 | MOD-010 | Combine latest commit, raw, safety, artifact, report index, preflight, private snapshot, and user authorization gates into automation status. | Missing gates become blockers; recurring automation stays review-only. |
| FORM-011 | MOD-011 | Deprecated softmax model over legacy home/draw/away scores and backtest metrics. | Neutral missing stats plus warnings; not active for TAB execution. |

Variable definitions, units, input domains, constraints, output ranges, normalization, boundary conditions, code refs, and test refs are machine-recorded in `formula_registry.yaml`.

## D. Parameters

Canonical parameter inventory is `parameter_registry.csv`.

S3PDT02 adds `PARAM-118` for the explicit legacy blocked-export flag. The active default is `false`, so blocked default exports fail closed.

The baseline separates:

- Default value: code fallback or literal default.
- Initial/prior value: initial code-defined value identified in the current implementation.
- Active value: value currently used by the code or configuration.
- Calibration method: evidence-based calibration if present, otherwise `UNKNOWN` and linked to an open task in `unknown_task_ids`.

Material parameter groups:

- `PARAM-001..PARAM-004`: odds parsing and no-vig transform.
- `PARAM-005..PARAM-030`: xG, Poisson, EV/edge, quality and curation gates.
- `PARAM-031..PARAM-043`: bankroll, target exposure, allocation, rounding, and cap rules.
- `PARAM-044..PARAM-051`: recommendation model-comparison source and routing labels.
- `PARAM-052..PARAM-059`: raw refresh access and fail-closed rules.
- `PARAM-060..PARAM-063`: live-board discovery routing rules.
- `PARAM-064..PARAM-068`: public/private safety marker and issue thresholds.
- `PARAM-069..PARAM-085`: provider coverage, KPI, credit, and alternate-market routing.
- `PARAM-086..PARAM-098`: manual Team Total import, hash, signature, and publish-lock rules.
- `PARAM-099..PARAM-108`: automation candidate and readiness gates.
- `PARAM-109..PARAM-117`: deprecated legacy softmax weights.

Open parameter evidence tasks:

- `TASK-FIFA-B-001`: calibration evidence for heuristic thresholds and gate ratios.
- `TASK-FIFA-B-002`: source rationale for curation maps, marker lists, expected artifacts, and manual required fields.

## E. Methodology

The active methodology is deterministic and safety-gated:

- Use validated decimal odds and no-vig transforms before probability or EV calculations.
- Use market-derived probabilities plus conservative xG/Poisson and curated overlays for research candidates.
- Use hard quality gates and curated support before any candidate can receive a research stake unit.
- Use bankroll caps and time-adjusted allocation to prevent excessive exposure in the research output.
- Use provider coverage, credit, manual verification, and hash/signature gates before formal publish.
- Use public artifact and private-output safety checks before any public-facing output is considered ready.

Alternatives explicitly not active:

- Automated betting or Bet Slip interaction.
- Browser stealth, CAPTCHA bypass, fingerprint spoofing, or headed fallback for blocked public raw.
- Treating provider coverage as a guarantee of model quality or profitability.
- Using the legacy softmax MVP as the active TAB execution model.

Calibration/backtest evidence:

- Many thresholds are EXTRACTED from code but calibration evidence is not present in the inspected files. These are linked to `TASK-FIFA-B-001`.
- Existing tests validate behavior and gates; they do not prove profitability.

## F. Strategy Logic

Signal formation:

- Odds validation and no-vig probabilities form the probability base.
- Candidate model computes xG, Poisson probabilities, edge, EV, and curated support.
- Recommendation enrichment compares current-market Poisson, goalmodel proxy, and Elo-Dixon-Coles sources.

Gate filtering:

- Quality gates reject invalid odds, unsupported markets, unsupported longshots, and selected mismatch cases.
- Raw/live access gates fail closed on access denied or `ai_controlled_access_rejected`.
- Provider gates pause batch expansion when coverage or credit runway is unsafe.
- Manual hash/signature gates block formal publish until canonical rows and approval fields match.
- Safety gates block public outputs containing private or sensitive markers.

Decision mapping:

- Research candidates may show `small_stake` or `marginal_small_stake`.
- Execution remains AUD 0 when formal, private, or manual gates are blocked.
- Automation remains review-only until explicit authorization and all required gates pass.

Failure behavior:

- Fail closed.
- Preserve the last trusted report pointer.
- Route to official/authorized feed, user export/import, TT-001 manual verification, or research-only diagnostics.

## G. Validation

Current validation commands for this baseline:

- `python scripts/validate_project_governance.py --project FIFA`
- `cd FIFA/tab-research-pipeline && python3 -m py_compile run_daily_report.py scripts/tab_fifa_app_server.py tests/test_pipeline.py`
- `cd FIFA/tab-research-pipeline && bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh`
- `cd FIFA/tab-research-pipeline && node --check scripts/refresh_tab_readonly.mjs`
- `cd FIFA/tab-research-pipeline && node --check scripts/discover_tab_live_boards.mjs`
- `cd FIFA/tab-research-pipeline && python3 -m unittest tests.test_pipeline -q`
- `python scripts/validate_project_governance.py --all`
- `git diff --check`

Current results are recorded in `delivery_tasks.yaml` and will be finalized after this run's validation commands complete.

Release gate:

- `TASK-FIFA-A-001` can be marked completed only after validator and focused checks pass and FIFA `ci_mode` is required.
