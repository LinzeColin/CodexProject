# S2PMT07 Final Command Execution CLI Validator

## Metadata

- Task ID: `S2PMT07-FINAL-COMMAND-EXECUTION-CLI-VALIDATOR`
- Parent task: `S2PMT07`
- Acceptance ID: `ACC-S2PMT07-FINAL-REVIEW`
- Timestamp: `2026-06-28T23:41:05+10:00`
- Status: `blocked_final_command_execution_cli_validator_ready_artifact_missing_no_production`
- Product version: `0.23.1`

## Scope

Expose the existing final-command execution artifact validator through the ADP CLI:

```bash
adp validate-final-command-execution --path FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json --json
```

The command wraps `build_final_command_execution_validation_state()`. It validates a future `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json` payload without executing commands, creating evidence, accepting the final bundle, or mutating any production state.

## Current Facts

- `artifact_path=FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`
- `command_execution_present=false`
- `status=blocked`
- `validation_errors=["final_command_execution_missing"]`
- `all_required_commands_passed=false`
- `final_commands_executed_by_payload=false`
- `production_acceptance_claimed=false`
- `integrated_production_accepted=false`
- `daily_operation_enabled=false`
- `state_hash=a516f2d33fcd1e8de56d85ebf4bca6587757bf1f415502b97edbe5bed6298fbb`

## Validation

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_final_command_cli_red PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - Failed as expected because `validate-final-command-execution` was not a registered CLI command.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_final_command_cli_green PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_cli.py -q`
  - `15 OK`

## Boundaries

This change does not create `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`, does not execute final commands, does not assign an independent final reviewer, does not record an independent closure decision, does not create P0/P1 zero proof, does not close inherited P0/P1, does not complete S2PLT04, does not create or accept the final bundle, does not create a live handoff, does not enable SMTP, scheduler, Release, restore, DAILY_OPERATION, or integrated production acceptance, and does not change CURRENT/V7 contracts.

## Next Required Action

Owner/coordinator must still supply a real independent final reviewer assignment artifact before any independent final reviewer can execute and record final commands as evidence.
