# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `arxiv-daily-push`
- Path: `arxiv-daily-push`
- CI mode: `required`
- Product version: `0.11.5`
- Model versions: `MOD-ADP-001:adp-foundation-v1, MOD-ADP-002:adp-ranking-v1, MOD-ADP-003:adp-claim-gate-v1, +12`
- Parameter profile versions: `adp-acceptance-parameters:adp-acceptance-parameters-v1.2, adp-arxiv-adapter-parameters:adp-arxiv-adapter-parameters-v1, adp-contract-parameters:adp-contract-parameters-v1, +12`
- Current iteration: `ITER-20260621-016`
- Current phase: `E`
- Current gate: `ADP-PHASE11-LIVE-ARXIV-INGEST-PASS`
- Model count: `15`
- Formula count: `17`
- Parameter count: `80`
- Task count: `16`
- Unbound event count: `23`

## Latest Run

- Event: `EVENT-20260621-ADP-023`
- Task: `ADP-PHASE11-LIVE-ARXIV-INGEST-006`
- Summary: Added a small-window live arXiv latest source ingest command with SourceBatch output, SourceItem validation, and duplicate source filtering.
- Model delta: `Added MOD-ADP-015 adp-live-arxiv-ingest-v1.`
- Parameter delta: `Added PARAM-ADP-075 through PARAM-ADP-080.`
- Tests: `['PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q', 'for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done', "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_live PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query 'cat:cs.AI' --max-results 1 --generated-at 2026-06-22T00:55:00+10:00 --json", "PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q", 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push', 'PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync', 'PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_dashboard python3 scripts/generate_governance_dashboard.py --write', 'git diff --check']`
- Evidence: `['arxiv-daily-push/docs/phase_records/PHASE_11_LIVE_ARXIV_INGEST.md', 'arxiv-daily-push/src/arxiv_daily_push/source_ingest.py', 'arxiv-daily-push/tests/test_source_ingest.py', 'arxiv-daily-push/schemas/source_batch.schema.json', 'https://info.arxiv.org/help/api/user-manual.html']`
- Result: `pass`
- Rollback: Revert live arXiv ingest command, SourceBatch schema, tests, and restore version 0.11.4.

## Current Blockers

Production acceptance still requires real 30-day trial, scheduler, Release, SMTP, and resource evidence; those are not claimed by this handoff.

## Next Task

`UNKNOWN`
