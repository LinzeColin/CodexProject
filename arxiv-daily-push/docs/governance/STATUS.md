# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.11`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +18`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +18`
- Current iteration: `ITER-20260621-022`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-LEDGER-PASS`
- Model count: `21`
- Formula count: `23`
- Parameter count: `112`
- Task count: `22`
- Unbound event count: `29`

## Latest Run

- Event: `EVENT-20260621-ADP-029`
- Task: `ADP-PHASE11-TRIAL-LEDGER-012`
- Summary: Added an incremental trial evidence ledger updater that appends production-ready scheduled daily-run evidence without claiming 30-day acceptance early.
- Model delta: `Added MOD-ADP-021 adp-trial-ledger-v1 and updated scheduler validation for trial ledger artifact evidence.`
- Parameter delta: `Added PARAM-ADP-108 through PARAM-ADP-112.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_target4 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_ledger.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push update-trial-ledger --scheduled-execution /tmp/adp-scheduled-production-ready.json --generated-at 2026-07-01T06:00:00+10:00 --trial-id adp-trial-202607 --trial-ref release://adp/trial-ledger.json --text-degradation-verified --video-degradation-verified --scheduler-enabled --scheduler-ref github-actions://adp-scheduler --private-release-verified --release-ref github-release://LinzeColin/CodexProject/adp-trial --real-smtp-verified --email-ref smtp://adp/30-day-delivery-evidence --resource-pressure-ok --resource-ref resource-gate://adp/30-day --json', 'bash -n /tmp/build-scheduled-daily-input.sh', 'bash -n /tmp/update-trial-evidence-ledger.sh', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_root2 python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_gov2 python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_ledger_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check', "find arxiv-daily-push \\( -name '__pycache__' -o -name '*.pyc' \\) -print", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_LEDGER_UPDATE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_ledger.py', 'arxiv-daily-push/tests/test_trial_ledger.py', 'arxiv-daily-push/schemas/trial_ledger.schema.json', '.github/workflows/arxiv-daily-push-scheduled.yml']`
- Result: `pass`
- Rollback: Revert trial ledger updater, workflow ledger artifact changes, schema, tests, and restore version 0.11.10.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
