# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.19`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +26`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +26`
- Current iteration: `ITER-20260621-030`
- Current phase: `E`
- Current gate: `ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-PASS`
- Model count: `29`
- Formula count: `31`
- Parameter count: `153`
- Task count: `30`
- Unbound event count: `37`

## Latest Run

- Event: `EVENT-20260622-ADP-037`
- Task: `ADP-PHASE11-PRODUCTION-LAUNCH-READINESS-020`
- Summary: Added fail-closed production launch readiness gate before default-branch trial start workflow dispatch; blocks draft/unmerged PR, head SHA mismatch, missing launch confirmation, non-durable evidence refs, missing SMTP secret refs, runner refs, Release refs, workflow variable refs, and trial-start workflow refs.
- Model delta: `Added MOD-ADP-029 adp-production-launch-readiness-v1.`
- Parameter delta: `Added PARAM-ADP-149 through PARAM-ADP-153.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_production_launch.py arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_cli.py -q', "find arxiv-daily-push/schemas -name '*.schema.json' -exec python3 -m json.tool {} \\; >/dev/null", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_dashboard python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_production_launch_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'git diff --check', "find arxiv-daily-push -name '__pycache__' -o -name '*.pyc'", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_PRODUCTION_LAUNCH_READINESS.md', 'arxiv-daily-push/src/arxiv_daily_push/production_launch.py', 'arxiv-daily-push/tests/test_production_launch.py']`
- Result: `pass`
- Rollback: Revert production launch readiness builder, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.18.

## Current Blockers

Production launch remains blocked while PR #14 is draft and unmerged; production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
