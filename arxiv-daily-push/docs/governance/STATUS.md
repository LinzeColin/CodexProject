# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.0`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +8`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +8`
- Current iteration: `ITER-20260621-011`
- Current phase: `E`
- Current gate: `ADP-PHASE11-ACCEPTANCE-HANDOFF-PASS`
- Model count: `11`
- Formula count: `13`
- Parameter count: `55`
- Task count: `11`
- Unbound event count: `18`

## Latest Run

- Event: `EVENT-20260621-ADP-018`
- Task: `ADP-PHASE11-ACCEPTANCE-HANDOFF-001`
- Summary: Implemented Phase 11 final acceptance and handoff readiness package while blocking unsupported production and 30-day trial claims.
- Model delta: `Activated MOD-ADP-011 deterministic final acceptance and handoff readiness gate.`
- Parameter delta: `Activated PARAM-ADP-051 through PARAM-ADP-055 as acceptance parameters.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase11_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase11_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase11_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase11_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase11_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11.md', 'arxiv-daily-push/src/arxiv_daily_push/acceptance.py', 'arxiv-daily-push/tests/test_acceptance.py', 'arxiv-daily-push/tests/fixtures/pipeline_input.json']`
- Result: `pass`
- Rollback: Revert Phase 11 acceptance code, tests, and governance updates.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
