# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.13`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +20`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +20`
- Current iteration: `ITER-20260621-024`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-OPS-EVIDENCE-PASS`
- Model count: `23`
- Formula count: `25`
- Parameter count: `122`
- Task count: `24`
- Unbound event count: `31`

## Latest Run

- Event: `EVENT-20260622-ADP-031`
- Task: `ADP-PHASE11-TRIAL-OPS-EVIDENCE-014`
- Summary: Added fail-closed operational trial evidence annotation for weekly/monthly replay, recovery drill, and other explicit refs without hand-editing trial evidence JSON.
- Model delta: `Added MOD-ADP-023 adp-trial-ops-evidence-v1.`
- Parameter delta: `Added PARAM-ADP-118 through PARAM-ADP-122.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_target4 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_trial.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_project2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_cli2 PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push annotate-trial-ops-evidence --path /tmp/adp-trial-evidence-without-ops.json --generated-at 2026-07-31T06:30:00+10:00 --weekly-replay-verified --monthly-replay-verified --weekly-monthly-ref github-release://adp/weekly-monthly-replay --recovery-drill-verified --recovery-ref github-actions://adp/recovery-drill --json', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_export2 PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ops-state --ops-update /tmp/adp-trial-ops-update.json --json', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ops_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check', "find arxiv-daily-push \\( -name '__pycache__' -o -name '*.pyc' \\) -print", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_OPS_EVIDENCE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_ops.py', 'arxiv-daily-push/src/arxiv_daily_push/cli.py', 'arxiv-daily-push/tests/test_trial_ops.py']`
- Result: `pass`
- Rollback: Revert trial ops annotator, CLI commands, tests, runbook/docs/governance updates, and restore version 0.11.12.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
