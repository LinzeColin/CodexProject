# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `PFI_BIG_DATA_SIMULATOR`
- Path: `PFI/大数据模拟器`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +12`
- Parameter profile versions: `default:param-profile-20260620`
- Current iteration: `ITER-20260621-PFI-001`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-PFI-in-progress`
- Model count: `15`
- Formula count: `15`
- Parameter count: `213`
- Task count: `15`
- Unbound event count: `3`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `218`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-PFI-001`

## Latest Run

- Event: `ITER-20260621-PFI-001`
- Task: `GOV-SEMANTIC-PFI-001`
- Summary: Add machine selectors for 211 PFI active parameters and implementation fingerprints for 15 active formulas without runtime behavior changes.
- Model delta: MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, +9 more
- Parameter delta: PARAM-001, PARAM-002, PARAM-003, PARAM-004, PARAM-005, PARAM-006, +207 more
- Tests: python3 scripts/validate_semantic_extractors.py PFI/大数据模拟器 -> exit 0; semantic_parameters_checked=211 semantic_formulas_checked=15, python3 -m py_compile scripts/validate_semantic_extractors.py -> exit 0, python3 -m pytest tests/governance/test_project_governance_validator.py -q -> exit 0; 45 passed, project/all/changed-only validators run after append-only event creation and recorded in run manifest/final report
- Evidence: PFI/大数据模拟器/docs/governance/parameter_registry.csv, PFI/大数据模拟器/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-PFI-EXTRACT-001.json
- Result: `PASS_PARTIAL_SEMANTIC: local semantic extractor and governance tests passed; coverage remains in_progress because PARAM-110 and PARAM-111 require human review.`
- Rollback: UNKNOWN

## Current Blockers

`PARAM-110` and `PARAM-111` remain HUMAN_REVIEW_REQUIRED; calibration/source rationale gaps tracked by `TASK-PFI-B-001` through `TASK-PFI-B-010`

## Semantic Coverage

- Status: `in_progress`
- Target: Add extractors for simulator strategy defaults, risk controls, and active formula fingerprints.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-PFI-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-PFI-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; PFI_BIG_DATA_SIMULATOR now machine-checks 211 active parameters and 15 active formulas while PARAM-110 and PARAM-111 remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-PFI-001.; status: in_progress; target: Add extractors for simulator strategy defaults, risk controls, and active formula fingerprints.; +1 more

## Next Task

`TASK-PFI-B-001` - Resolve calibration evidence for strategy catalog rule constants and indicator thresholds.

- Status: `blocked`
- Acceptance: ACC-PFI-B-001
- Selection rationale: status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=138
