# PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN

- Timestamp: `2026-06-30T10:41:36+10:00`
- Task IDs: `S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN`; parent `S2PLT02-TERMINAL-DELIVERY-PROOF`; current V7 task `S2PMT07`; acceptance `ACC-S2PLT02-2D`.
- Status: `blocked`.
- State hash: `81d89c0b03458d4b5cc569ae1d994b7d02ef36dfa89377516f7968619d03e878`.

## Goal

Add a no-write S2PLT02 terminal delivery proof capture plan. It consumes the current terminal delivery input inventory, lists the exact blocked inputs, and exposes the ordered next steps for a future controlled real capture window without sending mail, enabling scheduler, or writing the live terminal proof artifact.

## Current Facts

| Field | Value |
|---|---|
| `cli_command` | `adp plan-s2plt02-terminal-delivery-proof-capture --repo-root . --generated-at 2026-06-30T10:41:36+10:00 --json` |
| `cli_exit_code` | `2` |
| `blocked_by_missing_inputs` | `SECOND_REAL_DELIVERY_DAY`; `EIGHT_REAL_EMAILS`; `REAL_SCHEDULER_PROOF`; `S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT` |
| `observed_real_delivery_days` | `1 / 2` |
| `observed_real_email_count` | `4 / 8` |
| `next_executable_step` | `CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY` |
| `terminal_delivery_proof_ready` | `false` |
| `artifact_written` | `false` |
| `real_smtp_send_enabled` | `false` |
| `scheduler_install_enabled` | `false` |
| `daily_operation_enabled` | `false` |

## Capture Steps

1. `CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY`: only after explicit owner authorization, capture the second consecutive real M1-M4 SMTP delivery-day manifest; this plan itself must not send mail.
2. `COLLECT_REAL_LAUNCHD_SCHEDULER_PROOF`: collect and validate real launchd scheduler evidence without installing or enabling scheduler jobs.
3. `BUILD_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT`: run `adp build-s2plt02-terminal-delivery-proof-artifact-draft --delivery-manifest DAY1.json --delivery-manifest DAY2.json --scheduler-proof REAL-SCHEDULER-PROOF.json --json`.
4. `RUN_INDEPENDENT_TERMINAL_PROOF_REVIEW`: independent final reviewer checks the draft, manifests, scheduler proof, and no-production side-effect fields.
5. `WRITE_REVIEWED_TERMINAL_DELIVERY_PROOF_ARTIFACT`: only after independent review may `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` be written.
6. `VALIDATE_TERMINAL_DELIVERY_PROOF_ARTIFACT`: run `adp validate-s2plt02-terminal-delivery-proof --repo-root . --json`.

## Validation

- TDD red: focused final-gate test failed before `build_s2plt02_terminal_delivery_proof_capture_plan_state` existed.
- Focused final-gate and CLI capture-plan tests: `2 passed`.
- CLI capture plan returns blocked / exit 2 with the missing input set above.

## Boundaries

This phase does not collect real SMTP evidence, does not prove scheduler execution, does not write `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`, does not send SMTP, does not enable/install/bootstrap/kickstart scheduler, does not upload Release assets, does not restore production, does not mutate public schema/DB/production queues/source adapters/ranking, does not change CURRENT/V7 contracts, does not enable DAILY_OPERATION, does not accept S2PLT02/S2PLT03/S2PLT04/S2PMT07, and does not claim integrated production acceptance.

## Evidence

- `governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN-20260630.json`
- `arxiv-daily-push/src/arxiv_daily_push/stage2_final_gate.py`
- `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- `arxiv-daily-push/tests/test_stage2_final_gate.py`
- `arxiv-daily-push/tests/test_cli.py`

## Required Next Actions

1. Collect a second consecutive real M1-M4 SMTP service day under the already validated live authorization.
2. Reach eight total real M1-M4 email records across two consecutive service dates.
3. Collect and validate a real launchd scheduler proof manifest.
4. Run the stdout-only terminal delivery proof artifact draft builder from the two real delivery manifests and scheduler proof manifest.
5. Route the draft through the independent final reviewer before writing and validating `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`.
