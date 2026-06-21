# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.10`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +17`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +17`
- Current iteration: `ITER-20260621-021`
- Current phase: `E`
- Current gate: `ADP-PHASE11-DAILY-INPUT-BUILDER-PASS`
- Model count: `20`
- Formula count: `22`
- Parameter count: `107`
- Task count: `21`
- Unbound event count: `28`

## Latest Run

- Event: `EVENT-20260621-ADP-028`
- Task: `ADP-PHASE11-DAILY-INPUT-BUILDER-011`
- Summary: Added a daily input builder that converts live arXiv SourceBatch output into ranked scheduled daily pipeline input using only Atom summary claims.
- Model delta: `Added MOD-ADP-020 adp-daily-input-builder-v1 and updated scheduler validation for daily input artifact evidence.`
- Parameter delta: `Added PARAM-ADP-102 through PARAM-ADP-107.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_daily_input.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-daily-input --source-batch /tmp/adp-source-batch-fixture.json --date 2026-06-21 --generated-at 2026-06-21T05:00:00+10:00 --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_daily_input_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_DAILY_INPUT_BUILDER.md', 'arxiv-daily-push/src/arxiv_daily_push/daily_input.py', 'arxiv-daily-push/tests/test_daily_input.py', 'arxiv-daily-push/schemas/daily_input.schema.json', '.github/workflows/arxiv-daily-push-scheduled.yml', 'https://info.arxiv.org/help/api/user-manual.html']`
- Result: `pending_final_validation`
- Rollback: Revert daily input builder, workflow source/daily-input artifact changes, schema, tests, and restore version 0.11.9.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
