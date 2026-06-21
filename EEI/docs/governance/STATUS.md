# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `EEI`
- Path: `EEI`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:business-empire-model-v2, MOD-002:business-empire-model-v2, MOD-003:business-empire-model-v2, +9`
- Parameter profile versions: `balanced-v2:2, default-v2:2, model_runtime_defaults:14`
- Current iteration: `ITER-20260621-016`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-EEI-001-PARTIAL-EXTRACTORS`
- Model count: `12`
- Formula count: `12`
- Parameter count: `61`
- Task count: `124`
- Unbound event count: `15`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `153`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-EEI-001`

## Latest Run

- Event: `EVENT-20260621-018`
- Task: `GOV-SEMANTIC-EEI-001`
- Summary: Added partial EEI machine semantic extraction metadata without changing business behavior.
- Model delta: No runtime model behavior change; 10 active formula registry rows now have machine implementation fingerprints and FORM-012 is HUMAN_REVIEW_REQUIRED.
- Parameter delta: No active parameter value change; 54 active parameters now have source selectors and evidence hashes, 7 UNKNOWN motion parameters remain task-bound.
- Tests: python3 scripts/validate_semantic_extractors.py EEI, python3 scripts/validate_project_governance.py --project EEI --semantic, python3 scripts/validate_project_governance.py --all --semantic --drift-report, python3 -m pytest tests/governance -q, python3 scripts/generate_governance_dashboard.py --write twice, python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic, +4 more
- Evidence: governance/run_manifests/GOV-SEMANTIC-EEI-EXTRACT-001.json, EEI/docs/governance/parameter_registry.csv, EEI/docs/governance/formula_registry.yaml, EEI/artifacts/tests/a200/t1215_clean_room_release.json, EEI/artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip, EEI/artifacts/release_evidence_t1211.json, +1 more
- Result: `LOCAL_VALIDATION_PASS_EEI_SEMANTIC_IN_PROGRESS`
- Rollback: Remove EEI semantic selector and fingerprint metadata, reset semantic_coverage to planned, and rerun governance validators.

## Current Blockers

7 active motion parameters still have UNKNOWN runtime activation evidence, and FORM-012 remains HUMAN_REVIEW_REQUIRED.

## Semantic Coverage

- Status: `in_progress`
- Target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-EEI-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-EEI-EXTRACT-001.json; owner: project owner; rationale: EEI now has partial machine semantic extraction for 54 active parameters and 10 active formulas; 7 UNKNOWN motion parameters and FORM-012 remain task-bound.; status: in_progress; target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.; +1 more

## Next Task

`TASK-T1301` - Implement real data ingestion, entity resolution and evidence chain for the Golden Vertical

- Status: `in_progress`
- Acceptance: ACC-A202
- Selection rationale: status=in_progress; phase=C; current_phase=B; unmet_dependencies=none; score=122
