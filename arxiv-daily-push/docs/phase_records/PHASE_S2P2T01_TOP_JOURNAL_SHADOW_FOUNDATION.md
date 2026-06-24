# PHASE S2PCT01 - Top Journal Shadow Foundation

Date: 2026-06-24
Task: S2PCT01
Legacy alias: S2P2T01
Status: in_progress
Acceptance claim: not claimed

## Scope

S2PCT01 adds the first V7.1 D2 top-journal/Nature shadow foundation using official public Nature metadata only. Legacy V6 task ID `S2P2T01` is retained only as an alias.

Implemented:
- Nature official RSS metadata adapter.
- Main-journal research article filter for `s41586-*` article URLs.
- Metadata-only SourceItem conversion with no PDF, full-text, media, paywall bypass, or bulk harvesting.
- ROI candidate conversion through the existing queue/ranking path.
- No-send shadow daily runner with separate local queue, ledger, daily report, dry-run package, and email preview artifacts.
- CLI commands for `fetch-top-journal-latest` and `stage2-top-journal-shadow-daily`.

## Explicit Non-Scope

- No `STAGE2_PRODUCTION_ACCEPTED`.
- No `INTEGRATED_PRODUCTION_ACCEPTED`.
- No formal production inclusion of Nature/top journals.
- No SMTP send.
- No Release upload.
- No GitHub cloud production schedule.
- No video requirement.
- No PDF/full-text/paywall access.

## Source Policy

The adapter uses:
- `https://www.nature.com/nature.rss`
- `https://www.nature.com/nature/research-articles`

Only article landing-page links and RSS metadata are stored. News/editorial Nature URLs such as `d41586-*` are filtered out of the research queue.

## Verification

Focused tests:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_pycache_s2p2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_top_journal_adapter.py arxiv-daily-push/tests/test_stage2_sources.py -q
```

Result:

```text
Ran 14 tests in 0.559s
OK
```

Live no-send canary:

```text
fetch-top-journal-latest --journal nature --max-records 3 --fetcher curl
stage2-top-journal-shadow-daily --state-dir /tmp/adp_s2p2_nature_live_20260624/state
```

Result:

```text
batch_status pass
new_item_count 3
first_source_id nature:s41586-026-10799-8
shadow_status pass
selected_source_id nature:s41586-026-10799-8
real_smtp_sent False
formal_production_inclusion False
queue_path_exists True
ledger_path_exists True
email_preview_exists True
```

## Gate Status

This is evidence progress only. V7/root contract, AGENTS, three baseline files, and CI contract hash gate must pass before any formal Stage 2 source inclusion or production acceptance claim.
