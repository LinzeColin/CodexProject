# PHASE_07

Project: `arxiv-daily-push`
Phase: `D`
Task: `ADP-PHASE7-TTS-001`
Status: `PASS`
Version: `0.7.0`

## Scope

Implemented deterministic narration/TTS-ready dry-run JSON generation from
Lesson objects and local TTS resource gate reporting.

## Implemented

- `src/arxiv_daily_push/narration.py`
- `adp generate-narration` for local Lesson JSON narration dry runs.
- `schemas/narration.schema.json`.
- Local narration fixture at `tests/fixtures/narration_input.json`.
- Tests for dry-run boundary, real TTS blocking, audio path rejection, runtime
  parameters, and CLI output.
- Governance activation for `MOD-ADP-007`, `FORM-ADP-009`, and
  `PARAM-ADP-037` through `PARAM-ADP-040`.

## Non-Scope

- No audio synthesis.
- No model download.
- No audio file write or retained media artifact.
- No video rendering.
- No scheduled runner, Release upload, or real SMTP sending.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 42 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- - `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 27 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase7_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

Phase 7 narration/TTS dry-run acceptance is functionally satisfied locally. The
next implementation gate is Phase 8 video/storyboard dry-run and media QA.
