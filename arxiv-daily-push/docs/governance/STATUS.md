# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.18`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +25`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +25`
- Current iteration: `ITER-20260621-029`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-START-WORKFLOW-PASS`
- Model count: `28`
- Formula count: `30`
- Parameter count: `148`
- Task count: `29`
- Unbound event count: `36`

## Latest Run

- Event: `EVENT-20260622-ADP-036`
- Task: `ADP-PHASE11-TRIAL-START-WORKFLOW-019`
- Summary: Added manual default-branch trial start workflow and validator that collect preflight, bootstrap, scheduler, source, SMTP, Release, and start-gate artifacts with explicit side-effect variable gates before the 30-day production trial can be started.
- Model delta: `Added MOD-ADP-028 adp-trial-start-workflow-v1.`
- Parameter delta: `Added PARAM-ADP-144 through PARAM-ADP-148.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start_workflow.py arxiv-daily-push/tests/test_trial_start.py arxiv-daily-push/tests/test_trial_bootstrap.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_cli.py -q', "find arxiv-daily-push/schemas -name '*.schema.json' -exec python3 -m json.tool {} \\; >/dev/null", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_dashboard python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_workflow_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'git diff --check', "find arxiv-daily-push -name '__pycache__' -o -name '*.pyc'", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_START_WORKFLOW.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_start_workflow.py', 'arxiv-daily-push/tests/test_trial_start_workflow.py', '.github/workflows/arxiv-daily-push-trial-start.yml']`
- Result: `pass`
- Rollback: Revert trial start workflow, validator, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.17.

## Current Blockers

Production acceptance still requires a passing default-branch trial start workflow run, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
