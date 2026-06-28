# S2PMT07 P0/P1 Zero Proof CLI Validator

## Metadata

- Task ID: `S2PMT07-P0-P1-ZERO-PROOF-CLI-VALIDATOR`
- Parent task: `S2PMT07`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-28T23:23:48+10:00`
- Status: `blocked_zero_proof_cli_validator_ready_artifact_missing_no_production`
- Product version: `0.23.1`

## Scope

Expose the existing P0/P1 zero-proof artifact validator through the ADP CLI:

```bash
adp validate-p0-p1-zero-proof --path FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json --json
```

The command wraps `build_p0_p1_zero_proof_artifact_validation_state()`. It validates a future `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` payload without creating, accepting, or mutating any final-bundle artifact.

## Current Facts

- `artifact_path=FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`
- `artifact_present=false`
- `status=blocked`
- `validation_errors=["p0_p1_zero_proof_artifact_missing"]`
- `p0_zero_proven_by_payload=false`
- `p1_zero_proven_by_payload=false`
- `production_acceptance_claimed=false`
- `integrated_production_accepted=false`
- `daily_operation_enabled=false`
- `state_hash=d50b2a0e3449204f62ed3103ad3c6aff283d2dac1a0a606ddefa78c142d96e4d`

## Validation

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_zero_proof_cli_red PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - Failed as expected because `validate-p0-p1-zero-proof` was not a registered CLI command.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_zero_proof_cli_green PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - `13 OK`

## Boundaries

This change does not create `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`, does not assign an independent final reviewer, does not record an independent closure decision, does not close inherited P0/P1, does not complete S2PLT04, does not create or accept the final bundle, does not execute final commands, does not create a live handoff, does not enable SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance, and does not change CURRENT/V7 contracts.

## Next Required Action

Owner/coordinator must still supply a real independent final reviewer assignment artifact before any independent final reviewer can provide a real zero-proof artifact and closure decision.
