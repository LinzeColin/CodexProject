# Phase 11 Trial Start Gate

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-TRIAL-START-GATE-018`
Acceptance: `ADP-ACC-PHASE11-TRIAL-START-GATE`
Version: `0.11.17`
Status: `completed`

## Scope

- Added `adp-trial-start-v1` in `src/arxiv_daily_push/trial_start.py`.
- Added `adp plan-trial-start`.
- Added `schemas/trial_start.schema.json`.
- Added tests for passing start readiness, missing confirmation, missing durable
  refs, SMTP dry-run blocking, blocked preflight blocking, and CLI JSON output.
- Updated the production trial runbook, README, changelog, version files, and
  governance records.

## Acceptance Evidence

- A passing report requires:
  - explicit `--confirm-start`;
  - a passing production preflight report;
  - a ready trial bootstrap plan;
  - a ready production scheduler plan;
  - a passing live arXiv source batch;
  - a real sent SMTP report whose `delivery_ref` matches `--smtp-ref`;
  - a real created Release report whose `release_ref` matches `--release-ref`;
  - durable refs for default branch, runner, preflight, source ingest, SMTP,
    Release, scheduler, trial state, and the trial start gate artifact.
- The start gate performs no side effects and does not claim production
  acceptance.

## Validation

- Focused command:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start.py arxiv-daily-push/tests/test_trial_bootstrap.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_source_ingest.py arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_release_delivery.py arxiv-daily-push/tests/test_cli.py -q`
- Focused result: `34 tests OK`.

Full project and governance validation is recorded in
`governance/run_manifests/ADP-PHASE11-TRIAL-START-GATE-20260622.json`.

## Current Boundary

This gate proves only that the preconditions for starting a real trial are
represented and fail closed. It does not merge the branch, enable GitHub
schedules, send SMTP, create Releases, mutate the trial ledger, generate media,
retain local cache/model artifacts, or claim 30-day operational acceptance.

## Remaining Risks

- Real trial start still requires default-branch runner evidence and archived
  real SMTP, Release, source ingest, preflight, and start-gate refs.
- Production acceptance remains blocked until 30 unique daily production
  evidence entries, weekly/monthly replay, recovery drill, and resource
  telemetry evidence all pass.

## Rollback

Revert trial start gate, CLI command, schema, tests, runbook/docs/governance
updates, and restore version `0.11.16`.
