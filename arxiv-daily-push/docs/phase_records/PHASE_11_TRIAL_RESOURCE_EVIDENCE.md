# Phase 11 Trial Resource Evidence

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017`
Acceptance: `ADP-ACC-PHASE11-TRIAL-RESOURCE-EVIDENCE`
Status: `PASS_FOR_RESOURCE_EVIDENCE_CONTRACT`
Version: `0.11.16`

## Scope

Add a fail-closed resource telemetry evidence generator for 30-day trial daily
resource refs and archived production preflight reports.

## Implemented

- Added `src/arxiv_daily_push/trial_resource.py`.
- Added `adp build-trial-resource-evidence`.
- Added `schemas/trial_resource.schema.json`.
- Changed passing production preflight reports to emit timestamped
  `production-preflight://arxiv-daily-push/<generated-at>` refs instead of the
  previous static `current` ref.
- Added tests for resource pass, missing matching preflight blocking, blocked
  preflight blocking, missing durable ref blocking, lowered expected-day
  blocking, and CLI JSON output.
- Updated the production trial runbook so resource evidence is generated and
  archived before it is merged into trial evidence via
  `annotate-trial-ops-evidence`.

## Guardrails

- Resource evidence requires at least 30 unique daily `resource_gate_ref` values.
- Every daily resource ref must match a passing production preflight report.
- Each preflight report must pass validation and include passing disk, memory,
  Git artifact hygiene, local cache, and secret-environment gates.
- A durable `resource_ref` is required before resource evidence can be verified.
- The builder does not run preflight, mutate the trial ledger, send SMTP mail,
  upload Releases, generate media, or claim production acceptance.

## Result

`pass for resource evidence contract`

This phase does not claim real 30-day resource telemetry has already been
archived. Production acceptance remains blocked until the provisioned runner
provides live source, real SMTP, real Release, resource telemetry,
weekly/monthly replay, recovery drill, and 30 unique daily production evidence
entries.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_resource.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_cli.py -q`: 27 focused tests OK.

## Remaining Risk

- Real resource telemetry evidence still requires 30 production preflight
  reports archived from default-branch scheduled runs and a durable private ref.
- Real production acceptance remains blocked until default-branch scheduled
  execution, live arXiv ingest on the runner, real SMTP/private Release refs,
  weekly/monthly replay evidence, recovery drill evidence, resource telemetry,
  and 30 unique daily entries are archived.

## Rollback

Revert `trial_resource.py`, `build-trial-resource-evidence`, timestamped
preflight resource refs, resource schema, tests, runbook/docs/governance updates,
and restore version `0.11.15`.
