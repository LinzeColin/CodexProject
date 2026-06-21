# Phase 11 Trial Start Workflow

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-TRIAL-START-WORKFLOW-019`
Acceptance: `ADP-ACC-PHASE11-TRIAL-START-WORKFLOW`
Version: `0.11.18`
Status: `completed`

## Scope

- Added manual workflow `.github/workflows/arxiv-daily-push-trial-start.yml`.
- Added `adp-trial-start-workflow-v1` in
  `src/arxiv_daily_push/trial_start_workflow.py`.
- Added `adp plan-trial-start-workflow`.
- Added `schemas/trial_start_workflow.schema.json`.
- Added tests for manual-only workflow dispatch, preflight-first ordering,
  artifact coverage, durable ref arguments, side-effect variable gates, secret
  safety, and CLI JSON output.
- Updated the production trial runbook, README, changelog, version files, and
  governance records.

## Acceptance Evidence

- The workflow is `workflow_dispatch` only and has no cron schedule.
- The self-hosted runner job runs only after `confirm_trial_start=true`.
- Production preflight runs before live source, SMTP, Release, or start-gate
  work.
- Live arXiv source ingest must pass before SMTP or Release probes.
- Real SMTP and Release probes are gated by `ADP_ALLOW_SMTP_SEND` and
  `ADP_ALLOW_RELEASE_UPLOAD`.
- The workflow uploads:
  - `adp-trial-start-preflight`;
  - `adp-trial-start-bootstrap-plan`;
  - `adp-trial-start-scheduler-plan`;
  - `adp-trial-start-source-batch`;
  - `adp-trial-start-smtp-delivery`;
  - `adp-trial-start-release-delivery`;
  - `adp-trial-start-gate`.
- The start gate receives durable refs for default branch, runner, preflight,
  source ingest, SMTP, Release, scheduler, trial state, and trial start gate
  artifacts.
- The workflow maps SMTP secret names and does not read Codex auth or log
  secret values.

## Validation

- Focused command:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_trial_start.py arxiv-daily-push/tests/test_trial_bootstrap.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`
- Focused result: `20 tests OK`.

Full project and governance validation is recorded in
`governance/run_manifests/ADP-PHASE11-TRIAL-START-WORKFLOW-20260622.json`.

## Current Boundary

This phase proves the default-branch trial start evidence workflow contract and
validator. It does not merge the workflow to the default branch, run the
workflow, enable schedules, send SMTP locally, create Releases locally, mutate
the trial ledger, generate media, retain local cache/model artifacts, or claim
30-day operational acceptance.

## Remaining Risks

- Real trial start evidence still requires running the workflow from the default
  branch on the private runner with configured GitHub variables and SMTP
  secrets.
- Production acceptance remains blocked until live source pass on the runner,
  real SMTP and Release refs, resource telemetry, weekly/monthly replay,
  recovery drill, and 30 unique daily production evidence entries are archived
  and validated.

## Rollback

Revert trial start workflow, validator, CLI command, schema, tests,
runbook/docs/governance updates, and restore version `0.11.17`.
