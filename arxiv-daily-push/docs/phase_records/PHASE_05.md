# PHASE_05

Project: `arxiv-daily-push`
Phase: `C`
Task: `ADP-PHASE5-EVIDENCE-GATE-001`
Status: `PASS`
Version: `0.5.0`

## Scope

Implemented deterministic Claim Ledger construction and publication hard-block
gate for explicit local evidence claim inputs.

## Implemented

- `src/arxiv_daily_push/evidence_gate.py`
- `adp gate-publication` for local source/claim JSON gate checks.
- Local Claim Ledger fixture at `tests/fixtures/claim_ledger_input.json`.
- Evidence gate tests for supported P0 allowance, missing P0 locator,
  unsupported P0, arXiv peer-review claim evidence, metadata conflict, and CLI.
- Governance activation for `MOD-ADP-003`, `FORM-ADP-004`, and
  `PARAM-ADP-017` through `PARAM-ADP-018`.

## Non-Scope

- No PDF parsing.
- No automatic claim extraction from paper full text.
- No lesson generation.
- No TTS, video, runner automation, Release upload, or real SMTP sending.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 32 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 25 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase5_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

Phase 5 evidence gate acceptance is functionally satisfied locally. The next
implementation gate is Phase 6 evidence-linked Chinese lesson generation.
