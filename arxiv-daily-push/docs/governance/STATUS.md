# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.3`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +10`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +10`
- Current iteration: `ITER-20260621-014`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-PREFLIGHT-PASS`
- Model count: `13`
- Formula count: `15`
- Parameter count: `70`
- Task count: `14`
- Unbound event count: `21`

## Latest Run

- Event: `EVENT-20260621-ADP-021`
- Task: `ADP-PHASE11-PRODUCTION-PREFLIGHT-004`
- Summary: Added a fail-closed production preflight gate before scheduled execution.
- Model delta: `Added MOD-ADP-013 adp-production-preflight-v1.`
- Parameter delta: `Added PARAM-ADP-065 through PARAM-ADP-070.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push preflight-production --path . --generated-at 2026-06-21T23:58:00+10:00 --json', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_PREFLIGHT.md', 'arxiv-daily-push/src/arxiv_daily_push/production_preflight.py', 'arxiv-daily-push/tests/test_production_preflight.py']`
- Result: `pass`
- Rollback: Revert Phase 11 production preflight gate and restore version 0.11.2.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
