# Phase 11 Scheduled Execution Driver

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-SCHEDULED-EXECUTION-010`
Acceptance: `ADP-ACC-PHASE11-SCHEDULED-EXECUTION`
Version: `0.11.9`
Generated: `2026-06-21`

## Objective

Connect the scheduled production workflow to a controlled execution driver so
04:45 health-check, 05:00 daily-run, and 05:10 watchdog runs can produce
structured evidence artifacts without silently claiming 30-day production
acceptance.

## Implemented

- Added `src/arxiv_daily_push/scheduled_execution.py`.
- Added `adp run-scheduled-production`.
- Added `schemas/scheduled_execution.schema.json`.
- Added tests for health-check evidence, disabled daily-run blocking,
  dry-run side-effect degradation, mocked real SMTP/Release evidence, and CLI
  JSON output.
- Updated `.github/workflows/arxiv-daily-push-scheduled.yml` to upload
  `adp-scheduled-execution` after the preflight artifact.
- Updated the scheduler validator to require the execution driver and execution
  artifact.

## Safety Boundary

- Production preflight must pass before a scheduled mode can become useful
  production evidence.
- Daily-run remains blocked unless `ADP_SCHEDULED_RUN_ENABLED=true`.
- Real SMTP requires `ADP_ALLOW_SMTP_SEND=true` and the SMTP environment keys.
- Real Release upload requires `ADP_ALLOW_RELEASE_UPLOAD=true`,
  `ADP_RELEASE_TARGET`, `gh`, and safe release assets.
- A dry-run email or dry-run Release creates `degraded` evidence with
  `exit_code=2`; it cannot be counted as Phase 11 production acceptance.
- The driver never reads `~/.codex/auth.json` and never logs SMTP secret values,
  email body text, Release notes, `gh` stdout, or `gh` stderr.

## Current Status

`pass for scheduled execution driver contract`

This phase does not claim the workflow has run on the default branch and does
not claim the 30-day production trial has started. It creates the missing
runtime bridge between the scheduler gate and the evidence validator.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_target3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`: 13 focused tests OK.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- The default branch schedule, private self-hosted runner, GitHub variables, and
  SMTP/Release secrets are not verified here.
- Daily production still needs a real daily input/content-generation source,
  live arXiv source pass, and real SMTP/Release evidence before 30-day trial
  evidence can accumulate.
- Production acceptance still requires weekly/monthly replay, recovery drill,
  resource telemetry, and at least 30 unique daily run evidence entries.

## Rollback

Revert `scheduled_execution.py`, the `run-scheduled-production` CLI command,
`scheduled_execution.schema.json`, scheduled workflow execution-artifact
changes, related tests and governance records, and restore version `0.11.8`.
