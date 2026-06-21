# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.6`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +13`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +13`
- Current iteration: `ITER-20260621-017`
- Current phase: `E`
- Current gate: `ADP-PHASE11-SMTP-DELIVERY-PASS`
- Model count: `16`
- Formula count: `18`
- Parameter count: `85`
- Task count: `17`
- Unbound event count: `24`

## Latest Run

- Event: `EVENT-20260621-ADP-024`
- Task: `ADP-PHASE11-SMTP-DELIVERY-007`
- Summary: Added a fail-closed SMTP notification delivery boundary with dry-run evidence and explicit real-send gating.
- Model delta: `Added MOD-ADP-016 adp-smtp-delivery-v1.`
- Parameter delta: `Added PARAM-ADP-081 through PARAM-ADP-085.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_target PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_cli.py -q', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification --run-id run-001 --summary 'Daily status' --date 2026-06-21 --generated-at 2026-06-21T05:00:00+10:00 --json", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_smtp_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_SMTP_DELIVERY.md', 'arxiv-daily-push/src/arxiv_daily_push/smtp_delivery.py', 'arxiv-daily-push/tests/test_notifications.py', 'arxiv-daily-push/tests/test_cli.py', 'arxiv-daily-push/schemas/smtp_delivery.schema.json']`
- Result: `pass`
- Rollback: Revert SMTP delivery command, schema, tests, and restore version 0.11.5.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
