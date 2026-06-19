# Intake Gap Report

Generated: 2026-06-12

## Production Blockers

| Area | Current evidence | Required fix |
|---|---|---|
| Alipay positions | `data/imports/alipay_positions.csv` has 4 rows but source notes contain sample markers. | Replace with real Alipay/fund-platform holdings or manually transcribed verifiable current holdings. |
| Fund rules | `data/manual/fund_rules.csv` is sample/manual-local and missing `FUND006.redemption_status`, `FUND006.redemption_fee`. | Replace with Alipay path or fund-company official evidence for all execution fields. |
| Candidate universe | `data/manual/candidates.csv` is local/manual sample-like and has insufficient official source coverage. | Replace or extend with MooMoo, Alipay, fund-company, exchange, or official evidence chains. |

## Current Warnings

| Area | Current evidence | Preferred improvement |
|---|---|---|
| Benchmark history | `data/manual/benchmark_price_history.csv` now contains exact Shanghai Composite and S&P 500 fallback history from Yahoo Finance chart API. | Prefer MooMoo, official exchange/index provider, Alipay, or fund-company official source chain when available. |

## Latest Intake Validator

- `production_ready=false`
- `block_count=33`
- `warn_count=2`
- Block areas: `alipay_positions`, `fund_rules`, `candidate_universe`
- Warning area: `benchmark_history`
- Gap CSV: `outputs/preflight/intake_gap_latest.csv`

## Templates

- `app/templates/alipay_positions_template.csv`
- `app/templates/fund_rules_template.csv`
- `app/templates/candidates_template.csv`
- `app/templates/benchmark_price_history_template.csv`

## Gate Commands

```bash
python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
python -m app.cli benchmark-smoke --require-production --json
python -m app.cli preflight --require-production --json
```

Production remains blocked until every command returns success and `production_ready=true`.
