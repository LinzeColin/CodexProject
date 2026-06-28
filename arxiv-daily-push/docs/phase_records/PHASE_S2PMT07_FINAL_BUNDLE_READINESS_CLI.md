# S2PMT07 Final Bundle Readiness CLI

- Timestamp: `2026-06-28T22:44:37+10:00`
- Task ID: `S2PMT07-FINAL-BUNDLE-READINESS-CLI`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Status: `blocked_precheck_ready`

## What Changed

- Added CLI command: `adp validate-final-acceptance-bundle --repo-root . --json`.
- The command reuses the existing S2PMT07 final acceptance bundle readiness builder and validator.
- Missing real final-bundle artifacts return `status=blocked` and exit code `2`.
- `readiness_validation_errors=[]` means the readiness payload is internally valid, not that S2PMT07 passed.

## Current Observed State

- `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json`: present and recognized by the readiness state.
- Still missing:
  - `FINAL_ACCEPTANCE_BUNDLE/manifest.json`
  - `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`
  - `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`
  - `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json`
  - `FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml`
  - `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`
  - `HANDOFF/00_下一Agent先读.md`
- Current P0/P1 inherited blockers remain `P0=8 / P1=37`.
- `production_acceptance_claimed=false`
- `integrated_production_accepted=false`
- `daily_operation_enabled=false`

## Verification

- RED: focused CLI test failed because `validate-final-acceptance-bundle` was not a recognized command.
- GREEN: focused CLI readiness test passed after parser/dispatcher implementation.
- Command payload state hash observed from repo root: `6dda08bd9d205450b13a5ec00b1f8d6dd919e7c56f1b463d0e246b83b7cbf213`.

## Boundaries

This task does not create live final-bundle artifacts, assign an independent final reviewer, create P0/P1 zero proof, close inherited P0/P1 findings, complete S2PLT04, execute final commands, enable SMTP, install/enable scheduler, upload Release assets, execute restore, mutate public schema/DB/queue/source/ranking, change CURRENT/V7, enable DAILY_OPERATION, or claim integrated production acceptance.

## Next Step

Owner/coordinator must supply the real final-bundle artifacts, starting with `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`, then rerun the CLI readiness check from the repository root.
