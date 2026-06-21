# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `Alpha`
- Path: `Alpha`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:strategy-tournament-v0, MOD-002:risk-score-v0, MOD-003:pre-trade-gate-v0, +6`
- Parameter profile versions: `agent_loop:agent-loop-v0, paper_broker_defaults:paper-broker-v0, strategy_tournament_constants:strategy-tournament-v0, +1`
- Current iteration: `ITER-20260621-ALPHA-001`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-ALPHA-in-progress`
- Model count: `9`
- Formula count: `9`
- Parameter count: `55`
- Task count: `9`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `68`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-ALPHA-001`

## Latest Run

- Event: `EVENT-ALPHA-20260621-002`
- Task: `GOV-SEMANTIC-ALPHA-001`
- Summary: Validated Alpha semantic extractor rollout locally and recorded blocked focused tests caused by missing local PyYAML dependency.
- Model delta: No runtime model behavior change; validation confirms 9 active formula fingerprints match live code symbols.
- Parameter delta: No active value change; validation confirms 42 active parameter active values match live code/config selectors; 13 branch-rule parameters remain HUMAN_REVIEW_REQUIRED.
- Tests: UNKNOWN
- Evidence: Alpha/docs/governance/parameter_registry.csv, Alpha/docs/governance/formula_registry.yaml, governance/run_manifests/GOV-SEMANTIC-ALPHA-EXTRACT-001.json, tests/governance/test_project_governance_validator.py
- Result: `PASS_WITH_BLOCKED_ADDITIONAL_CHECK`
- Rollback: Revert this branch changes; no Alpha runtime rollback is required.

## Current Blockers

live execution policy and production validation remain blocked under `TASK-ALPHA-B-001`.

## Semantic Coverage

- Status: `in_progress`
- Target: Add machine source selectors for active parameters and implementation fingerprints for active formulas.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-ALPHA-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-ALPHA-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; Alpha now machine-checks 42 active parameters and 9 active formulas while 13 branch-rule parameters remain HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-ALPHA-001.; status: in_progress; target: Add machine source selectors for active parameters and implementation fingerprints for active formulas.; +1 more

## Next Task

`TASK-ALPHA-B-001` - Resolve production validation and execution-policy UNKNOWN items before release readiness.

- Status: `blocked`
- Acceptance: ACC-ALPHA-B-001
- Selection rationale: status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=152
