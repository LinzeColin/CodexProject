# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:serenity-scoring-v1, MOD-002:serenity-ranking-v1, MOD-003:serenity-metrics-v1, +2`
- Parameter profile versions: `serenity-parameters:serenity-parameters-v1`
- Current iteration: `ITER-20260621-002`
- Current phase: `B`
- Current gate: `GOV-REVIEW6-B-SEMANTIC-EXTRACT`
- Model count: `5`
- Formula count: `12`
- Parameter count: `49`
- Task count: `8`
- Unbound event count: `3`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `0`
- Semantic coverage: `machine_verified`
- Semantic rollout task: `TASK-B-003`

## Latest Run

- Event: `ITER-20260621-002`
- Task: `GOV-REVIEW6-B-SERENITY-SEMANTIC-EXTRACT-001`
- Summary: Added Serenity-Alipay semantic extraction pilot for active parameters and formulas without changing business behavior.
- Model delta: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005
- Parameter delta: PARAM-001, PARAM-002, PARAM-003, PARAM-004, PARAM-005, PARAM-006, +43 more
- Tests: python3 scripts/validate_semantic_extractors.py Serenity-Alipay -> exit 0 checked 49 parameters and 12 formulas, python3 scripts/validate_project_governance.py --project Serenity-Alipay --semantic -> exit 0 errors 0 warnings 0, python3 scripts/validate_project_governance.py --all --semantic --drift-report -> exit 0 errors 0 warnings 0, python3 -m pytest tests/governance -q -> exit 0 28 passed, python3 -m py_compile scripts/validate_project_governance.py scripts/validate_governance_sync.py scripts/validate_semantic_extractors.py -> exit 0, PYTHONPATH=Serenity-Alipay python3 -m pytest -q Serenity-Alipay/tests/test_scoring.py Serenity-Alipay/tests/test_pipeline_serenity_priority.py Serenity-Alipay/tests/test_risk_gate_regression.py Serenity-Alipay/tests/test_metrics.py Serenity-Alipay/tests/test_discipline.py Serenity-Alipay/tests/test_comparison.py Serenity-Alipay/tests/test_scheduler.py Serenity-Alipay/tests/test_timezones.py -> exit 1 root-cwd fixture path failure for scheduler tests, +1 more
- Evidence: Serenity-Alipay/docs/governance/parameter_registry.csv, Serenity-Alipay/docs/governance/formula_registry.yaml, tests/governance/test_project_governance_validator.py, scripts/validate_semantic_extractors.py
- Result: `pass_local_governance_validation_with_corrected_focused_test_invocation`
- Rollback: UNKNOWN

## Current Blockers

semantic extractor pilot currently covers Serenity-Alipay only; other projects need separate migration tasks.

## Semantic Coverage

- Status: `machine_verified`
- Target: Machine-check active parameter values and active formula implementation fingerprints.
- Evidence/rollout: acceptance_id: ACC-B-003; evidence_ref: governance/run_manifests/GOV-REVIEW6-B-SERENITY-SEMANTIC-EXTRACT-001.json; owner: project owner; rationale: Review6-B enabled 49 active parameter checks and 12 active formula fingerprints.; status: machine_verified; target: Machine-check active parameter values and active formula implementation fingerprints.; +1 more

## Next Task

`TASK-B-001` - Close empirical calibration UNKNOWNs for score weights, grade thresholds, and Top5 allocation constants.

- Status: `planned`
- Acceptance: ACC-B-001
- Selection rationale: status=planned; phase=B; current_phase=B; unmet_dependencies=TASK-A-002; score=59
