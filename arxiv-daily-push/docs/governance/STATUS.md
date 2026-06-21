# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.7`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +14`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +14`
- Current iteration: `ITER-20260621-018`
- Current phase: `E`
- Current gate: `ADP-PHASE11-RELEASE-DELIVERY-PASS`
- Model count: `17`
- Formula count: `19`
- Parameter count: `91`
- Task count: `18`
- Unbound event count: `25`

## Latest Run

- Event: `EVENT-20260621-ADP-025`
- Task: `ADP-PHASE11-RELEASE-DELIVERY-008`
- Summary: Added a fail-closed GitHub Release delivery boundary with dry-run evidence and explicit real-upload gating.
- Model delta: `Added MOD-ADP-017 adp-release-delivery-v1.`
- Parameter delta: `Added PARAM-ADP-086 through PARAM-ADP-091.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_release_delivery.py arxiv-daily-push/tests/test_cli.py -q', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release --tag adp-release-probe-20260621 --title 'arXiv Daily Push release probe' --notes 'Release delivery boundary probe' --asset governance/run_manifests/ADP-PHASE11-RELEASE-DELIVERY-20260621.json --generated-at 2026-06-21T05:00:00+10:00 --json", "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_root2 python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_gov2 python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_sync3 python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_release_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_RELEASE_DELIVERY.md', 'arxiv-daily-push/src/arxiv_daily_push/release_delivery.py', 'arxiv-daily-push/tests/test_release_delivery.py', 'arxiv-daily-push/tests/test_cli.py', 'arxiv-daily-push/schemas/release_delivery.schema.json']`
- Result: `pass`
- Rollback: Revert Release delivery command, schema, tests, and restore version 0.11.6.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
