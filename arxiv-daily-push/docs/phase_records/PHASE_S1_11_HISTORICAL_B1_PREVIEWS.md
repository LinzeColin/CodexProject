# PHASE S1-11 Historical B1 Previews

## Scope

- Task: `S1-11-HISTORICAL_B1_PREVIEWS-001`
- Acceptance: `ADP-ACC-S1-11-HISTORICAL-B1-PREVIEWS`
- Version: `0.21.0`
- Board: `B1` arXiv only

## Result

S1-11 is complete for offline historical preview evidence. The new
`adp historical-b1-previews` command generated 30 independent B1/arXiv report
and email preview packages, with 30 unique source IDs, 30 unique content
hashes, 30 unique email IDs, 30 content ledger rows, and 150 written preview
artifacts in the command-level smoke run. The command accepts deterministic
synthetic inputs plus JSON array, JSONL, and object-wrapper historical input
files, and the validator blocks future-information leakage.

## Evidence Boundary

- This is not live delivery evidence.
- This does not enable a production scheduler.
- This does not send real SMTP mail.
- This does not upload a GitHub Release.
- This does not generate video.
- This does not claim `ARXIV_PRODUCTION_ACCEPTED`.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s111_focus_final PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage1_historical_previews.py arxiv-daily-push/tests/test_stage1_b1_report.py arxiv-daily-push/tests/test_stage1_queue.py arxiv-daily-push/tests/test_cli.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s111_version_final PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push version
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s111_alltests PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s111_semantic_final PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_s111_cli_final PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push historical-b1-previews --generated-at 2026-06-23T07:30:00+10:00 --artifact-dir /tmp/codex_adp_s111_preview_artifacts --write --json
```

## Observed Results

- Focused S1-11 historical/B1/queue/CLI tests: 21 tests OK.
- Version CLI: `0.21.0`.
- arxiv-daily-push unit tests: 225 tests OK.
- Semantic extractor: 46 active formulas and 331 active parameters checked with no errors.
- CLI artifact smoke: pass; 30 previews, 30 unique dates, 30 unique source IDs, 30 unique content hashes, 30 unique email IDs, 150 artifact files, manifest exists, future leakage count 0, and SMTP/Release/video/network/scheduler side effects false.

## Next Gate

Next planned task: `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`.

That gate must collect controlled live B1/arXiv email delivery evidence across
two real natural days on the target runner. It must still avoid enabling
production scheduling until the dedicated production acceptance gate passes.
