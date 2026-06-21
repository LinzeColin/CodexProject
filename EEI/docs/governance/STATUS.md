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
- Current iteration: `ITER-20260621-015`
- Current phase: `D`
- Current gate: `TASK-T1307-A209-RUNNER-REPAIR-REMOTE-CI`
- Model count: `12`
- Formula count: `12`
- Parameter count: `61`
- Task count: `124`
- Unbound event count: `14`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `135`
- Semantic coverage: `planned`
- Semantic rollout task: `GOV-SEMANTIC-EEI-001`

## Latest Run

- Event: `EVENT-20260621-017`
- Task: `TASK-T1307`
- Summary: Recorded remote CI PASS for the T1307/A209 operator soak parallel-window runner repair commit.
- Model delta: No scoring formula change; remote CI evidence only.
- Parameter delta: No canonical parameter behavior change; remote CI evidence only.
- Tests: GitHub Actions EEI validation run 27894602887 / job 82543882466, GitHub Actions Project Governance run 27894602898
- Evidence: GitHub Actions run 27894602887, GitHub Actions job 82543882466, GitHub Actions Project Governance run 27894602898, EEI/docs/phase/MVP_DEVELOPMENT_RECORD.md
- Result: `REMOTE_CI_PASS_A209_RUNNER_REPAIR_A209_A206_STILL_IN_PROGRESS`
- Rollback: Revert the remote evidence update, regenerate release artifacts with remote_status=PENDING, and rerun validation.

## Current Blockers

A209 remains open until committed 4h and 24h operator soak evidence exists.

## Semantic Coverage

- Status: `planned`
- Target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.
- Evidence/rollout: acceptance_id: ACC-SEMANTIC-EEI-001; evidence_ref: EEI/docs/governance/OWNER_STATUS.md; owner: project owner; rationale: Review6-D rollout guard; EEI has rich legacy registries but no root semantic extractor profile yet.; status: planned; target: Bind EEI active parameter_catalog and model/formula registries to machine extractors without changing runtime behavior.; +1 more

## Next Task

`TASK-T1307` - Run 4h and 24h browser and worker soak tests for memory, timer, listener and retry stability

- Status: `in_progress`
- Acceptance: ACC-A209
- Selection rationale: status=in_progress; phase=D; current_phase=D; unmet_dependencies=none; score=102
