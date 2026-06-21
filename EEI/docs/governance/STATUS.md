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
- Current iteration: `ITER-20260621-017`
- Current phase: `C`
- Current gate: `TASK-T1307-A209-4H-OPERATOR-SOAK-PARTIAL`
- Model count: `12`
- Formula count: `12`
- Parameter count: `61`
- Task count: `124`
- Unbound event count: `16`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `153`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-EEI-001`

## Latest Run

- Event: `EVENT-20260621-019`
- Task: `TASK-T1307`
- Summary: Generated local 4h operator soak evidence for T1307/A209 with 48/48 PASS windows and PARTIAL_OPERATOR_EVIDENCE status because 24h is missing.
- Model delta: No scoring formula change.
- Parameter delta: No canonical model parameter change; run environment used PLAYWRIGHT_BROWSERS_PATH=/private/tmp/eei-ms-playwright.
- Tests: Playwright fixed-path install, 5-second fixed browser path probe, 4h operator soak, validate_operator_soak_evidence generate, validate_operator_soak_evidence validate
- Evidence: EEI/artifacts/tests/a209/t1307_operator_soak_4h.json, EEI/artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl, EEI/artifacts/tests/a209/t1307_operator_soak_evidence_validation.json, EEI/docs/phase/MVP_DEVELOPMENT_RECORD.md, EEI/docs/governance/VERSION_MATRIX.yaml, EEI/docs/governance/delivery_tasks.yaml, +2 more
- Result: `LOCAL_4H_OPERATOR_SOAK_PASS_A209_PARTIAL_24H_MISSING`
- Rollback: Remove the 4h JSON/checkpoint, regenerate A209 evidence validation, development artifacts and release artifacts, then rerun validation.

## Current Blockers

A209/A206 remain open until 24h operator soak evidence is produced and CI-validated; 7 active motion parameters still have UNKNOWN runtime activation evidence, and FORM-012 remains HUMAN_REVIEW_REQUIRED.

## Semantic Coverage

- Status: `in_progress`
- Target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-EEI-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-EEI-EXTRACT-001.json; owner: project owner; rationale: EEI now has partial machine semantic extraction for 54 active parameters and 10 active formulas; 7 UNKNOWN motion parameters and FORM-012 remain task-bound.; status: in_progress; target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.; +1 more

## Next Task

`TASK-T1301` - Implement real data ingestion, entity resolution and evidence chain for the Golden Vertical

- Status: `in_progress`
- Acceptance: ACC-A202
- Selection rationale: status=in_progress; phase=C; current_phase=C; unmet_dependencies=none; score=122
