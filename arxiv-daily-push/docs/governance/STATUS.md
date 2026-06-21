# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.2`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +9`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +9`
- Current iteration: `ITER-20260621-013`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-PASS`
- Model count: `12`
- Formula count: `14`
- Parameter count: `64`
- Task count: `13`
- Unbound event count: `20`

## Latest Run

- Event: `EVENT-20260621-ADP-020`
- Task: `ADP-PHASE11-TRIAL-EVIDENCE-VALIDATOR-003`
- Summary: Added a 30-day operational trial evidence validator and required validated trial reports for production acceptance.
- Model delta: `Added MOD-ADP-012 adp-trial-evidence-v1 and updated MOD-ADP-011 to adp-acceptance-v1.2.`
- Parameter delta: `Added PARAM-ADP-057 through PARAM-ADP-064.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_EVIDENCE_VALIDATOR.md', 'arxiv-daily-push/src/arxiv_daily_push/trial.py', 'arxiv-daily-push/tests/test_trial.py', 'arxiv-daily-push/tests/test_acceptance.py']`
- Result: `pass`
- Rollback: Revert Phase 11 trial evidence validator and restore version 0.11.1.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
