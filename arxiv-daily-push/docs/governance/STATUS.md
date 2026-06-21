# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.15`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +22`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +22`
- Current iteration: `ITER-20260621-026`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-PASS`
- Model count: `25`
- Formula count: `27`
- Parameter count: `132`
- Task count: `26`
- Unbound event count: `33`

## Latest Run

- Event: `EVENT-20260622-ADP-033`
- Task: `ADP-PHASE11-TRIAL-RECOVERY-EVIDENCE-016`
- Summary: Added fail-closed trial recovery evidence builder and CLI command so recovery drill evidence can be generated from failed and recovered scheduled daily-run reports before ops annotation.
- Model delta: `Added MOD-ADP-025 adp-trial-recovery-v1.`
- Parameter delta: `Added PARAM-ADP-128 through PARAM-ADP-132.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_recovery.py arxiv-daily-push/tests/test_trial_replay.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_cli.py -q', "find arxiv-daily-push/schemas -name '*.schema.json' -exec python3 -m json.tool {} \\;", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_dashboard python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_recovery_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'git diff --check', "find arxiv-daily-push -name '__pycache__' -o -name '*.pyc'", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_RECOVERY_EVIDENCE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_recovery.py', 'arxiv-daily-push/src/arxiv_daily_push/cli.py', 'arxiv-daily-push/tests/test_trial_recovery.py']`
- Result: `pass`
- Rollback: Revert trial recovery builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.14.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
