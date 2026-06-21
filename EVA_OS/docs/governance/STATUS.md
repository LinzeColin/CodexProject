# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `EVA_OS`
- Path: `EVA_OS`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +13`
- Parameter profile versions: `default:param-profile-20260620, semantic_extractor_profile:param-semantic-profile-20260621`
- Current iteration: `ITER-20260621-EVA-003`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-EVA-001-in-progress`
- Model count: `16`
- Formula count: `16`
- Parameter count: `189`
- Task count: `13`
- Unbound event count: `3`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `404`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-EVA-001`

## Latest Run

- Event: `ITER-20260621-EVA-003`
- Task: `GOV-SEMANTIC-EVA-001`
- Summary: Add machine selectors for 52 EVA_OS active parameters and implementation fingerprints for 16 active formulas without runtime behavior changes.
- Model delta: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, +10 more
- Parameter delta: PARAM-001, PARAM-002, PARAM-003, PARAM-004, PARAM-005, PARAM-006, +46 more
- Tests: python3 -m py_compile scripts/validate_semantic_extractors.py scripts/validate_project_governance.py scripts/validate_governance_sync.py scripts/generate_governance_dashboard.py -> exit 0, python3 scripts/validate_semantic_extractors.py EVA_OS -> exit 0; semantic_parameters_checked=52 semantic_formulas_checked=16, python3 scripts/validate_project_governance.py --project EVA_OS --semantic -> exit 0; errors 0 warnings 0, python3 scripts/validate_project_governance.py --all --semantic --drift-report -> exit 0; errors 0 warnings 0, python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic -> exit 0; errors 0 warnings 0 after append-only repair, python3 -m pytest tests/governance -q -> exit 0; 44 passed, +2 more
- Evidence: EVA_OS/docs/governance/parameter_registry.csv, EVA_OS/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-EVA-EXTRACT-001.json
- Result: `PASS: local semantic extractor validation, project validator, all-project validator, changed-only sync gate after append-only repair, governance tests, dashboard determinism and diff check all returned exit 0.`
- Rollback: UNKNOWN

## Current Blockers

calibration/source rationale gaps tracked by `TASK-EVA-B-001` through `TASK-EVA-B-008`

## Semantic Coverage

- Status: `in_progress`
- Target: Add machine selectors for strategy parameters and fingerprints for active strategy formulas.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-EVA-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-EVA-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; EVA_OS now machine-checks 52 active parameters and 16 active formulas while remaining parameters stay HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-EVA-001.; status: in_progress; target: Add machine selectors for strategy parameters and fingerprints for active strategy formulas.; +1 more

## Next Task

`TASK-EVA-B-003` - Resolve source rationale for cross-source validation tolerance.

- Status: `blocked`
- Acceptance: ACC-EVA-B-003
- Selection rationale: status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=145
