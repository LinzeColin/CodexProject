# PHASE S2PDT02 China C1 Department Source Map Evidence

Date: 2026-06-24

## Scope

S2PDT02 / legacy S2P3T02 builds a metadata-only China C1 central department source map after the completed S2PDT01 C0 national authority source foundation.

Covered C1 sectors:

- macro_policy
- science_technology
- industry_policy
- finance
- market_regulation
- key_industry

## Acceptance

Acceptance target: ACC-S2PDT02-C1.

The report passes only when every department record has an official domain, source URL, accepted official identity state, aliases, industry routes, board routes, evidence refs, and metadata-only flags.

## Boundaries

This phase does not grant D3 core source-domain acceptance and does not include any source in production mail.

Forbidden and kept false:

- formal production inclusion
- Stage2 or integrated production acceptance
- SMTP transport
- Release upload
- GitHub cloud schedule
- production queue mutation
- schema migration
- bulk scraping
- PDF download
- full-text extraction
- paid API use
- paywall bypass
- V7.1 CURRENT switch
- V7.2 mail or public Schema pre-run

## Evidence

- Code: `arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py`
- CLI: `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- Tests: `arxiv-daily-push/tests/test_stage2_sources.py`
- Manifest: `governance/run_manifests/ADP-S2PDT02-CHINA-C1-DEPARTMENT-SOURCE-MAP-EVIDENCE-20260624.json`

## Verification

Initial focused validation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pdt02_focus1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q`
- Result: 39 tests OK

Final semantic and governance validation are recorded in the run manifest after closeout.
