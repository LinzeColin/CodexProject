# PHASE_S2PCT06_AUTHORITATIVE_REPORTS_EVIDENCE

Task: `S2PCT06`
Phase: `S2PC`
Date: `2026-06-24`
Fact level: `EXTRACTED`

## Goal

Add authoritative research institution, laboratory, industry technical report,
and product technical note metadata-only shadow evidence after S2PCT05
engineering public-signal evidence is stable.

## Scope

- Requires a passing S2PCT05 engineering signal report.
- Requires all four report types:
  `research_institution_report`, `lab_technical_report`,
  `industry_technical_report`, and `product_technical_note`.
- Validates publisher type, publisher identity, interest relation, evidence
  level, version/source URL, engineering signal traceability, and canonical
  paper traceability.
- Persists an authoritative report source report and JSONL ledger rows in
  shadow mode.

## Non-Scope

This phase does not enable or claim `D2_SOURCE_DOMAIN_ACCEPTED`,
`STAGE2_PRODUCTION_ACCEPTED`, `INTEGRATED_PRODUCTION_ACCEPTED`, production mail
inclusion, SMTP send, Release upload, GitHub cloud production schedule, video,
PDF/full-text download, paid API use, paywall bypass, or marketing-only report
acceptance.

## Evidence

- `governance/run_manifests/ADP-S2PCT06-AUTHORITATIVE-REPORTS-EVIDENCE-20260624.json`
- `arxiv-daily-push/tests/fixtures/authoritative_technical_reports.json`
- `arxiv-daily-push/tests/test_stage2_sources.py`
- `arxiv-daily-push/src/arxiv_daily_push/stage2_sources.py`
- `arxiv-daily-push/src/arxiv_daily_push/cli.py`

## Validation

- Focused Stage 2 source tests: `27 OK`.
- Semantic extractor: `semantic_formulas_checked=61`,
  `semantic_parameters_checked=398`.

## Result

`S2PCT06` is complete as metadata-only no-send shadow evidence. The next S2PC
task is `S2PCT07` D2 source-domain qualification and cross-type calibration.

## Rollback

Revert the S2PCT06 additions in `stage2_sources.py`, CLI wiring, authoritative
technical report fixtures/tests, governance registry entries, this phase record,
the run manifest, event records, and rendered governance sync.
