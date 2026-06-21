# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.12`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +19`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +19`
- Current iteration: `ITER-20260621-023`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-LEDGER-STATE-PASS`
- Model count: `22`
- Formula count: `24`
- Parameter count: `117`
- Task count: `23`
- Unbound event count: `30`

## Latest Run

- Event: `EVENT-20260622-ADP-030`
- Task: `ADP-PHASE11-TRIAL-LEDGER-STATE-013`
- Summary: Added cross-run trial evidence ledger state persistence through GitHub Actions artifact restore/export without storing state in Git or local cache.
- Model delta: `Added MOD-ADP-022 adp-trial-ledger-state-v1 and updated scheduler validation for trial ledger state artifact evidence.`
- Parameter delta: `Added PARAM-ADP-113 through PARAM-ADP-117.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ledger.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', 'bash -n /tmp/build-scheduled-daily-input.sh', 'bash -n /tmp/resolve-trial-ledger-state.sh', 'bash -n /tmp/update-trial-evidence-ledger.sh', 'bash -n /tmp/export-trial-evidence-ledger-state.sh', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ledger-state --ledger-update /tmp/adp-ledger-update-pass.json --json', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_state_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check', "find arxiv-daily-push \\( -name '__pycache__' -o -name '*.pyc' \\) -print", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_LEDGER_STATE.md', 'arxiv-daily-push/src/arxiv_daily_push/cli.py', 'arxiv-daily-push/tests/test_trial_ledger.py', 'arxiv-daily-push/tests/test_production_scheduler.py', '.github/workflows/arxiv-daily-push-scheduled.yml']`
- Result: `pass`
- Rollback: Revert trial ledger state restore/export workflow changes, export command, tests, and restore version 0.11.11.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
