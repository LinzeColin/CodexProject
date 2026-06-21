# PHASE_08

Project: `arxiv-daily-push`
Phase: `D`
Task: `ADP-PHASE8-VIDEO-001`
Status: `PASS`
Version: `0.8.0`

## Scope

Implemented deterministic Storyboard JSON generation from Narration objects and
video media gate reporting in dry-run mode.

## Implemented

- `src/arxiv_daily_push/video.py`
- `adp generate-storyboard` for local narration JSON storyboard dry runs.
- Local video fixture at `tests/fixtures/video_input.json`.
- Tests for storyboard dry-run output, render/write/download blocking, media path
  rejection, scene claim subset validation, and CLI output.
- Governance activation for `MOD-ADP-008`, `FORM-ADP-010`, and
  `PARAM-ADP-041` through `PARAM-ADP-044`.

## Non-Scope

- No real video rendering.
- No media file write.
- No asset download.
- No scheduled runner, Release upload, or real SMTP sending.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 47 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- - `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 28 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_phase8_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

Phase 8 storyboard/video dry-run acceptance is functionally satisfied locally.
The next implementation gate is Phase 9 local daily pipeline dry-run.
