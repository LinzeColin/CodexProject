# S2PLT02 Terminal Capture Window Runtime State Sync

- Timestamp: 2026-06-30 14:31:47 Australia/Sydney
- Task ID: `S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC`
- Parent task: `S2PLT02-TERMINAL-DELIVERY-PROOF`
- Acceptance: `ACC-S2PLT02-2D`
- Status: `blocked`

## Objective

Expose the current launchd runtime state inside the S2PLT02 terminal capture-window audit so loaded LaunchAgents with calendar triggers cannot be misread as real scheduler proof while user-domain disabled overrides remain active.

## Current Facts

| Field | Value |
|---|---|
| CLI | `audit-s2plt02-terminal-capture-window --repo-root . --state-dir /Users/linzezhang/.adp/arxiv-daily-push --candidate-service-dates 2026-06-28,2026-06-29,2026-06-30 --json` |
| CLI exit | `2` |
| State hash | `cebee97e51f4cc6231a10b787aa65b17eed10c951330dea4328cd18d73ed912a` |
| Candidate service dates | `2026-06-28`, `2026-06-29`, `2026-06-30` |
| Dry-run service dates | `2026-06-29`, `2026-06-30` |
| Real sent candidate emails | `4` |
| Dry-run candidate emails | `8` |
| Terminal email credit | `4 / 8` |
| LaunchAgents loaded | `true` |
| LaunchAgents not running | `true` |
| LaunchAgents have calendar triggers | `true` |
| LaunchAgents disabled by user-domain override | `true` |
| Scheduler runtime evidence status | `launchagents_loaded_but_disabled_not_terminal_scheduler_proof` |
| Real scheduler proven | `false` |

## Decision

The current runtime evidence remains nonterminal. Loaded launchd services and calendar triggers are useful runtime evidence, but they do not prove S2PLT02 real scheduler execution while disabled overrides are active and the second real M1-M4 SMTP day is missing.

## Blocking Reasons

- `second_consecutive_real_m1_m4_smtp_day_missing`
- `eight_real_emails_not_proven`
- `real_launchd_scheduler_proof_missing`
- `adp_allow_smtp_send_false`
- `adp_launchagents_disabled_by_user_domain_override`
- `s2plt02_terminal_delivery_proof_artifact_missing`

## Evidence

- [runtime-state sync manifest](../../../governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-RUNTIME-STATE-SYNC-20260630.json)
- [stage2_final_gate.py](../../src/arxiv_daily_push/stage2_final_gate.py)
- [cli.py](../../src/arxiv_daily_push/cli.py)
- [test_stage2_final_gate.py](../../tests/test_stage2_final_gate.py)
- [test_cli.py](../../tests/test_cli.py)

## No-Production Boundary

This task did not send SMTP, enable/install/kickstart scheduler, upload Release assets, execute restore, modify CURRENT/V7/V7.1/V7.2, mutate public schema/DB/source/ranking/queue, enable DAILY_OPERATION, close P0/P1, accept S2PLT02/S2PLT03/S2PLT04/S2PMT07, or claim integrated production acceptance.
