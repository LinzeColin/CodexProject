# Phase 11 Trial Ledger Update

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-TRIAL-LEDGER-012`
Acceptance: `ADP-ACC-PHASE11-TRIAL-LEDGER`
Version: `0.11.11`
Generated: `2026-06-21`

## Objective

Close the gap between production-ready scheduled daily-run artifacts and the
30-day trial evidence package by appending one validated daily evidence entry at
a time.

## Implemented

- Added `src/arxiv_daily_push/trial_ledger.py`.
- Added `adp update-trial-ledger`.
- Added `schemas/trial_ledger.schema.json`.
- Updated scheduled execution daily-run evidence to include date, source ID,
  scheduled local time, and publication safety fields needed by the trial
  validator.
- Updated `.github/workflows/arxiv-daily-push-scheduled.yml` to upload an
  `adp-trial-ledger-update` artifact after daily-run execution.
- Updated the scheduler validator, tests, runbook, and governance records.

## Safety Boundary

- The ledger updater accepts only `daily-run` scheduled execution reports with
  `production_evidence_ready=true`.
- Dry-run SMTP, dry-run Release, degraded non-production evidence, missing
  daily evidence refs, missing P0 traceability, unsupported claims, misleading
  failure output, and duplicate daily/source/publication IDs are blocked.
- Existing ledger booleans can be upgraded only when explicit evidence flags or
  production-ready scheduled refs are present.
- Weekly/monthly replay and recovery drill evidence are not auto-completed by a
  daily-run update.
- The update report may append a daily entry while the embedded
  `adp-trial-evidence-v1` report remains blocked until all 30-day gates pass.

## Current Status

`pass for trial ledger update contract`

This phase does not claim the 30-day trial has started or passed. Production
acceptance remains blocked until the runner provides live source, real SMTP,
real Release, resource, weekly/monthly replay, recovery drill, and 30 unique
daily evidence entries.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_target3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ledger.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`: 19 focused tests OK.
- `bash -n /tmp/update-trial-evidence-ledger.sh`: scheduled workflow ledger
  step syntax OK.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- The production runner, GitHub variables, SMTP secrets, Release target, and
  default-branch schedule are not verified here.
- Live arXiv fetch still depends on runner TLS/CA health and arXiv availability.
- Real 30-day acceptance still requires weekly/monthly replay, recovery drill,
  resource telemetry, and at least 30 unique daily production evidence entries.

## Rollback

Revert `trial_ledger.py`, the `update-trial-ledger` CLI command, scheduled
workflow ledger artifact changes, `trial_ledger.schema.json`, related tests and
governance records, and restore version `0.11.10`.
