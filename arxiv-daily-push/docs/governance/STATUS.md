# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.4`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +11`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +11`
- Current iteration: `ITER-20260621-015`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-BOOTSTRAP-PASS`
- Model count: `14`
- Formula count: `16`
- Parameter count: `74`
- Task count: `15`
- Unbound event count: `22`

## Latest Run

- Event: `EVENT-20260621-ADP-022`
- Task: `ADP-PHASE11-TRIAL-BOOTSTRAP-005`
- Summary: Added a manual GitHub Actions production trial bootstrap workflow, runbook, and CLI validator while keeping cron, Release upload, and SMTP sending disabled.
- Model delta: `Added MOD-ADP-014 adp-trial-bootstrap-v1.`
- Parameter delta: `Added PARAM-ADP-071 through PARAM-ADP-074.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-bootstrap --path . --generated-at 2026-06-22T00:30:00+10:00 --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_bootstrap_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_BOOTSTRAP_WORKFLOW.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_bootstrap.py', 'arxiv-daily-push/tests/test_trial_bootstrap.py', '.github/workflows/arxiv-daily-push-production-trial.yml', 'arxiv-daily-push/docs/runbooks/PRODUCTION_TRIAL_RUNBOOK.md']`
- Result: `pass`
- Rollback: Revert Phase 11 trial bootstrap workflow, runbook, validator, tests, and restore version 0.11.3.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
