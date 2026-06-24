# S2PCT02 Science Metadata-Only Shadow Evidence

Task: `S2PCT02` / legacy `S2P2T02`
Acceptance: `ACC-S2PCT02-SCIENCE`
Phase: `S2PC`
Status: completed shadow evidence, no formal production inclusion

## Evidence

- Official public Science RSS endpoint: `https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science`
- Article type gate admits only `Research Article`, `Report`, `Review`, and `Perspective`.
- SourceItems remain metadata-only with `pdf_download_enabled=false`, `full_text_download_enabled=false`, `bulk_harvest_enabled=false`, and `paywall_bypass_allowed=false`.
- Focused tests cover Science URL selection, DOI identity, article-type classification, non-target item filtering, duplicate source handling, no-send shadow queue/ledger/email preview, and CLI JSON output.
- Live canary on 2026-06-24 returned `journal=science`, `new_item_count=3`, and no-send shadow report `status=pass` with selected source `science:10.1126/science.ads7910`.

## Boundaries

This task does not claim `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, or `INTEGRATED_PRODUCTION_ACCEPTED`.

No SMTP send, Release upload, GitHub production schedule, video, PDF/full-text download, or paywall bypass is enabled.

## Rollback

Revert Science additions in `top_journal_adapter.py`, `stage2_sources.py`, `cli.py`, the Science fixture/tests, governance registry rows, this phase record, and the run manifest.
