# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.17`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +24`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +24`
- Current iteration: `ITER-20260621-028`
- Current phase: `E`
- Current gate: `ADP-PHASE11-TRIAL-START-GATE-PASS`
- Model count: `27`
- Formula count: `29`
- Parameter count: `143`
- Task count: `28`
- Unbound event count: `35`

## Latest Run

- Event: `EVENT-20260622-ADP-035`
- Task: `ADP-PHASE11-TRIAL-START-GATE-018`
- Summary: Added fail-closed trial start readiness gate that aggregates production preflight, bootstrap, scheduler, live source, real SMTP, real Release, durable refs, and explicit confirmation before marking the 30-day trial start-ready.
- Model delta: `Added MOD-ADP-027 adp-trial-start-v1.`
- Parameter delta: `Added PARAM-ADP-138 through PARAM-ADP-143.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_trial_start.py arxiv-daily-push/tests/test_trial_bootstrap.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_production_preflight.py arxiv-daily-push/tests/test_source_ingest.py arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_release_delivery.py arxiv-daily-push/tests/test_cli.py -q', "find arxiv-daily-push/schemas -name '*.schema.json' -exec python3 -m json.tool {} \\; >/dev/null", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_dashboard python3 scripts/generate_governance_dashboard.py --write', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_trial_start_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'git diff --check', "find arxiv-daily-push -name '__pycache__' -o -name '*.pyc'", 'du -sh arxiv-daily-push .git']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_TRIAL_START_GATE.md', 'arxiv-daily-push/src/arxiv_daily_push/trial_start.py', 'arxiv-daily-push/tests/test_trial_start.py']`
- Result: `pass`
- Rollback: Revert trial start gate, CLI command, schema, tests, runbook/docs/governance updates, and restore version 0.11.16.

## Current Blockers

Production acceptance still requires default-branch trial start evidence, live source ingest pass on the runner, real SMTP and Release refs, resource telemetry, weekly/monthly replay, recovery drill, and 30 unique daily production evidence entries; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
