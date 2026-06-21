# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- CI mode: `required`
- Product version: `0.0.0`
- Model versions: `MOD-001:salary-logic-v0, MOD-002:streamlit-input-v0`
- Parameter profile versions: `province_weights:salary-logic-v0, salary_logic_constants:salary-logic-v0, streamlit_defaults:streamlit-input-v0`
- Current iteration: `ITER-20260621-WHKM-001`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-WHKM-in-progress`
- Model count: `2`
- Formula count: `10`
- Parameter count: `80`
- Task count: `6`
- Unbound event count: `3`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `173`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-WHKM-001`

## Latest Run

- Event: `EVENT-WHKM-20260621-001`
- Task: `GOV-SEMANTIC-WHKM-001`
- Summary: Added machine semantic selectors for whkmSalary salary constants and formula fingerprints without changing salary runtime behavior.
- Model delta: MOD-001, MOD-002
- Parameter delta: PARAM-001, PARAM-002, PARAM-003, PARAM-004, PARAM-005, PARAM-006, +74 more
- Tests: python3 scripts/validate_semantic_extractors.py whkmSalary
- Evidence: governance/run_manifests/GOV-SEMANTIC-WHKM-EXTRACT-001.json, whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml
- Result: `IN_PROGRESS`
- Rollback: Revert whkmSalary semantic metadata, root projects.yaml semantic coverage update, generated status pages, and run manifest. No business code rollback is required.

## Current Blockers

`TASK-WHKM-B-001` for policy/source/effective date/rounding/boundary evidence; `GOV-SEMANTIC-WHKM-001` retains human review for `PARAM-004`, `PARAM-005`, and `FORM-010`.

## Semantic Coverage

- Status: `in_progress`
- Target: Add extractors for salary constants, policy formula references, and active formula fingerprints.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-WHKM-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-WHKM-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; whkmSalary now machine-checks 78 active parameters and 9 active formulas while PARAM-004, PARAM-005, and FORM-010 remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-WHKM-001.; status: in_progress; target: Add extractors for salary constants, policy formula references, and active formula fingerprints.; +1 more

## Next Task

`TASK-WHKM-B-001` - Resolve salary policy source, jurisdiction, effective date, tax basis, boundary behavior, and rounding policy evidence.

- Status: `blocked`
- Acceptance: ACC-WHKM-B-001
- Selection rationale: status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=108
