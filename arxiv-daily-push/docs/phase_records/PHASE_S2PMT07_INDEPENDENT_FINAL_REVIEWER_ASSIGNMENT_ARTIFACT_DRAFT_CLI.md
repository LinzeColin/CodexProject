# PHASE_S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_DRAFT_CLI

- Project: `arxiv-daily-push`
- Task: `S2PMT07-INDEPENDENT-FINAL-REVIEWER-ASSIGNMENT-ARTIFACT-DRAFT-CLI`
- Parent task: `S2PMT07`
- Acceptance: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-29T00:40:23+10:00`
- Gate: `S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_DRAFT_CLI_READY_NO_ASSIGNMENT_NO_PRODUCTION`
- Result: `blocked_assignment_artifact_draft_cli_ready_no_assignment_no_production`
- Fact level: `EXTRACTED`

## What Changed

`adp build-final-reviewer-assignment-artifact-draft ... --json` now builds a stdout-only draft payload for the future `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` artifact from explicit owner/coordinator inputs.

The command preserves the exact artifact field order required by `validate-final-reviewer-assignment`, calculates `assignment_hash`, and reports validation errors before any owner/coordinator writes the live artifact.

## Current CLI Facts

- `status`: `draft`
- `exit_code`: `0`
- `artifact_path`: `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`
- `assignment_hash`: `sha256:1b31de0eae2283814fa5e458d69700774f2ae8441187a3e8f0fd3a03740c2dec`
- `state_hash`: `5bfa7b97e6a318a5ee98ba4b56ee65b2d140fe877d94931cfc350c644cc93ee3`
- `assignment_artifact_written`: `false`
- `assignment_artifact_present_in_repo`: `false`
- `assignment_gate_satisfied_by_this_command`: `false`
- `independent_final_reviewer_assigned_by_this_command`: `false`
- `validation_errors`: `[]`

## Validation

- Red: command was not recognized by argparse.
- Red: JSON output initially sorted nested artifact keys, which would make a copied artifact fail the existing field-order validator.
- Green: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_assignment_draft_order_green2 PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q` -> 18 tests OK.
- Direct CLI sample preserves artifact field order and returns exit 0 with draft status.

## Boundary

This phase does not write `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`, does not assign an independent final reviewer, does not satisfy the assignment gate, does not record a closure decision, does not close P0/P1, does not complete S2PLT04, does not execute final commands, and does not accept production.

No SMTP, scheduler, Release, restore, public schema, DB migration, production queue, source adapter, ranking, CURRENT/V7, V7.1 baseline, V7.2 contract, DAILY_OPERATION, or integrated production acceptance side effect is changed.

## Next Required Step

Owner/coordinator must review the draft, select the real independent final reviewer, and write a real `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json` artifact before independent final review can proceed.
