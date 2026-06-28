# S2PMT07 Independent Final Closure Decision Owner Packet CLI

## Metadata

- Task ID: `S2PMT07-INDEPENDENT-FINAL-CLOSURE-DECISION-OWNER-PACKET-CLI`
- Parent task: `S2PMT07`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-28T23:04:29+10:00`
- Status: `blocked_owner_packet_cli_ready_no_closure_no_production`
- Product version: `0.23.1`

## Scope

Expose the existing independent final closure decision owner/reviewer packet through the ADP CLI:

```bash
adp build-final-closure-decision-owner-packet --json
```

The command wraps the existing `build_independent_final_closure_decision_owner_packet_state()` and `validate_independent_final_closure_decision_owner_packet_state()` helpers. It gives the owner/coordinator and future independent final reviewer the exact closure-decision artifact ref, required owner actions, assignment prerequisite, review input refs, P0/P1 open counts, and no-production flags without creating or accepting any live artifact.

## Current Facts

- `assignment_artifact_present=false`
- `independent_final_reviewer_assigned=false`
- `independent_final_closure_decision_present=false`
- `zero_proof_artifact_present=false`
- `p0_zero_proven=false`
- `p1_zero_proven=false`
- `closure_claimed=false`
- `observed_open_p0_findings=8`
- `observed_open_p1_findings=37`
- `owner_packet_validation_errors=[]`
- `state_hash=9d71fde46f0884146e80c97e4508bd1fc581423507c736906be7551504496178`

## Validation

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_closure_owner_cli_red PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push.tests.test_cli.CliTests.test_build_final_closure_decision_owner_packet_json_command -q`
  - Failed as expected because `build-final-closure-decision-owner-packet` was not a registered CLI command.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_closure_owner_cli_green PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push.tests.test_cli.CliTests.test_build_final_closure_decision_owner_packet_json_command -q`
  - `1 OK`

## Boundaries

This change does not create `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`, does not create `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`, does not record an independent closure decision, does not close inherited P0/P1, does not complete S2PLT04, does not create or accept the final bundle, does not execute final commands, does not create a live handoff, does not enable SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance, and does not change CURRENT/V7 contracts.

## Next Required Action

Owner/coordinator must still supply a real independent final reviewer assignment artifact before the future independent final reviewer can issue or reject the closure decision in the final bundle.
