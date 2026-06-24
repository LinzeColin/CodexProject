# S2PCT03 The Lancet Metadata-Only Shadow Evidence

Task: `S2PCT03` / legacy `S2P2T03`
Acceptance: `ACC-S2PCT03-LANCET`
Phase: `S2PC`
Status: completed shadow evidence, no formal production inclusion

## Evidence

- Official public Lancet Online First RSS endpoint: `https://www.thelancet.com/rssfeed/lancet_online.xml`
- Official current issue RSS cross-check endpoint: `https://www.thelancet.com/rssfeed/lancet_current.xml`
- Article type gate admits medical research-grade metadata such as `Articles`, `Review`, `Seminar`, `Series`, `Clinical Rounds`, `Viewpoint`, and `Perspectives`.
- PubMed relation is metadata-only and DOI-query-ready; no PubMed scraping, PDF download, full-text download, bulk harvest, or paywall bypass is enabled.
- Focused tests cover Lancet URL selection, DOI identity, medical article-type classification, Correspondence/Comment filtering, duplicate source handling, no-send shadow queue/ledger/email preview, and CLI JSON output.
- Live canary on 2026-06-24 returned `journal=lancet`, `new_item_count=3`, and no-send shadow report `status=pass` with selected source `lancet:10.1016/s0140-6736(26)00918-9`.

## Boundaries

This task does not claim `D2_SOURCE_DOMAIN_ACCEPTED`, `STAGE2_PRODUCTION_ACCEPTED`, or `INTEGRATED_PRODUCTION_ACCEPTED`.

No SMTP send, Release upload, GitHub production schedule, video, PDF/full-text download, PubMed full-record harvesting, or paywall bypass is enabled.

## Rollback

Revert Lancet additions in `top_journal_adapter.py`, `stage2_sources.py`, `cli.py`, the Lancet fixture/tests, governance registry rows, this phase record, and the run manifest.
