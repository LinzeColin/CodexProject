# PHASE_11_LIVE_ARXIV_INGEST

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-LIVE-ARXIV-INGEST-006`
Status: `PASS_FOR_CODE_GATE_BLOCKED_FOR_LOCAL_LIVE_FETCH`
Version: `0.11.5`

## Scope

Added a live arXiv latest-source ingest command for the first production source
object.

The source ingest gate includes:

- `adp fetch-arxiv-latest`;
- small-window arXiv Atom query fetch using the existing `arxiv.atom.v1`
  adapter;
- `SourceBatch` JSON output;
- generic `SourceItem` validation;
- incremental duplicate filtering by `source_id`;
- no PDF download;
- no bulk harvest;
- fail-closed network, TLS, API, Atom parsing, SourceItem validation, and
  duplicate-only behavior.

The implementation follows the official arXiv API query and Atom response model
documented at `https://info.arxiv.org/help/api/user-manual.html`.

## Non-Scope

- No scheduled runner execution.
- No PDF or full-text download.
- No bulk metadata harvest.
- No ranking automation.
- No lesson, narration, video, Release, or SMTP side effect.
- No TLS bypass.

## Current Environment Status

`blocked_for_live_fetch`

The local command failed closed because Python HTTPS certificate verification
failed for `https://export.arxiv.org/api/query`. This is an environment
readiness blocker; the implementation must not bypass TLS verification.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 78 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_live PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query 'cat:cs.AI' --max-results 1 --generated-at 2026-06-22T00:55:00+10:00 --json`: exit 2; blocked on Python SSL certificate verification.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 36 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_ingest_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

The repository now has a real source-ingest CLI boundary for arXiv latest Atom
metadata and duplicate filtering. The current local environment still cannot
produce live source evidence until Python CA trust is repaired.
