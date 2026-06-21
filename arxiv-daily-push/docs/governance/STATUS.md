# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.14`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +21`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +21`
- Current iteration: `ITER-20260621-025`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-PASS`
- Model count: `24`
- Formula count: `26`
- Parameter count: `127`
- Task count: `25`
- Unbound event count: `32`

## Latest Run

- Event: `EVENT-20260622-ADP-032`
- Task: `ADP-PHASE11-TRIAL-REPLAY-EVIDENCE-015`
- Summary: Added fail-closed weekly/monthly trial replay evidence builder and CLI command so replay evidence can be generated from production-ready daily trial entries before ops annotation.
- Model delta: `Added MOD-ADP-024 adp-trial-replay-v1.`
- Parameter delta: `Added PARAM-ADP-123 through PARAM-ADP-127.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_target3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_replay.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_trial.py arxiv-daily-push/tests/test_cli.py -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool \\"$f\\" >/dev/null || exit 1', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_sync2 python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_replay_dashboard2 python3 scripts/generate_governance_dashboard.py --write', 'git diff --check', "find arxiv-daily-push \\( -name '__pycache__' -o -name '*.pyc' \\) -print", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_REPLAY_EVIDENCE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_replay.py', 'arxiv-daily-push/src/arxiv_daily_push/cli.py', 'arxiv-daily-push/tests/test_trial_replay.py']`
- Result: `pass`
- Rollback: Revert trial replay builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.13.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
