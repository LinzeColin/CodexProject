# Phase 11 Trial Recovery Evidence

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016`
Acceptance: `ADP-ACC-PHASE11-TRIAL-RECOVERY-EVIDENCE`
Status: `PASS_FOR_RECOVERY_EVIDENCE_CONTRACT`
Version: `0.11.15`

## Scope

Add a fail-closed recovery drill evidence generator for a failed, blocked, or
degraded scheduled daily-run and a recovered production-ready rerun.

## Implemented

- Added `src/arxiv_daily_push/trial_recovery.py`.
- Added `adp build-trial-recovery-evidence`.
- Added `schemas/trial_recovery.schema.json`.
- Added tests for recovery pass, dry-run failure notification blocking, missing
  durable recovery ref blocking, non-production-ready recovery blocking, and CLI
  JSON output.
- Updated the production trial runbook so recovery drill evidence is generated
  and archived before it is merged into trial evidence via
  `annotate-trial-ops-evidence`.

## Guardrails

- The failure input must be an `adp-scheduled-execution-v1` daily-run report
  with status `blocked`, `failed`, or `degraded`, exit code 2, blocking reasons,
  and `production_evidence_ready=false`.
- The failure notification must be a real sent SMTP delivery report with a
  `delivery_ref`; dry-run notifications block recovery evidence.
- The recovery input must be an `adp-scheduled-execution-v1` daily-run report
  with status `succeeded`, exit code 0, `production_evidence_ready=true`, a real
  sent SMTP delivery report, and daily run, Release, SMTP, and resource refs.
- Durable `failure_ref` and `recovery_ref` values are required before recovery
  evidence can be verified.
- If both reports include `daily_run_report.date`, the dates must match.
- The builder does not rerun the scheduler, send SMTP mail, upload Releases,
  fetch arXiv, generate media, mutate the trial ledger, or claim production
  acceptance.

## Result

`pass for recovery evidence contract`

This phase does not claim a real recovery drill has already run. Production
acceptance remains blocked until the provisioned runner provides live source,
real SMTP, real Release, resource, weekly/monthly replay, recovery drill, and
30 unique daily production evidence entries.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_recovery.py arxiv-daily-push/tests/test_trial_replay.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_cli.py -q`: 21 focused tests OK.

## Remaining Risk

- Real recovery drill evidence still requires a controlled production failure or
  degraded daily-run artifact, a recovered production-ready rerun artifact, and
  durable private refs for both.
- Real production acceptance remains blocked until default-branch scheduled
  execution, live arXiv ingest on the runner, real SMTP/private Release refs,
  resource telemetry, weekly/monthly replay evidence, recovery drill evidence,
  and 30 unique daily entries are archived.

## Rollback

Revert `trial_recovery.py`, `build-trial-recovery-evidence`, recovery schema,
tests, runbook/docs/governance updates, and restore version `0.11.14`.
