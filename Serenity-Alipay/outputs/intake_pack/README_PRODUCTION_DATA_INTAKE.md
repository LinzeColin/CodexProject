# Serenity Production Intake Pack

Generated: 2026-06-13T05:57:05+08:00

## Status

- Production ready: False
- Block gaps: 33
- Warn gaps: 2
- Gap areas: {'alipay_positions': 4, 'fund_rules': 16, 'candidate_universe': 13, 'benchmark_history': 2}

## Files To Fill

- `README`: `outputs/intake_pack/README_PRODUCTION_DATA_INTAKE.md`
- `field_guide`: `outputs/intake_pack/FIELD_GUIDE.md`
- `evidence_guide`: `outputs/intake_pack/EVIDENCE_INTAKE_GUIDE.md`
- `alipay_positions_to_fill`: `outputs/intake_pack/01_alipay_positions_to_fill.csv`
- `fund_rules_to_fill`: `outputs/intake_pack/02_fund_rules_to_fill.csv`
- `candidates_to_fill`: `outputs/intake_pack/03_candidates_to_fill.csv`
- `gap_actions`: `outputs/intake_pack/04_gap_actions.csv`
- `discovered_files`: `outputs/intake_pack/05_discovered_candidate_files.csv`
- `review_prefill`: `outputs/intake_pack/06_alipay_positions_review_prefill.csv`
- `special_rule_checklist`: `outputs/intake_pack/07_special_fund_rule_checklist.csv`
- `fund_rule_review_checklist`: `outputs/intake_pack/08_fund_rules_from_review_checklist.csv`
- `candidate_source_review_prefill`: `outputs/intake_pack/09_candidate_source_review_prefill.csv`
- `summary_json`: `outputs/intake_pack/production_intake_pack_latest.json`

## Review-Matrix Assisted Files

- `review_prefill`: optional stale/manual-review Alipay candidate rows generated from the local holdings review matrix.
- `special_rule_checklist`: QDII/global/HK/special fund rows that must be checked against Alipay/fund-company rules before production.
- `fund_rule_review_checklist`: per-holding rule fields and source queries for filling `02_fund_rules_to_fill.csv`.
- `candidate_source_review_prefill`: per-holding source-chain queries for filling `03_candidates_to_fill.csv`.
- These helper files are not copied by `promote-intake-pack`; they are only aids for filling `01/02/03` after current-page confirmation.

## Required Fixes

### alipay_positions
- `FUND001` / `source_note`: source_note contains sample/demo marker -> Replace with real source note such as Alipay export date or verified manual snapshot
- `FUND003` / `source_note`: source_note contains sample/demo marker -> Replace with real source note such as Alipay export date or verified manual snapshot
- `FUND004` / `source_note`: source_note contains sample/demo marker -> Replace with real source note such as Alipay export date or verified manual snapshot
- `FUND005` / `source_note`: source_note contains sample/demo marker -> Replace with real source note such as Alipay export date or verified manual snapshot

### fund_rules
- `FUND001` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND002` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND003` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND004` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND004` / `source_type`: Source type is not production-grade: aggregated -> Use moomoo, alipay, or official
- `FUND004` / `source_priority`: Source priority 5 is below production threshold -> Use source priority 1-3
- `FUND004` / `fallback_aggregated`: Aggregated fallback cannot unlock execution rules -> Replace with official or Alipay evidence
- `FUND005` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND006` / `source`: Fund rule source is sample/manual-local -> Replace with Alipay path or fund-company official evidence
- `FUND006` / `source_type`: Source type is not production-grade: aggregated -> Use moomoo, alipay, or official
- `FUND006` / `source_priority`: Source priority 5 is below production threshold -> Use source priority 1-3
- `FUND006` / `fallback_aggregated`: Aggregated fallback cannot unlock execution rules -> Replace with official or Alipay evidence
- ... 4 more gaps in `gap_actions.csv`

### candidate_universe
- `FUND001` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND002` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND003` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND004` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND004` / `source_type`: Source type is not production-grade: aggregated -> Use moomoo, alipay, or official
- `FUND004` / `official_source_count`: Official source count 1 < 2 -> Add at least two official-grade sources
- `FUND004` / `fallback_aggregated`: Aggregated fallback cannot unlock production candidate -> Replace with production-grade sources
- `FUND005` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND006` / `source`: Candidate source is sample/manual-local -> Replace with moomoo, Alipay, fund-company, or official source
- `FUND006` / `source_type`: Source type is not production-grade: aggregated -> Use moomoo, alipay, or official
- `FUND006` / `official_source_count`: Official source count 0 < 2 -> Add at least two official-grade sources
- `FUND006` / `fallback_aggregated`: Aggregated fallback cannot unlock production candidate -> Replace with production-grade sources
- ... 1 more gaps in `gap_actions.csv`

## Acceptance Commands

```bash
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli preflight --require-production --json
```

Do not run `--apply` until every `REPLACE_...` and `YYYY-MM-DD` marker is replaced. The promotion command blocks placeholders and backs up existing production files before copying.
