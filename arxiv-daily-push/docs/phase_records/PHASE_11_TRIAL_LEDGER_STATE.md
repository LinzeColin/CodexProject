# Phase 11 Trial Ledger State Persistence

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-TRIAL-LEDGER-STATE-013`
Acceptance: `ADP-ACC-PHASE11-TRIAL-LEDGER-STATE`
Version: `0.11.12`
Generated: `2026-06-22`

## Objective

Allow the 30-day trial evidence ledger to continue across GitHub Actions runs by
restoring the previous state artifact before appending a new daily evidence
entry and uploading the updated state afterward.

## Implemented

- Added `adp export-trial-ledger-state`.
- Updated `.github/workflows/arxiv-daily-push-scheduled.yml` to grant
  `actions: read`, attempt `gh run download` of the previous
  `adp-trial-evidence-ledger` artifact, and use the restored JSON as the next
  `update-trial-ledger --path` input.
- Added export/upload of `adp-trial-evidence-ledger` only when the ledger update
  actually appends evidence.
- Updated the scheduler validator, tests, runbook, README, runtime example,
  version files, and governance records.

## Safety Boundary

- The workflow does not write trial state to Git.
- The state artifact contains only small JSON trial evidence, not media, model
  weights, credentials, Codex auth, GitHub tokens, SMTP secrets, or rendered
  cache output.
- If the previous artifact cannot be found, the first daily-run can start a new
  ledger; if an explicit configured path is supplied, that file takes priority.
- If the ledger update is blocked, `export-trial-ledger-state` exits non-zero
  and no replacement `adp-trial-evidence-ledger` state artifact is uploaded.
- A persisted ledger can still fail `adp-trial-evidence-v1` until all 30-day,
  scheduler, Release, SMTP, resource, weekly/monthly, and recovery gates pass.

## Current Status

`pass for trial ledger state persistence contract`

This phase does not claim that a real default-branch schedule has run, that
SMTP/Release production refs exist, or that 30 unique daily production evidence
entries have been collected.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ledger.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`: 15 focused tests OK.
- `bash -n /tmp/resolve-trial-ledger-state.sh`: scheduled workflow state
  restore step syntax OK.
- `bash -n /tmp/export-trial-evidence-ledger-state.sh`: scheduled workflow
  state export step syntax OK.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- Real artifact restore still depends on a default-branch workflow run, GitHub
  Actions artifact retention, a provisioned runner, and `gh` auth through the
  workflow token.
- Production acceptance still requires live source pass on the runner, real
  SMTP/Release refs, resource telemetry, weekly/monthly replay, recovery drill,
  and 30 unique daily production evidence entries.

## Rollback

Revert the `export-trial-ledger-state` CLI command, scheduled workflow state
restore/export artifact changes, related tests and governance records, and
restore version `0.11.11`.
