# PHASE_S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_CLI

- Project: `arxiv-daily-push`
- Task: `S2PMT07-FINAL-BUNDLE-PREREQUISITE-PLAN-CLI`
- Parent task: `S2PMT07`
- Acceptance: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-29T00:14:34+10:00`
- Gate: `S2PMT07_FINAL_BUNDLE_PREREQUISITE_PLAN_CLI_READY_NO_ARTIFACTS_NO_PRODUCTION`
- Result: `blocked_final_bundle_prerequisite_plan_cli_ready_no_artifacts_no_production`
- Fact level: `EXTRACTED`

## What Changed

`adp plan-final-bundle-prerequisites --json` now exposes the S2PMT07 final-bundle prerequisite plan from the CLI. The plan is read-only and fail-closed.

The plan consumes the committed `FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json` artifact, so the `NO_PRODUCTION_SIDE_EFFECT_ATTESTATION` step is `pass`. The first blocked step is still `INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION`.

## Current CLI Facts

- `status`: `blocked`
- `exit_code`: `2`
- `state_hash`: `e8ccb6bb749fdb79007f7c76d962166e31d4a0f84dffc5c3c2fa247570abefb7`
- `next_required_step`: `INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_VALIDATION`
- `NO_PRODUCTION_SIDE_EFFECT_ATTESTATION`: `pass`
- `ready_for_final_bundle_manifest`: `false`
- `all_required_steps_passed`: `false`
- `plan_validation_errors`: `[]`
- `blocking_reasons`: `independent_final_reviewer_assignment_missing;p0_p1_zero_proof_artifact_missing;s2plt04_completion_report_missing;final_command_execution_missing;next_agent_handoff_missing;independent_review_signoff_missing;final_acceptance_bundle_manifest_missing;inherited_v7_1_p0_findings_open;inherited_v7_1_p1_findings_open`

## Validation

- Red: command was not recognized, and the prerequisite plan did not consume the committed no-production attestation.
- Green: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_plan_prereq_green2 PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py arxiv-daily-push/tests/test_stage2_final_gate.py -q` -> 97 tests OK.
- Direct CLI `main(["plan-final-bundle-prerequisites", "--json"])` returns exit 2 with `status=blocked` by design.

## Boundary

This phase does not create final-bundle artifacts, does not assign an independent final reviewer, does not record a closure decision, does not close P0/P1, does not complete S2PLT04, does not execute final commands, and does not accept production.

No SMTP, scheduler, Release, restore, public schema, DB migration, production queue, source adapter, ranking, CURRENT/V7, V7.1 baseline, V7.2 contract, DAILY_OPERATION, or integrated production acceptance side effect is changed.

## Next Required Step

Owner/coordinator must supply a real `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` artifact before independent final review can proceed.
