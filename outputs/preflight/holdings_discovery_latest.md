# Holdings Discovery

- Generated at: 2026-06-13T05:08:50+08:00
- Production-ready candidate found: False
- Converted candidate CSV: outputs/preflight/alipay_positions_candidate_from_quantlab.csv
- Review matrix CSV: outputs/preflight/alipay_holdings_review_matrix.csv
- Path display: workspace-relative for project files; external local paths are filename-only for privacy.

## Files

- **csv_candidate** rows=0 eligible=False: `app/templates/alipay_positions_template.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=4 eligible=False: `data/imports/alipay_positions.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=4 eligible=False: `outputs/intake_pack/01_alipay_positions_to_fill.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=28 eligible=False: `outputs/intake_pack/06_alipay_positions_review_prefill.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=28 eligible=False: `outputs/preflight/alipay_holdings_review_matrix.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=28 eligible=False: `outputs/preflight/alipay_positions_candidate_from_quantlab.csv`
  - schema does not match holdings intake
- **candidate_file** rows=0 eligible=False: `outputs/preflight/alipay_fund_execution_window_evidence.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `outputs/preflight/holdings_discovery_latest.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:HoldingsImportHistory.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:HoldingsBook.json`
  - non-csv or unsupported candidate
- **quantlab_holdings_book** rows=28 eligible=False: `external:HoldingsBook.csv`
  - manual_review_required: newest=2026-06-05, stale_days=8, quality=['carried_forward_unverified', 'video_visible', 'video_visible_lowres']
- **csv_candidate** rows=9 eligible=False: `external:confirmed_holding_candidates.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=12 eligible=False: `external:alipay_sample.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=4148 eligible=False: `external:支付宝交易明细(20250604-20260603).csv`
  - schema does not match holdings intake
- **csv_candidate** rows=15 eligible=False: `external:holdings.csv`
  - schema does not match holdings intake
- **candidate_file** rows=0 eligible=False: `external:HoldingSymbolMappingsFromBus.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:HoldingUpdateCandidatesFromBus.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:HoldingsMasterFromBus.json`
  - non-csv or unsupported candidate
- **csv_candidate** rows=1592 eligible=False: `external:alipay_20220605-20230605_24779d7bb0f9.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=4148 eligible=False: `external:alipay_20250604-20260603_eaff20de65cc.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=1607 eligible=False: `external:alipay_20240605-20250605_c592e6a224da.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=1552 eligible=False: `external:alipay_20230605-20240605_c16e278e987c.csv`
  - schema does not match holdings intake
- **candidate_file** rows=0 eligible=False: `external:HoldingsImportHistory.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:HoldingsBook.json`
  - non-csv or unsupported candidate
- **csv_candidate** rows=28 eligible=False: `external:HoldingsBook.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=7 eligible=False: `external:confirmed_holding_candidates.csv`
  - schema does not match holdings intake
- **candidate_file** rows=0 eligible=False: `external:alipay_fund_rule_template.json`
  - non-csv or unsupported candidate
- **candidate_file** rows=0 eligible=False: `external:ALIPAY_SMOKE_FUND.metadata.json`
  - non-csv or unsupported candidate
- **csv_candidate** rows=40 eligible=False: `external:ALIPAY_SMOKE_FUND.csv`
  - schema does not match holdings intake
- **csv_candidate** rows=40 eligible=False: `external:alipay_nav.csv`
  - schema does not match holdings intake

## Review Summary

- Rows: 28
- Row production candidates after row-level checks: 0
- Stale or missing-date rows: 28
- Special fund rule check required rows: 12
- Quality counts: `{"carried_forward_unverified": 4, "video_visible": 23, "video_visible_lowres": 1}`

Rows in the review matrix remain manual-review candidates. They do not unlock production unless the current Alipay page/export confirms fresh holdings and fund-specific rules.
