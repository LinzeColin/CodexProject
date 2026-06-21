# Phase 11 Trial Replay Evidence

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015`
Acceptance: `ADP-ACC-PHASE11-TRIAL-REPLAY-EVIDENCE`
Status: `PASS_FOR_REPLAY_EVIDENCE_CONTRACT`
Version: `0.11.14`

## Scope

Add a fail-closed weekly/monthly replay evidence generator for the accumulated
30-day trial ledger.

## Implemented

- Added `src/arxiv_daily_push/trial_replay.py`.
- Added `adp build-trial-replay-evidence`.
- Added `schemas/trial_replay.schema.json`.
- Added tests for weekly/monthly replay pass, monthly coverage blocking,
  missing durable ref blocking, duplicate-date blocking, and CLI JSON output.
- Updated the production trial runbook so weekly/monthly evidence is generated
  and archived before it is merged into trial evidence via
  `annotate-trial-ops-evidence`.

## Guardrails

- The replay builder accepts only existing `daily_runs` entries with production
  daily run, Release, SMTP, and resource refs.
- Weekly replay requires at least 7 consecutive daily entries.
- Monthly replay requires at least 30 consecutive daily entries even if an input
  ledger attempts to lower `period.expected_days`.
- Duplicate daily dates, source IDs, or publication IDs block the report.
- A durable `replay_ref` is required before replay evidence can be verified.
- The builder does not send SMTP mail, upload Releases, fetch arXiv, generate
  media, mutate the trial ledger, or claim production acceptance.

## Result

`pass for replay evidence contract`

This phase does not claim a real weekly/monthly replay has already run.
Production acceptance remains blocked until the provisioned runner provides
live source, real SMTP, real Release, resource, weekly/monthly replay, recovery
drill, and 30 unique daily production evidence entries.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_replay.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_cli.py -q`: 16 focused tests OK.

## Remaining Risk

- Real replay evidence still requires actual weekly/monthly replay execution and
  a durable GitHub Actions artifact, private Release ref, or equivalent private
  evidence ref.
- Real production acceptance remains blocked until default-branch scheduled
  execution, live arXiv ingest on the runner, real SMTP/private Release refs,
  resource telemetry, recovery drill evidence, and 30 unique daily entries are
  archived.

## Rollback

Revert `trial_replay.py`, `build-trial-replay-evidence`, replay schema, tests,
runbook/docs/governance updates, and restore version `0.11.13`.
