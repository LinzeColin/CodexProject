# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `OpMe_System`
- Path: `OpMe_System`
- CI mode: `required`
- Product version: `1.0.0`
- Model versions: `MOD-001:mod-001-v0, MOD-002:mod-002-v0, MOD-003:mod-003-v0, +4`
- Parameter profile versions: `llm_router:opme-router-v0, offline_rules:opme-rules-v0`
- Current iteration: `ITER-20260621-OPME-001`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-OPME-in-progress`
- Model count: `7`
- Formula count: `7`
- Parameter count: `49`
- Task count: `6`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `92`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-OPME-001`

## Latest Run

- Event: `EVENT-OPME-20260621-003`
- Task: `GOV-SEMANTIC-OPME-001`
- Summary: Validated OpMe_System semantic extractor rollout locally and recorded blocked backend focused tests caused by missing local dependencies.
- Model delta: No runtime model behavior change; validation confirms 7 active formula fingerprints match live code symbols.
- Parameter delta: No active value change; validation confirms 49 active parameter active values match live code/config selectors.
- Tests: UNKNOWN
- Evidence: OpMe_System/docs/governance/parameter_registry.csv, OpMe_System/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-OPME-EXTRACT-001.json, tests/governance/test_project_governance_validator.py
- Result: `PASS_WITH_BLOCKED_ADDITIONAL_CHECK`
- Rollback: Revert this branch changes; no OpMe runtime rollback is required.

## Current Blockers

`TASK-OPME-B-001` for calibration, prompt/provider governance, and signoff evidence.

## Semantic Coverage

- Status: `in_progress`
- Target: Add extractors for analysis rule constants and fingerprints for active deterministic formulas.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-OPME-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-OPME-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; OpMe_System now machine-checks 49 active parameters and 7 active formulas while calibration, prompt/provider policy, and signoff evidence remain blocked under TASK-OPME-B-001.; status: in_progress; target: Add extractors for analysis rule constants and fingerprints for active deterministic formulas.; +1 more

## Next Task

`GOV-SEMANTIC-OPME-001` - Add extractors for analysis rule constants and fingerprints for active deterministic formulas.

- Status: `in_progress`
- Acceptance: ACC-SEMANTIC-OPME-001
- Selection rationale: status=in_progress; phase=B; current_phase=B; unmet_dependencies=none; score=133
