# PHASE_11_PRODUCTION_PREFLIGHT

Project: `arxiv-daily-push`
Phase: `E`
Task: `ADP-PHASE11-PRODUCTION-PREFLIGHT-004`
Status: `PASS_FOR_PREFLIGHT_GATE`
Version: `0.11.3`

## Scope

Added a fail-closed production preflight gate for scheduled arXiv Daily Push
execution.

The gate checks:

- production runtime commands: `python3`, `git`, `node`, `npm`, `gh`, `ffmpeg`,
  `docker`, and `codex`;
- required secret environment key presence without logging values;
- free disk against the 80 GiB media/TTS threshold;
- total memory against the 8 GiB minimum;
- Git tracked/untracked artifact hygiene for media, model weights, credential
  suffixes, and large files;
- local cache, staging, render, media, model, voice sample, and release asset
  directories.

## Non-Scope

- No secret values are read or printed.
- No `~/.codex/auth.json` access.
- No scheduler enablement.
- No Release upload.
- No SMTP send.
- No media rendering, model download, or retained cache artifact generation.

## Current Environment Status

`blocked`

This is expected until production prerequisites are provisioned. The current
local gate can produce the blocking evidence, but it does not claim production
readiness.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_project PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`: 71 tests OK.
- `for f in arxiv-daily-push/schemas/*.schema.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`: all schema JSON files parse.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_root python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`: 34 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_gov python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_sync python3 scripts/validate_project_governance.py --changed-only --enforce-sync`: errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_cli PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push preflight-production --path . --generated-at 2026-06-21T23:58:00+10:00 --json`: exit 2 as expected; blocked on missing `gh`, `ffmpeg`, `docker`, missing SMTP/Release/runner env keys, and 25.36 GiB free disk below 80 GiB.
- `PYTHONPYCACHEPREFIX=/tmp/codex_adp_pycache_preflight_dashboard python3 scripts/generate_governance_dashboard.py --write`: PASS.
- `git diff --check`: exit 0.

## Result

The system now has a pre-scheduler production gate. It still requires external
runner, SMTP, Release, and resource prerequisites before a real production run
can start.
