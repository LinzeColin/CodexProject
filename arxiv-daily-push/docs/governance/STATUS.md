# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.8`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +15`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +15`
- Current iteration: `ITER-20260621-019`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-SCHEDULER-PASS`
- Model count: `18`
- Formula count: `20`
- Parameter count: `96`
- Task count: `19`
- Unbound event count: `26`

## Latest Run

- Event: `EVENT-20260621-ADP-026`
- Task: `ADP-PHASE11-PRODUCTION-SCHEDULER-009`
- Summary: Added a fail-closed scheduled production workflow gate with Australia/Sydney health-check, daily-run, and watchdog slots.
- Model delta: `Added MOD-ADP-018 adp-production-scheduler-v1.`
- Parameter delta: `Added PARAM-ADP-092 through PARAM-ADP-096.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-scheduler --path . --generated-at 2026-06-21T05:00:00+10:00 --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_sync2 python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_scheduler_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_SCHEDULER.md', '.github/workflows/arxiv-daily-push-scheduled.yml', 'arxiv-daily-push/src/arxiv_daily_push/production_scheduler.py', 'arxiv-daily-push/tests/test_production_scheduler.py', 'arxiv-daily-push/schemas/production_scheduler.schema.json', 'https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows', 'https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax']`
- Result: `pass`
- Rollback: Revert scheduled production workflow, scheduler validator, schema, tests, and restore version 0.11.7.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
