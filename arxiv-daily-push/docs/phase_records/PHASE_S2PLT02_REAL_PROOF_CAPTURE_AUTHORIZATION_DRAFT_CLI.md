# PHASE_S2PLT02_REAL_PROOF_CAPTURE_AUTHORIZATION_DRAFT_CLI

- Timestamp: `2026-06-29T20:57:12+10:00`
- Task IDs: `S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI`; parent `S2PLT02`; current V7 task `S2PMT07`; acceptance `ACC-S2PLT02-2D`.
- Status: `draft_s2plt02_real_proof_capture_authorization_artifact_cli_ready_no_write_no_production`.
- Readiness state hash: `819b1c3911892ce861fd5ba5bdde0dc381e303076beea684f35eb94c75975463`.
- Draft state hash: `b464cecac874de888d5ca3e025361ac523a6a89cabe7de560ace5d48e79f2eff`.
- Draft authorization hash: `sha256:259b91d676acdc59a5b529140e15220eb0c21cd1987bb2250d0ced89a9797eb0`.

## Goal

Add a stdout-only CLI that builds a valid S2PLT02 real-proof capture authorization artifact draft from explicit owner inputs. This reduces future schema/hash mistakes if the owner later approves real SMTP/scheduler proof capture, but it does not write the live authorization artifact and does not authorize proof capture.

## Current Facts

| Field | Value |
|---|---|
| `cli_command` | `adp build-s2plt02-real-proof-capture-authorization-artifact-draft --owner-id owner_or_coordinator --owner-role owner --generated-at 2026-06-29T20:57:12+10:00 --readiness-state-hash 819b1c3911892ce861fd5ba5bdde0dc381e303076beea684f35eb94c75975463 --json` |
| `cli_exit_code` | `0` |
| `status` | `draft` |
| `artifact_path` | `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json` |
| `authorization_artifact_written` | `false` |
| `authorization_artifact_present_in_repo` | `false` |
| `authorization_gate_satisfied_by_this_command` | `false` |
| `real_proof_capture_authorized_by_this_command` | `false` |
| `validation_errors` | `[]` |
| `real_smtp_send_enabled` | `false` |
| `scheduler_install_enabled` | `false` |
| `production_acceptance_claimed` | `false` |

## Required Next Actions

1. Owner/coordinator must explicitly approve or reject real SMTP/scheduler proof capture.
2. If approved, a human or follow-up task may write the reviewed JSON to `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`.
3. Re-run `validate-s2plt02-real-proof-capture-authorization --path FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json --expected-readiness-state-hash 819b1c3911892ce861fd5ba5bdde0dc381e303076beea684f35eb94c75975463 --json`.
4. Only a passing live authorization artifact can unlock second-day real SMTP/scheduler proof capture.

## Validation

- TDD red: focused stage2 final-gate test failed before `build_s2plt02_real_proof_capture_authorization_artifact_draft_state` existed.
- TDD red: focused CLI test failed before `build-s2plt02-real-proof-capture-authorization-artifact-draft` was a recognized command.
- Focused green tests passed for the new builder and CLI.
- The CLI output validated its embedded draft artifact with no validation errors.
- `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json` remains absent.

## Boundaries

This run does not create or write the live authorization artifact. It does not authorize real proof capture, send SMTP, install/enable/kickstart scheduler, upload Release assets, execute restore, mutate public schema/DB/production queues/source adapters/ranking, change CURRENT/V7 contracts, enable DAILY_OPERATION, accept S2PLT02/S2PLT03/S2PLT04/S2PMT07, or claim integrated production acceptance.

## Evidence

- `governance/run_manifests/ADP-S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION-DRAFT-CLI-20260629.json`
- `arxiv-daily-push/src/arxiv_daily_push/stage2_final_gate.py`
- `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- `arxiv-daily-push/tests/test_stage2_final_gate.py`
- `arxiv-daily-push/tests/test_cli.py`
