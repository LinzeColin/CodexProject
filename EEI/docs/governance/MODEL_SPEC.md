# MODEL_SPEC

Project: `EEI`
Fact level: `EXTRACTED` for legacy CSV/config values; `RECONSTRUCTED` where the baseline maps legacy IDs into CodexProject governance IDs.
Governance spec version: `1.0.0`

## Canonical Sources

- Model registry: `docs/governance/model_registry.yaml`
- Formula registry: `docs/governance/formula_registry.yaml`
- Parameter registry: `docs/governance/parameter_registry.csv`
- Legacy evidence inputs: `data/model_registry.csv`, `data/formula_registry.csv`, `data/parameter_catalog.csv`, `config/model_profiles/balanced-v2.json`, `config/thresholds/default-v2.json`, `config/model_runtime_defaults.yaml`

## Model Inventory Summary

machine_summary:

- model_count: 12
- formula_count: 12
- parameter_count: 92

The counts above are generated from the canonical machine registries in this directory. Legacy Markdown files are indexes and must not be edited as independent count sources.

## Current Audit Note

- 2026-06-22 T1304/A206 closure changes scheduler, retry and dead-letter delivery status only; no scoring model, graph traversal formula, extraction formula, formula weight or runtime model behavior changed.
- 2026-06-22 T1301/A202 plus T1309/A210 release-decision bundle adds governance contract parameter `PARAM-063` for `CONTRACT_SCHEMA_VERSION`; no scoring model, graph traversal formula, extraction formula, formula weight or runtime threshold changed.
- 2026-06-22 T904/A026/A027 gold-quality evaluation adds governance gate parameters `PARAM-064` through `PARAM-068` for minimum gold-set sample count, precision and source coverage; no scoring model, graph traversal formula, extraction formula or formula weight changed.
- 2026-06-22 T1301/A202 signed-bundle publication binding makes the production owner sign-off publication path require a signed A202/A210 release decision bundle and stores bundle/signature hashes in the evidence chain; no scoring model, graph traversal formula, extraction formula, formula weight or threshold value changed.
- 2026-06-23 T1301/A202 source-withdrawal and counter-evidence fail-closed rehearsal adds publication-control checks for disputed raw source snapshots, disputed ingestion evidence-chain rows and unreviewed evidence-chain counter-evidence; no scoring model, graph traversal formula, extraction formula, formula weight or threshold value changed.
- 2026-06-23 T1303/A204-A205 release-manager activation preflight aggregates existing A202/A026/A027/A209/A210 release evidence and fails closed while external gates are missing; no scoring model, graph traversal formula, extraction formula, formula weight or threshold value changed.
- 2026-06-23 T904/A026-A027 production gold-label intake adds explicit `--allow-production-gold-set` and `production_gold_evidence` metadata requirements for real operator-supplied labels; PARAM-064 through PARAM-068 threshold values remain unchanged and repository fixtures still fail closed.
- 2026-06-23 T1307/A209 background soak governance adds operational evidence parameters `PARAM-069` through `PARAM-071` for watchdog cadence, stale-PID detection and heartbeat schema binding; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T904/A026-A027 production gold-label intake template adds an operator-fillable template artifact for required production-label metadata and case schemas; PARAM-064 through PARAM-068 values remain unchanged and the template is not release-ready evidence.
- 2026-06-24 T1309/A210 brand-clearance intake adds governance evidence parameters `PARAM-072` through `PARAM-075` for schema version, required trademark jurisdictions, required market surfaces and accepted signed-clearance decisions; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1301/A202 release-decision intake adds governance evidence parameter `PARAM-076` for the A202 intake schema version covering source-license, passage-level, owner and legal review fields; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1301/A202 signed-intake preflight adds governance evidence parameter `PARAM-081` for the A202 preflight schema version that turns a template or future signed intake into a hash-bound gate artifact; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1302/A203 production API release preflight adds governance evidence parameter `PARAM-077` for the A203 preflight schema version; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1303/A204-A205 MVP release-gate preflight adds governance evidence parameter `PARAM-078` for the final fail-closed release aggregator schema version; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1307/A209 operator-soak finalization preflight adds governance evidence parameter `PARAM-079` for the finalizer schema version; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1303 external release evidence bundle preflight adds governance evidence parameter `PARAM-080` for the bundle schema version; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T1307/A209 background heartbeat refresh adds governance evidence parameter `PARAM-082` for the invariant policy `soak.background_heartbeat_counts_as_release_ready=false`; no scoring model, graph traversal formula, extraction formula, formula weight or business scoring threshold changed.
- 2026-06-24 T904/A026-A027 governance sync adds `PARAM-083` for the production gold-set forbidden fixture-ref/labeler exclusion; no scoring model, formula weight or precision threshold value changed.
- 2026-06-25 T1301/A202 signed-decision hardening adds `PARAM-085` for exact signed candidate/source/owner coverage rejection prefixes; no scoring model, graph traversal formula, extraction formula, formula weight or business threshold changed.
- 2026-06-25 T1301/A202 live official capture freshness refresh adds `PARAM-086` for the non-clearance policy `capture_policy.release_clearance=false`; no scoring model, graph traversal formula, extraction formula, formula weight, business threshold or publication policy changed.
- 2026-06-25 T1303 external release operator intake packet adds `PARAM-087` for the operator checklist packet schema version; it organizes required A202/A210/A026/A027/A209 inputs and does not close release-manager activation, public launch, scoring, formula, threshold or publication gates.
- 2026-06-25 T1301/A202 signed-intake source-boundary hardening adds `PARAM-088` for disallowed repository fixture/source prefixes; signed intake closure now rejects repository fixtures, templates, docs, config, data and test sources unless the file is outside the repository or under an approved operator-input directory. No scoring model, graph traversal formula, extraction formula, formula weight, business threshold or publication policy changed.
- 2026-06-25 T1302/A203 API implementation contract closure marks A203 implementation coverage DONE and refreshes A209 heartbeat to `35/288`; no scoring model, graph traversal formula, extraction formula, formula weight, business threshold, API schema, database schema, frontend behavior or publication policy changed.
- 2026-06-25 T1302/A203 E2E CI repair updates development-status evidence expectations and generated release artifacts only; no scoring model, graph traversal formula, extraction formula, formula weight, business threshold, API schema, database schema, frontend behavior or publication policy changed.
- 2026-06-27 T1309/A210 signed brand-clearance source-boundary and T1307/A209 Playwright runtime repair add `PARAM-089` and `PARAM-090`; repository brand-clearance fixtures/templates still cannot close A210, short runtime smoke evidence does not close A209, and no scoring model, graph traversal formula, extraction formula, formula weight, business threshold, API schema, database schema, frontend behavior or publication policy changed.
- 2026-06-27 T1307/A209 heartbeat/watchdog stale binding changes only operational evidence interpretation: heartbeat now consumes watchdog output and maps stale live checkpoint observations to intervention; `PARAM-070` remains 900 seconds and no scoring model, graph traversal formula, extraction formula, formula weight, business threshold, API schema, database schema, frontend behavior or publication policy changed.
- 2026-06-27 T1307/A209 wall-clock budget repair adds `PARAM-091` and `PARAM-092`; the operator runner and evidence validator now use `measured_duration_seconds + max(180, measured_duration_seconds * 0.5)` for wall-clock evidence acceptance while still rejecting serialized 300s measured / 600s elapsed windows. No scoring model, graph traversal formula, extraction formula, formula weight, business threshold, API schema, database schema, frontend behavior or publication policy changed.

## A. Model Overview

### `MOD-001` - 综合研究优先级

- Kind: `ranking_or_scoring_model`
- Purpose: 节点大小、排序、路径、Watchlist
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:2, EEI/config/model_profiles/balanced-v2.json, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=node; formula=F-NP-001
- Outputs: 节点大小、排序、路径、Watchlist
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-001
- Parameter IDs: PARAM-001, PARAM-002, PARAM-003, PARAM-004, PARAM-005, PARAM-006, PARAM-007, PARAM-008, PARAM-009, PARAM-010, PARAM-011, PARAM-012
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:2, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-002` - 证据质量

- Kind: `ranking_or_scoring_model`
- Purpose: 证据等级、发布门槛、解释
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:3, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=evidence; formula=F-EQ-001
- Outputs: 证据等级、发布门槛、解释
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-002
- Parameter IDs: PARAM-020, PARAM-021, PARAM-022, PARAM-023, PARAM-024, PARAM-025
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:3, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-003` - 时间相关性

- Kind: `ranking_or_scoring_model`
- Purpose: 所有时间衰减
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:4, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=fact_event; formula=F-RF-001
- Outputs: 所有时间衰减
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-003
- Parameter IDs: PARAM-013, PARAM-014, PARAM-015, PARAM-016, PARAM-017, PARAM-018, PARAM-019
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:4, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-004` - 关系重要性

- Kind: `ranking_or_scoring_model`
- Purpose: 边显示、宽度、Top-N
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:5, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=relationship; formula=F-EM-001
- Outputs: 边显示、宽度、Top-N
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-004
- Parameter IDs: PARAM-026, PARAM-027, PARAM-028, PARAM-029, PARAM-030, PARAM-031, PARAM-032, PARAM-033, PARAM-034, PARAM-035
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:5, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-005` - 供应链关键性

- Kind: `ranking_or_scoring_model`
- Purpose: 瓶颈、替代性、关键路径
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:6, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=relationship_path; formula=F-SC-001
- Outputs: 瓶颈、替代性、关键路径
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-005
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:6, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-006` - 控制影响

- Kind: `ranking_or_scoring_model`
- Purpose: 所有权与控制视图
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:7, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=entity_relationship; formula=F-CI-001
- Outputs: 所有权与控制视图
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-006
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:7, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-007` - 资本动量

- Kind: `ranking_or_scoring_model`
- Purpose: 资金与并购视图
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:8, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=entity_period; formula=F-CM-001
- Outputs: 资金与并购视图
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-007
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:8, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-008` - 政策暴露

- Kind: `ranking_or_scoring_model`
- Purpose: 政策雷达和风险
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:9, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=entity_jurisdiction; formula=F-PE-001
- Outputs: 政策雷达和风险
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-008
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:9, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-009` - 战略信号

- Kind: `ranking_or_scoring_model`
- Purpose: 战略主题和反证
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:10, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=entity_theme_period; formula=F-SS-001
- Outputs: 战略主题和反证
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-009
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:10, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-010` - 变化告警

- Kind: `ranking_or_scoring_model`
- Purpose: 变化优先级和 Watchlist 告警
- Owner: model owner
- Status: `active`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:11, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=change_event; formula=F-AS-001
- Outputs: 变化优先级和 Watchlist 告警
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-010
- Parameter IDs: PARAM-036, PARAM-037, PARAM-038, PARAM-039, PARAM-040, PARAM-041
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:11, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-011` - 依赖风险

- Kind: `planned_risk_model`
- Purpose: 跨关系族依赖风险
- Owner: model owner
- Status: `planned`
- Model version: `business-empire-model-v2`
- Implementation reference: EEI/data/model_registry.csv:12, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Inputs: scoring_object=entity_path; formula=F-DR-001
- Outputs: 跨关系族依赖风险
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-011
- Parameter IDs: NOT_APPLICABLE
- Test references: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47, EEI/tests/e2e/state-contract.spec.ts:5
- Evidence references: EEI/data/model_registry.csv:12, EEI/data/model_registry.csv; EEI/data/formula_registry.csv; EEI/data/parameter_catalog.csv, EEI/data/development_status_ledger.csv:19-29
- Failure modes: missing evidence inputs; coverage below threshold; configuration validation failure; production scoring engine not confirmed

### `MOD-012` - 运行、视觉与校准阈值控制

- Kind: `deterministic_configuration_rule`
- Purpose: Provide non-scoring operational thresholds for refresh, visual coverage, motion timing, calibration controls, soak runner execution windows and browser runtime fallback, fail-closed A202 review-packet gates, A202 release-decision intake, signed-intake preflight and signed-intake source-boundary gates, A202/A210 release-decision bundle schema validation/publication binding, A026/A027 gold-quality/intake gates, A209 background heartbeat controls, A210 brand-clearance intake/source-boundary gates and T1303 external release operator intake packet gates.
- Owner: model owner
- Status: `active`
- Model version: `operational-controls-v1`
- Implementation reference: EEI/data/parameter_catalog.csv:43-84, EEI/config/thresholds/default-v2.json, EEI/config/model_runtime_defaults.yaml, EEI/scripts/run_operator_soak.mjs, EEI/scripts/validate_a202_operator_review_packet.py, EEI/scripts/validate_release_decision_bundle.py, EEI/scripts/validate_a202_signed_intake_preflight.py, EEI/scripts/validate_gold_quality_evaluation.py, EEI/scripts/watch_operator_soak.py, EEI/scripts/record_operator_soak_heartbeat.py, EEI/scripts/validate_brand_clearance.py, EEI/scripts/validate_external_release_evidence_bundle.py
- Inputs: parameter_key; configured_value; default_value; min_value; max_value
- Outputs: validated operational parameter value
- Use cases: research prioritization, explainable visual focus, governance validation, and bounded exploration support.
- Non-use cases: investment return prediction, live trading signal generation, hidden-truth inference, or production factual claims without evidence.
- Formula IDs: FORM-012
- Parameter IDs: PARAM-042, PARAM-043, PARAM-044, PARAM-045, PARAM-046, PARAM-047, PARAM-048, PARAM-049, PARAM-050, PARAM-051, PARAM-052, PARAM-053, PARAM-054, PARAM-055, PARAM-056, PARAM-057, PARAM-058, PARAM-059, PARAM-060, PARAM-061, PARAM-062, PARAM-063, PARAM-064, PARAM-065, PARAM-066, PARAM-067, PARAM-068, PARAM-069, PARAM-070, PARAM-071, PARAM-072, PARAM-073, PARAM-074, PARAM-075, PARAM-076, PARAM-077, PARAM-078, PARAM-079, PARAM-080, PARAM-081, PARAM-082, PARAM-083, PARAM-084, PARAM-085, PARAM-086, PARAM-087, PARAM-088, PARAM-089, PARAM-090
- Test references: EEI/scripts/validate_model_config.py:49-71, EEI/scripts/validate_governance.py:108-121, EEI/scripts/run_operator_soak.mjs, EEI/scripts/validate_v5_production_readiness_sync.py, EEI/scripts/validate_a202_operator_review_packet.py, EEI/scripts/validate_release_decision_bundle.py, EEI/scripts/validate_gold_quality_evaluation.py, EEI/scripts/record_operator_soak_heartbeat.py, EEI/scripts/validate_brand_clearance.py, EEI/scripts/validate_external_release_evidence_bundle.py, EEI/tests/unit/test_official_source_live_capture.py, EEI/tests/unit/test_release_decision_bundle.py, EEI/tests/unit/test_gold_quality_evaluation.py, EEI/tests/unit/test_operator_soak_evidence.py, EEI/tests/unit/test_brand_clearance.py, EEI/tests/unit/test_external_release_evidence_bundle.py
- Evidence references: EEI/data/parameter_catalog.csv:43-84, EEI/docs/governance/parameter_registry.csv:PARAM-089, EEI/docs/governance/parameter_registry.csv:PARAM-090, EEI/config/thresholds/default-v2.json:1, EEI/config/model_runtime_defaults.yaml:1, EEI/artifacts/tests/a209/t1307_operator_soak_readiness.json, EEI/artifacts/tests/a209/t1307_operator_soak_background_progress.json, EEI/artifacts/tests/a202/t1301_operator_review_packet_contract.json, EEI/artifacts/tests/a202/t1301_a202_release_decision_intake_template.json, EEI/artifacts/tests/a202/t1301_a202_a210_release_decision_bundle_contract.json, EEI/artifacts/tests/a026/t904_a026_a027_production_gold_label_intake_template.json, EEI/artifacts/tests/a026/t904_entity_resolution_gold_evaluation_contract.json, EEI/artifacts/tests/a027/t904_relationship_gold_evaluation_contract.json, EEI/artifacts/tests/a210/t1309_brand_clearance_intake_template.json, EEI/artifacts/tests/a205/t1303_external_release_operator_intake_packet.json
- Failure modes: missing runtime motion config; threshold out of schema range; auto activation enabled

## B. Assumptions

### `ASM-001`

- Statement: Scores are research prioritization and explanation aids, not investment return probabilities.
- Why needed: keeps scores, missing data, and activation claims bounded to evidenced behavior.
- Evidence or source: EEI/AGENTS.md:24-26, EEI/config/model_profiles/balanced-v2.json:5
- Applicable scope: all EEI model, formula, parameter, task, and acceptance governance.
- Impact if violated: scores may be interpreted as factual or predictive claims without support.
- How to falsify or validate: run model config validators, inspect source provenance, and verify missing-value handling in formula registry.
- Current status: `active` / `EXTRACTED`

### `ASM-002`

- Statement: Missing or unobserved inputs are not coerced to zero; formula missing_policy controls renormalization or disclosure.
- Why needed: keeps scores, missing data, and activation claims bounded to evidenced behavior.
- Evidence or source: EEI/AGENTS.md:24, EEI/data/formula_registry.csv:2-12, EEI/config/model_runtime_defaults.yaml:6
- Applicable scope: all EEI model, formula, parameter, task, and acceptance governance.
- Impact if violated: scores may be interpreted as factual or predictive claims without support.
- How to falsify or validate: run model config validators, inspect source provenance, and verify missing-value handling in formula registry.
- Current status: `active` / `EXTRACTED`

### `ASM-003`

- Statement: Model and parameter changes require dry-run validation, immutable versioning, preview, and rollback before activation.
- Why needed: keeps scores, missing data, and activation claims bounded to evidenced behavior.
- Evidence or source: EEI/config/model_runtime_defaults.yaml:4-7, EEI/config/model_profiles/balanced-v2.json; EEI/config/thresholds/default-v2.json
- Applicable scope: all EEI model, formula, parameter, task, and acceptance governance.
- Impact if violated: scores may be interpreted as factual or predictive claims without support.
- How to falsify or validate: run model config validators, inspect source provenance, and verify missing-value handling in formula registry.
- Current status: `active` / `EXTRACTED`

### `ASM-004`

- Statement: Production scoring engine, live data calibration, and real benchmark quality are not fully evidenced in current governance inputs.
- Why needed: keeps scores, missing data, and activation claims bounded to evidenced behavior.
- Evidence or source: EEI/data/development_status_ledger.csv:19-29, EEI/data/development_status_ledger.csv:19-29
- Applicable scope: all EEI model, formula, parameter, task, and acceptance governance.
- Impact if violated: scores may be interpreted as factual or predictive claims without support.
- How to falsify or validate: run model config validators, inspect source provenance, and verify missing-value handling in formula registry.
- Current status: `active` / `EXTRACTED`

## C. Functions and Formulas

Machine source: `formula_registry.yaml`. Legacy `F-*` IDs are preserved as `legacy_formula_id`; canonical IDs are `FORM-xxx`.

### `FORM-001` - legacy `F-NP-001`

- Model: `MOD-001`
- Status: `active`
- Mathematical formula or exact pseudocode: `sum(component_i * weight_i) * QualityFactor * CoverageFactor`
- Natural language explanation: 控制节点大小、排序、路径和 Watchlist 优先级
- Variables: component_i (number, score, 0..100); weight_i (number, ratio, 0..1; group sum 1.0); QualityFactor (number, ratio, 0..1); CoverageFactor (number, ratio, 0..1)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=minimum adjusted priority >= 46; unobserved inputs follow missing_policy
- Missing data handling: renormalize_available+coverage_penalty
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:4, EEI/config/model_profiles/balanced-v2.json, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-002` - legacy `F-EQ-001`

- Model: `MOD-002`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.28*source_authority + 0.18*locator_precision + 0.14*temporal_fit + 0.16*cross_source_confirmation + 0.12*source_independence + 0.12*entity_resolution_quality`
- Natural language explanation: 衡量证据可信度与可定位性
- Variables: source_authority (number, score, 0..100); locator_precision (number, score, 0..100); temporal_fit (number, score, 0..100); cross_source_confirmation (number, score, 0..100); source_independence (number, score, 0..100); entity_resolution_quality (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=minimum quality >= 55; inferred relation sources >= 2; unobserved inputs follow missing_policy
- Missing data handling: renormalize_available
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:2, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-003` - legacy `F-RF-001`

- Model: `MOD-003`
- Status: `active`
- Mathematical formula or exact pseudocode: `exp(-ln(2) * age_days / half_life_days)`
- Natural language explanation: 按信息类型衰减时间贡献
- Variables: age_days (number, days, >=0); half_life_days (number, days, 30..1825)
- Output range: 0..1
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..1; default_threshold=30..1825 days; unobserved inputs follow missing_policy
- Missing data handling: use_observed_at_or_disclose_unknown
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:3, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-004` - legacy `F-EM-001`

- Model: `MOD-004`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.35*relationship_strength + 0.25*strategic_dependency + 0.20*transaction_materiality + 0.10*evidence_quality + 0.10*time_relevance`
- Natural language explanation: 控制关系边显示、宽度和聚合
- Variables: relationship_strength (number, score, 0..100); strategic_dependency (number, score, 0..100); transaction_materiality (number, score, 0..100); evidence_quality (number, score, 0..100); time_relevance (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=minimum edge materiality >= 48; unobserved inputs follow missing_policy
- Missing data handling: renormalize_available
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:5, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-005` - legacy `F-SC-001`

- Model: `MOD-005`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.30*uniqueness + 0.25*switching_cost + 0.20*lead_time + 0.15*capacity_concentration + 0.10*geopolitical_exposure`
- Natural language explanation: 定位瓶颈、替代性和单点依赖
- Variables: uniqueness (number, score, 0..100); switching_cost (number, score, 0..100); lead_time (number, score, 0..100); capacity_concentration (number, score, 0..100); geopolitical_exposure (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=critical >= 70; unobserved inputs follow missing_policy
- Missing data handling: unknown_not_zero
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:8, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-006` - legacy `F-CI-001`

- Model: `MOD-006`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.30*voting_power + 0.25*board_rights + 0.20*special_rights + 0.15*economic_interest + 0.10*founder_management_power`
- Natural language explanation: 区分经济所有权与实际控制
- Variables: voting_power (number, score, 0..100); board_rights (number, score, 0..100); special_rights (number, score, 0..100); economic_interest (number, score, 0..100); founder_management_power (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=material >= 55; unobserved inputs follow missing_policy
- Missing data handling: separate_unknown_components
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:9, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-007` - legacy `F-CM-001`

- Model: `MOD-007`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.25*capex_growth + 0.20*financing_activity + 0.20*strategic_investment + 0.15*mna_activity + 0.10*buyback_dividend_shift + 0.10*commitment_growth`
- Natural language explanation: 识别资本配置方向
- Variables: capex_growth (number, score, 0..100); financing_activity (number, score, 0..100); strategic_investment (number, score, 0..100); mna_activity (number, score, 0..100); buyback_dividend_shift (number, score, 0..100); commitment_growth (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=material >= 60; unobserved inputs follow missing_policy
- Missing data handling: amount_semantics_aware
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:10, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-008` - legacy `F-PE-001`

- Model: `MOD-008`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.25*revenue_dependency + 0.20*subsidy_dependency + 0.20*export_control + 0.15*regulatory_intensity + 0.10*government_contract + 0.10*geographic_concentration`
- Natural language explanation: 呈现政策机会、约束和依赖
- Variables: revenue_dependency (number, score, 0..100); subsidy_dependency (number, score, 0..100); export_control (number, score, 0..100); regulatory_intensity (number, score, 0..100); government_contract (number, score, 0..100); geographic_concentration (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=watch >= 55; unobserved inputs follow missing_policy
- Missing data handling: jurisdiction_specific_unknown
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:11, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-009` - legacy `F-SS-001`

- Model: `MOD-009`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.28*capex_acceleration + 0.20*investment_and_mna + 0.18*capacity_and_long_contracts + 0.14*talent_and_hiring + 0.10*patent_product_signal + 0.10*policy_alignment`
- Natural language explanation: 形成下一步战略主题研究假设
- Variables: capex_acceleration (number, score, 0..100); investment_and_mna (number, score, 0..100); capacity_and_long_contracts (number, score, 0..100); talent_and_hiring (number, score, 0..100); patent_product_signal (number, score, 0..100); policy_alignment (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=watch >= 60; strong >= 75; unobserved inputs follow missing_policy
- Missing data handling: renormalize_available+contradiction_panel
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:6, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-010` - legacy `F-AS-001`

- Model: `MOD-010`
- Status: `active`
- Mathematical formula or exact pseudocode: `0.35*score_delta + 0.25*novelty + 0.20*evidence_quality + 0.20*watchlist_relevance`
- Natural language explanation: 决定变化与告警优先级
- Variables: score_delta (number, score, 0..100); novelty (number, score, 0..100); evidence_quality (number, score, 0..100); watchlist_relevance (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=high-priority alert >= 80; material delta >= 8; unobserved inputs follow missing_policy
- Missing data handling: no_alert_without_evidence
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:7, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-011` - legacy `F-DR-001`

- Model: `MOD-011`
- Status: `planned`
- Mathematical formula or exact pseudocode: `0.30*concentration + 0.25*criticality + 0.20*switching_cost + 0.15*contract_lock_in + 0.10*policy_exposure`
- Natural language explanation: 跨供应链、技术和商业依赖形成风险排序
- Variables: concentration (number, score, 0..100); criticality (number, score, 0..100); switching_cost (number, score, 0..100); contract_lock_in (number, score, 0..100); policy_exposure (number, score, 0..100)
- Output range: 0..100
- Normalization: renormalize available components when indicated by missing_policy; otherwise disclose unavailable inputs.
- Constraints: output_range=0..100; default_threshold=high >= 70; unobserved inputs follow missing_policy
- Missing data handling: renormalize_available+coverage
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/formula_registry.csv:12, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_governance.py:108-121
- Test position: EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_model_config.py:23-47

### `FORM-012` - legacy `NOT_APPLICABLE`

- Model: `MOD-012`
- Status: `active`
- Mathematical formula or exact pseudocode: `value = configured_value if present and within [min_value,max_value] else default_value; activation requires validation and manual gate where configured.`
- Natural language explanation: Operational deterministic lookup for threshold, motion, visual, refresh, calibration, frontend hydration guard and gold-quality gate parameters without a scoring formula.
- Variables: configured_value (number|string|boolean, parameter_specific, parameter_registry min_value..max_value); default_value (number|string|boolean, parameter_specific, parameter_registry min_value..max_value); min_value (number|string|boolean, parameter_specific, catalog constraint); max_value (number|string|boolean, parameter_specific, catalog constraint)
- Output range: parameter_specific
- Normalization: NOT_APPLICABLE: deterministic configuration lookup, not a score aggregation.
- Constraints: parameter-specific range from parameter_registry.csv; calibration.auto_activate must be false; calibration cadence remains 14 days; workspace layer controls must remain disabled until stateReady and a supported layer-to-lens mapping exists; gold-quality closure requires the configured sample-count, precision and source-coverage gates to pass; gold-label intake templates must remain non-closure evidence
- Missing data handling: fallback_to_default_or_UNKNOWN_with_task
- Boundary conditions: respect per-variable input domain and configured min/max bounds; invalid configuration fails validation.
- Fallback: use configured default or previous valid snapshot; Unavailable values remain disclosed and task-linked.
- Implementation position: EEI/data/parameter_catalog.csv:43-84, EEI/apps/web/src/app/page.tsx, EEI/config/thresholds/default-v2.json, EEI/config/ui/motion-tokens.json, EEI/config/model_runtime_defaults.yaml, EEI/scripts/validate_model_config.py:validate_motion_tokens, EEI/scripts/validate_a202_operator_review_packet.py, EEI/scripts/validate_release_decision_bundle.py, EEI/scripts/validate_gold_quality_evaluation.py
- Test position: EEI/tests/e2e/home.spec.ts, EEI/scripts/validate_model_config.py, EEI/scripts/validate_governance.py:108-121, EEI/scripts/validate_a202_operator_review_packet.py, EEI/scripts/validate_release_decision_bundle.py, EEI/scripts/validate_gold_quality_evaluation.py, EEI/tests/unit/test_official_source_live_capture.py, EEI/tests/unit/test_release_decision_bundle.py, EEI/tests/unit/test_gold_quality_evaluation.py

## D. Parameters

Machine source: `parameter_registry.csv`. Defaults, initial/prior values, active values, ranges, source rationale, code refs, config refs, and test refs are separated per row.

## E. Methodology

- Why current method: existing EEI Task Pack defines deterministic, explainable scoring and threshold controls for research ordering and visual focus.
- Alternatives considered: no alternative runtime motion source was adopted; `config/ui/motion-tokens.json` is the machine-verified source for motion duration controls. Broader comparative model-selection evidence remains UNKNOWN and task-linked to production model review.
- Objective: explainable prioritization and bounded UI/research workflow support, not prediction of returns.
- Calibration method: extracted governance cadence is every 14 days with `auto_activate=false`; no live empirical calibration evidence is confirmed.
- Training/backtest/experiment method: UNKNOWN for production scoring; validators and E2E tests prove catalog/config/UI contracts only. Linked task: TASK-T1206.
- Baseline: `balanced-v2@2`, `default-v2@2`, `model_runtime_defaults` version 14.
- Data split and out-of-sample: UNKNOWN for model quality evaluation. Linked task: TASK-T1206.
- Sensitivity analysis: parameter step/range validation exists, including motion token range and step checks; empirical sensitivity results are UNKNOWN. Linked task: TASK-T1206.
- Known limitations: production calculation engine and real data benchmarks are not fully evidenced in current governance inputs.

## F. Strategy Logic

- Signal formation: formulas compute or configure prioritization, materiality, quality, recency, alerts, and operational thresholds from evidenced inputs.
- Gate filtering: thresholds in `config/thresholds/default-v2.json` and `parameter_registry.csv` gate evidence, graph size, alerts, visual coverage, refresh, and calibration.
- Score-to-decision mapping: scores drive visual focus, ordering, Watchlist/change priority, and explanation panels; they do not trigger trading or investment decisions.
- Risk limits: unknowns are disclosed, fixture/live boundaries are preserved, calibration does not auto-activate, and previous valid snapshots remain available.
- Fallback: validation failure blocks activation; existing snapshot remains active.
- Deactivation conditions: invalid config, inconsistent model/data snapshot, unresolved source coverage risk, or missing acceptance evidence.
- Human approval points: model/parameter activation, calibration proposal acceptance, release gates, source-license/legal/brand decisions, and production owner sign-off.
- Safe behavior on failure: no partial publish and no silent fill of unknowns.

## G. Validation

- Metrics: weight sums, schema/range validity, catalog uniqueness, task/acceptance traceability, E2E model context evidence.
- Baseline: `balanced-v2@2`, `default-v2@2`.
- Dataset or fixture: existing EEI fixtures and catalogs; live production data not confirmed.
- Test command: `python scripts/validate_model_config.py config/model_profiles/balanced-v2.json config/thresholds/default-v2.json`.
- Test command: `python scripts/apply_model_config.py --profile config/model_profiles/supply-chain-v3.json --thresholds config/thresholds/default-v2.json --dry-run`.
- Test command: `python scripts/validate_governance.py`.
- Current operator activation boundary: `scripts/apply_model_config.py` dry-run is hash-bound and non-writing; `--execute` requires a PostgreSQL URL and delegates to the repository transaction layer. This changes the operator entrypoint only, not active formula, weight or threshold values.
- Current result: see `DEVELOPMENT_LEDGER.md` after GOV-G2 validation run.
- Result date: 2026-06-20.
- Uncovered scenarios: live data calibration, empirical model quality, exact per-task historical stdout for all reconstructed tasks.
- Release gate: `GOV-G2-EEI-BASELINE`.
