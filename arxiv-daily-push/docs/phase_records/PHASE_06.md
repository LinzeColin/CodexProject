# PHASE_06

Project: `arxiv-daily-push`
Phase: `C`
Task: `ADP-PHASE6-LESSON-001`
Status: `PASS`
Version: `0.6.0`

## Scope

Implemented deterministic Chinese text Lesson JSON generation from supported
Claim Ledger evidence.

## Implemented

- `src/arxiv_daily_push/lesson.py`
- `adp generate-lesson` for local source/claim JSON lesson generation.
- Local lesson fixture at `tests/fixtures/lesson_input.json`.
- Lesson tests for supported claim linkage, unverified claim exclusion, blocked
  ledger behavior, unregistered claim rejection, visible claim markers, and CLI.
- Governance activation for `MOD-ADP-006`, `FORM-ADP-008`, and
  `PARAM-ADP-035` through `PARAM-ADP-036`.

## Non-Scope

- No narration generation.
- No TTS model download or voice synthesis.
- No video rendering.
- No scheduled runner, Release upload, or real SMTP sending.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 37 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 26 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase6_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

Phase 6 lesson acceptance is functionally satisfied locally. The next
implementation gate is Phase 7 narration/TTS dry-run and resource validation.
