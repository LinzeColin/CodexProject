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

## Latest Run

- Event: `ITER-20260621-002`
- Task: `GOV-REVIEW6-B-SERENITY-SEMANTIC-EXTRACT-001`
- Summary: Added Serenity-Alipay semantic extraction pilot for active parameters and formulas without changing business behavior.
- Model delta: `['MOD-001', 'MOD-002', 'MOD-003', 'MOD-004', 'MOD-005']`
- Parameter delta: `['PARAM-001', 'PARAM-002', 'PARAM-003', 'PARAM-004', 'PARAM-005', 'PARAM-006', 'PARAM-007', 'PARAM-008', 'PARAM-009', 'PARAM-010', 'PARAM-011', 'PARAM-012', 'PARAM-013', 'PARAM-014', 'PARAM-015', 'PARAM-016', 'PARAM-017', 'PARAM-018', 'PARAM-019', 'PARAM-020', 'PARAM-021', 'PARAM-022', 'PARAM-023', 'PARAM-024', 'PARAM-025', 'PARAM-026', 'PARAM-027', 'PARAM-028', 'PARAM-029', 'PARAM-030', 'PARAM-031', 'PARAM-032', 'PARAM-033', 'PARAM-034', 'PARAM-035', 'PARAM-036', 'PARAM-037', 'PARAM-038', 'PARAM-039', 'PARAM-040', 'PARAM-041', 'PARAM-042', 'PARAM-043', 'PARAM-044', 'PARAM-045', 'PARAM-046', 'PARAM-047', 'PARAM-048', 'PARAM-049']`
- Tests: `['python3 scripts/validate_semantic_extractors.py Serenity-Alipay -> exit 0 checked 49 parameters and 12 formulas', 'python3 scripts/validate_project_governance.py --project Serenity-Alipay --semantic -> exit 0 errors 0 warnings 0', 'python3 scripts/validate_project_governance.py --all --semantic --drift-report -> exit 0 errors 0 warnings 0', 'python3 -m pytest tests/governance -q -> exit 0 28 passed', 'python3 -m py_compile scripts/validate_project_governance.py scripts/validate_governance_sync.py scripts/validate_semantic_extractors.py -> exit 0', 'PYTHONPATH=Serenity-Alipay python3 -m pytest -q Serenity-Alipay/tests/test_scoring.py Serenity-Alipay/tests/test_pipeline_serenity_priority.py Serenity-Alipay/tests/test_risk_gate_regression.py Serenity-Alipay/tests/test_metrics.py Serenity-Alipay/tests/test_discipline.py Serenity-Alipay/tests/test_comparison.py Serenity-Alipay/tests/test_scheduler.py Serenity-Alipay/tests/test_timezones.py -> exit 1 root-cwd fixture path failure for scheduler tests', 'cd Serenity-Alipay && PYTHONPATH=. python3 -m pytest -q tests/test_scoring.py tests/test_pipeline_serenity_priority.py tests/test_risk_gate_regression.py tests/test_metrics.py tests/test_discipline.py tests/test_comparison.py tests/test_scheduler.py tests/test_timezones.py -> exit 0 22 passed']`
- Evidence: `['Serenity-Alipay/docs/governance/parameter_registry.csv', 'Serenity-Alipay/docs/governance/formula_registry.yaml', 'tests/governance/test_project_governance_validator.py', 'scripts/validate_semantic_extractors.py']`
- Result: `pass_local_governance_validation_with_corrected_focused_test_invocation`
- Rollback: UNKNOWN

## Current Blockers

semantic extractor pilot currently covers Serenity-Alipay only; other projects need separate migration tasks.

## Next Task

`TASK-A-001`
