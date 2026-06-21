# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.9`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +16`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +16`
- Current iteration: `ITER-20260621-020`
- Current phase: `E`
- Current gate: `ADP-PHASE11-SCHEDULED-EXECUTION-PASS`
- Model count: `19`
- Formula count: `21`
- Parameter count: `101`
- Task count: `20`
- Unbound event count: `27`

## Latest Run

- Event: `EVENT-20260621-ADP-027`
- Task: `ADP-PHASE11-SCHEDULED-EXECUTION-010`
- Summary: Added a controlled scheduled execution driver and workflow evidence artifact for health-check, daily-run, and watchdog modes.
- Model delta: `Added MOD-ADP-019 adp-scheduled-execution-v1 and updated scheduler validation for execution artifact evidence.`
- Parameter delta: `Added PARAM-ADP-097 through PARAM-ADP-101.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_target3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push run-scheduled-production --mode health-check --generated-at 2026-06-21T04:45:00+10:00 --preflight-report /tmp/adp-scheduled-preflight-pass.json --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_sched_exec_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_SCHEDULED_EXECUTION_DRIVER.md', 'arxiv-daily-push/src/arxiv_daily_push/scheduled_execution.py', 'arxiv-daily-push/tests/test_scheduled_execution.py', 'arxiv-daily-push/schemas/scheduled_execution.schema.json', '.github/workflows/arxiv-daily-push-scheduled.yml']`
- Result: `pending_final_validation`
- Rollback: Revert scheduled execution driver, workflow execution artifact changes, schema, tests, and restore version 0.11.8.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
