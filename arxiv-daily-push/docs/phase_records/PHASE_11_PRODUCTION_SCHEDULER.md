# Phase 11 Production Scheduler Gate

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-PRODUCTION-SCHEDULER-009`
Acceptance: `ADP-ACC-PHASE11-PRODUCTION-SCHEDULER`
Version: `0.11.8`
Generated: `2026-06-21`

## Objective

Add a fail-closed scheduled production workflow gate so the system has a
verifiable path for Australia/Sydney 04:45 health check, 05:00 daily run, and
05:10 watchdog execution without accidentally enabling production side effects.

## Implemented

- Added `.github/workflows/arxiv-daily-push-scheduled.yml`.
- Added `src/arxiv_daily_push/production_scheduler.py`.
- Added `adp plan-production-scheduler`.
- Added `schemas/production_scheduler.schema.json`.
- Added tests for timezone-aware schedule slots, production variable gates,
  preflight-first ordering, artifact upload, no Codex auth read, and no SMTP or
  Release side-effect commands.
- Updated the production trial runbook with scheduler gate validation and
  enablement boundaries.

## Safety Boundary

- The workflow declares `timezone: "Australia/Sydney"` for:
  - `04:45` health check;
  - `05:00` daily-run gate;
  - `05:10` watchdog.
- Scheduled runs skip by default unless `ADP_PRODUCTION_ENABLED=true`.
- Scheduled mode still fails closed unless `ADP_SCHEDULED_RUN_ENABLED=true`.
- Production preflight runs before any scheduled mode work.
- Scheduled preflight evidence is uploaded as `adp-scheduled-preflight`.
- The scheduler gate does not use `--allow-send`, `--allow-upload`, `gh release
  create`, or `gh release upload`.
- SMTP sending and Release upload remain controlled by their explicit delivery
  boundaries.

## Current Status

`pass for scheduler contract`

This phase does not claim the workflow has run on the default branch and does
not claim the 30-day trial has started. GitHub scheduled workflows run only from
the default branch, and production variables must remain unset until the private
runner and prerequisites pass.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`: 8 focused tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-scheduler --path . --generated-at 2026-06-21T05:00:00+10:00 --json`: scheduler plan emitted with `status=pass`.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- Schedule triggers will not run until this workflow is merged to the default
  branch.
- The private self-hosted runner and production GitHub variables are not
  verified here.
- Daily production execution is still blocked after preflight until the next
  controlled enablement phase.
- Production acceptance still requires CA trust repair, live source pass, real
  SMTP, private Release, weekly/monthly replay, recovery drill, and 30-day
  evidence.

## Rollback

Revert `.github/workflows/arxiv-daily-push-scheduled.yml`,
`production_scheduler.py`, the `plan-production-scheduler` CLI command,
`production_scheduler.schema.json`, related tests, runbook updates, and restore
version `0.11.7`.
