# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `FIFA`
- Path: `FIFA`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +8`
- Parameter profile versions: `active_profile:param-profile-20260620, legacy_profile:rules-v1.0.0`
- Current iteration: `ITER-20260621-FIFA-001`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-FIFA-in-progress`
- Model count: `11`
- Formula count: `11`
- Parameter count: `117`
- Task count: `10`
- Unbound event count: `3`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `108`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-FIFA-001`

## Latest Run

- Event: `EVT-FIFA-GOV-20260621-001`
- Task: `GOV-SEMANTIC-FIFA-001`
- Summary: Add machine source selectors for 91 active FIFA parameters and AST implementation fingerprints for 10 active formulas; keep 17 active parameters HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-FIFA-001.
- Model delta: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, +4 more
- Parameter delta: PARAM-001..PARAM-108
- Tests: python3 scripts/validate_semantic_extractors.py FIFA -> exit 0; semantic_parameters_checked=91 semantic_formulas_checked=10, python3 scripts/validate_project_governance.py --project FIFA --semantic -> exit 0; errors 0 warnings 0, python3 scripts/validate_project_governance.py --all --semantic --drift-report -> exit 0; errors 0 warnings 0, python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic -> exit 0; errors 0 warnings 0, python3 -m pytest tests/governance/test_project_governance_validator.py -q -> exit 0; 52 passed, FIFA py_compile/bash -n/node --check focused syntax checks -> exit 0, +2 more
- Evidence: FIFA/docs/governance/parameter_registry.csv, FIFA/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-FIFA-EXTRACT-001.json
- Result: `in_progress_local_validation_passed_pending_ci_binding`
- Rollback: UNKNOWN

## Current Blockers

TASK-FIFA-B-001, TASK-FIFA-B-002, TASK-FIFA-C-001, TASK-FIFA-C-002, TASK-FIFA-D-001, TASK-FIFA-D-002, TASK-FIFA-E-001, TASK-FIFA-E-002

## Semantic Coverage

- Status: `in_progress`
- Target: Add extractors for parser constants, validation rules, and active governance formulas.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-FIFA-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-FIFA-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; FIFA now machine-checks 91 active parameters and 10 active formulas while 17 active parameters remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-FIFA-001.; status: in_progress; target: Add extractors for parser constants, validation rules, and active governance formulas.; +1 more

## Next Task

`GOV-SEMANTIC-FIFA-001` - Add extractors for parser constants, validation rules, and active governance formulas.

- Status: `in_progress`
- Acceptance: ACC-SEMANTIC-FIFA-001
- Selection rationale: status=in_progress; phase=B; current_phase=B; unmet_dependencies=none; score=114
