# PHASE S2PDT03 China Legal Metadata Relation Evidence

Date: 2026-06-24

## Scope

S2PDT03 / legacy S2P3T03 builds metadata-only China legal metadata relation shadow evidence after the completed S2PDT02 C1 department source map.

Covered relation surfaces:

- draft/formal legal status taxonomy
- amended/repealed legal status transitions
- implemented/interpreted legal relations
- reprint/original-source relation guard
- forced rescore and old-conclusion update evidence

## Acceptance

Acceptance target: ACC-S2PDT03-LEGAL.

The report passes only when required legal statuses and relation types are observed, dates are ISO `YYYY-MM-DD`, reprint relations identify reprint and original roles with `original_source_verified=true`, and status changes trigger old-conclusion update plus rescore evidence.

## Boundaries

This phase does not provide legal advice, does not grant D3 core source-domain acceptance, and does not include any source in production mail.

Forbidden and kept false:

- legal advice
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
- Manifest: `governance/run_manifests/ADP-S2PDT03-CHINA-LEGAL-METADATA-RELATION-EVIDENCE-20260624.json`

## Verification

Initial focused validation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pdt03_focus1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_sources.py -q`
- Result: 43 tests OK

Semantic validation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_s2pdt03_semantic2 PYTHONPATH=scripts:arxiv-daily-push/src python3 scripts/validate_semantic_extractors.py arxiv-daily-push`
- Result: 65 formulas / 432 parameters OK

Final governance validation is recorded in the run manifest after closeout.
