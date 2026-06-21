# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.16`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +23`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +23`
- Current iteration: `ITER-20260621-027`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-PASS`
- Model count: `26`
- Formula count: `28`
- Parameter count: `137`
- Task count: `27`
- Unbound event count: `34`

## Latest Run

- Event: `EVENT-20260622-ADP-034`
- Task: `ADP-PHASE11-TRIAL-RESOURCE-EVIDENCE-017`
- Summary: Added fail-closed trial resource telemetry evidence builder and timestamped production preflight resource refs so 30-day resource evidence can be matched before ops annotation.
- Model delta: `Added MOD-ADP-026 adp-trial-resource-v1.`
- Parameter delta: `Added PARAM-ADP-133 through PARAM-ADP-137.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_target2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_resource.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_trial_ops.py arxiv-daily-push/tests/test_cli.py -q', "find arxiv-daily-push/schemas -name '*.schema.json' -exec python3 -m json.tool {} \\; >/dev/null", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_dashboard python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_resource_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'git diff --check', "find arxiv-daily-push -name '__pycache__' -o -name '*.pyc'", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_RESOURCE_EVIDENCE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_resource.py', 'arxiv-daily-push/src/arxiv_daily_push/production_preflight.py', 'arxiv-daily-push/tests/test_trial_resource.py']`
- Result: `pass`
- Rollback: Revert trial resource builder, timestamped preflight resource ref change, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.15.

## Current Blockers

Production acceptance still requires default-branch scheduled execution, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
