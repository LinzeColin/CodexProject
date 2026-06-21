# PHASE_04

Project: `arxiv-daily-push`
Phase: `B`
Task: `ADP-PHASE4-RANKING-001`
Status: `PASS`
Version: `0.4.0`

## Scope

Implemented deterministic candidate ranking and queue audit for explicit local
candidate inputs.

## Implemented

- `src/arxiv_daily_push/ranking.py`
- `adp rank-candidates` for local JSON candidate ranking.
- Local queue fixture at `tests/fixtures/ranking_candidates.json`.
- Ranking tests for 100-point weight sum, golden score, missing P0 evidence,
  metadata conflict, recent duplicate blocking, selection payload, and CLI.
- Governance activation for `MOD-ADP-002`, `FORM-ADP-003`, and
  `PARAM-ADP-009` through `PARAM-ADP-016`.

## Non-Scope

- No live arXiv fetch.
- No automatic Claim Ledger extraction from paper text or PDF.
- No lesson generation.
- No TTS, video, runner automation, Release upload, or real SMTP sending.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase4_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 26 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase4_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 24 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase4_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase4_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase4_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

Phase 4 ranking acceptance is functionally satisfied locally. The next
implementation gate is Phase 5 Claim Ledger extraction and publication gate.
