# Phase 11 Daily Input Builder

Project: `arxiv-daily-push`
Task: `ADP-PHASE11-DAILY-INPUT-BUILDER-011`
Acceptance: `ADP-ACC-PHASE11-DAILY-INPUT-BUILDER`
Version: `0.11.10`
Generated: `2026-06-21`

## Objective

Close the gap between live arXiv source ingest and scheduled daily execution by
turning a small `adp-live-arxiv-ingest-v1` source batch into a ranked daily
pipeline input package.

## Implemented

- Added `src/arxiv_daily_push/daily_input.py`.
- Added `adp build-daily-input`.
- Added `schemas/daily_input.schema.json`.
- Updated `.github/workflows/arxiv-daily-push-scheduled.yml` so 05:00 daily-run
  builds and uploads `adp-scheduled-source-batch` and
  `adp-scheduled-daily-input` when no `ADP_DAILY_INPUT_PATH` override is set.
- Updated scheduled execution to accept either the raw daily input package or
  the daily input builder report.
- Updated the scheduler validator, runbook, tests, and governance records.

## Safety Boundary

- Claims are generated only from arXiv Atom `<summary>` and metadata fields.
- The builder does not download PDFs, perform bulk harvesting, or infer peer
  review status from arXiv.
- The builder fails closed when the source batch is blocked, no new items exist,
  the selected item lacks an Atom summary, metadata conflicts block ranking, or
  all candidates are recently selected/ineligible.
- Daily-run still cannot count as production-ready evidence unless preflight,
  daily run, real SMTP, real Release, and resource evidence refs are all present.

## Current Status

`pass for daily input builder contract`

This phase does not claim that live arXiv ingest has passed on the production
runner, does not claim real SMTP or Release evidence, and does not start the
30-day operational trial.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_daily_input.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q`: 18 focused tests OK.

Full validation results are recorded in the governance run manifest after the
complete local validation suite.

## Remaining Risks

- The production runner, GitHub variables, SMTP secrets, Release target, and
  default-branch schedule are not verified here.
- Live arXiv fetch still depends on runner TLS/CA health and arXiv availability.
- Production acceptance still requires weekly/monthly replay, recovery drill,
  resource telemetry, and at least 30 unique daily production evidence entries.

## Rollback

Revert `daily_input.py`, the `build-daily-input` CLI command, scheduled workflow
daily-input artifact changes, `daily_input.schema.json`, related tests and
governance records, and restore version `0.11.9`.
