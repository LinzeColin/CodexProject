# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `OpenAIDatabase`
- Path: `OpenAIDatabase`
- CI mode: `required`
- Product version: `0.2.0`
- Model versions: `MOD-001:memory-candidate-v0, MOD-002:redaction-policy-v0, MOD-003:active-memory-v0, +8`
- Parameter profile versions: `codex_sync:codex-sync-parameters-v0, memory_analysis:memory-analysis-parameters-v0, memory_atlas:memory-atlas-parameters-v0, +2`
- Current iteration: `ITER-20260621-OAI-004`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-OAIDB-in-progress`
- Model count: `11`
- Formula count: `11`
- Parameter count: `92`
- Task count: `10`
- Unbound event count: `6`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `345`
- Semantic coverage: `in_progress`
- Semantic rollout task: `GOV-SEMANTIC-OAIDB-001`

## Latest Run

- Event: `GOV-SEMANTIC-OAIDB-STATUS-001`
- Task: `GOV-SEMANTIC-OAIDB-001`
- Summary: Bind generated dashboard, STATUS, and OWNER_STATUS outputs to the OpenAIDatabase semantic extractor rollout diff.
- Model delta: UNKNOWN
- Parameter delta: UNKNOWN
- Tests: python3 scripts/generate_governance_dashboard.py --write, python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic
- Evidence: GOVERNANCE_DASHBOARD.md, OpenAIDatabase/docs/governance/STATUS.md, OpenAIDatabase/docs/governance/OWNER_STATUS.md
- Result: `RETRY: initial changed-only run failed because generated STATUS and OWNER_STATUS were not listed in the latest development event; this append-only event records the complete diff set before rerun.`
- Rollback: UNKNOWN

## Current Blockers

remaining complex branch rules, TypeScript writeback semantics, and heuristic calibration evidence are HUMAN_REVIEW_REQUIRED or UNKNOWN under `GOV-SEMANTIC-OAIDB-001` and `TASK-OAI-B-001`

## Semantic Coverage

- Status: `in_progress`
- Target: Add extractors for memory-analysis trigger rules, routing constants, and active formula fingerprints.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-OAIDB-001; evidence_ref: governance/run_manifests/GOV-SEMANTIC-OAIDB-EXTRACT-001.json; owner: project owner; rationale: Review6-D rollout guard; OpenAIDatabase now machine-checks 28 active parameters and 10 active formulas while remaining active parameters and FORM-010 stay HUMAN_REVIEW_REQUIRED under GOV-SEMANTIC-OAIDB-001.; status: in_progress; target: Add extractors for memory-analysis trigger rules, routing constants, and active formula fingerprints.; +1 more

## Next Task

`TASK-OAI-B-001` - Resolve UNKNOWN calibration evidence for heuristic weights and thresholds.

- Status: `blocked`
- Acceptance: ACC-OAI-B-001
- Selection rationale: status=blocked; phase=B; current_phase=B; unmet_dependencies=none; score=136
