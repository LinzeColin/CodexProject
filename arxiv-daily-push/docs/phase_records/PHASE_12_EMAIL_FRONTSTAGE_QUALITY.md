# Phase 12 Email Front-Stage Quality

Date: 2026-06-22
Task: `ADP-PHASE12-EMAIL-FRONTSTAGE-QUALITY-037`
Version: `0.13.1`

## Trigger

Controlled manual workflow run `27934320671` succeeded technically on GitHub
Actions after PR #50 merged, but exposed human front-stage quality defects:

- the Release page was still treated as visible delivery context even though it
  is machine evidence and artifact storage;
- the email foregrounded a short video instead of the Chinese brief;
- the MP4 transcript still showed `ROI score`, which is backend ranking data.

## Changes

- Email body now makes the Chinese text brief the reading entry point.
- Email body keeps only an optional video file link and removes the Release
  landing page from the human reading path.
- Email action guidance no longer tells the recipient to start with a
  12-second video.
- MP4 transcript no longer includes backend ROI score or the numeric ranking
  score.
- Release notes identify the Release as machine evidence and downloadable
  media artifacts, not the reading entry point.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_focus PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_video.py arxiv-daily-push/tests/test_cli.py -q`
  - 27 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_all PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
  - 182 tests OK.

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_semantic PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push`
  - 37 active formulas and 266 active parameters checked with no errors.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_root2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s tests/governance -p 'test_*.py' -q`
  - 126 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_gov PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref origin/main`
  - errors 0 warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_frontstage_iq PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_information_quality.py --all --fast --fail-on-error`
  - PASS, errors 0 warnings 0.
- `python3 -m json.tool governance/run_manifests/ADP-PHASE12-EMAIL-FRONTSTAGE-QUALITY-20260622.json`
  - PASS.
- `git diff --check`
  - PASS.
- `find arxiv-daily-push tests/governance \( -name __pycache__ -o -name '*.pyc' \) -print`
  - no output.

CI evidence must still pass on the PR before this can be merged and manually
retested.

## Safety

- No production schedule was enabled.
- No SMTP email was sent by this code change.
- No GitHub Release was created by this code change.
- No secrets were read or logged.
- Video remains a GitHub Release/download link only; it is not an email
  attachment.

## Rollback

Revert version `0.13.1` front-stage quality code, tests, phase record,
manifest, event, and governance records, then restore version `0.13.0`.
