# Serenity Production Unblock Evidence Matrix

- Generated: 2026-06-13T06:53:26+08:00
- Production ready: True
- Block count: 0
- Warn count: 6
- Gap count by area: {'alipay_positions': 4, 'benchmark_history': 2}
- Gap count by severity: {'warn': 6}

## Purpose

Production preflight currently passes. This matrix records warning/open quality items for evidence refresh. It is read-only and does not promote or execute any trading action.

## Files

- `markdown`: `outputs/preflight/PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md`
- `csv`: `outputs/preflight/production_unblock_evidence_matrix.csv`
- `json`: `outputs/preflight/production_unblock_evidence_matrix.json`

## Unlock Ladder

```bash
python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli production-unblock-matrix --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json
python -m app.cli preflight --scan-path ~/Downloads --scan-path ~/Documents --require-production --json
```

Production preflight currently passes; rerun the last two commands after any evidence refresh to confirm `production_ready=true` remains true.

## Area Requirements

### alipay_positions

- Production file: `data/imports/alipay_positions.csv`
- Intake file: `outputs/intake_pack/01_alipay_positions_to_fill.csv`
- Helper files: `outputs/intake_pack/06_alipay_positions_review_prefill.csv`
- Accepted sources: Current Alipay export, Alipay current holding page, or manually transcribed current holding with `evidence=/path/or/https-url` in source_note
- Source rule: Alipay/current platform evidence is optional overlay evidence for personal-position review; sample/demo rows are ignored by baseline production gates
- Freshness rule: as_of must be valid YYYY-MM-DD and no more than 2 Beijing-calendar days stale
- Unlock effect: Unlocks optional personal-position comparison only; baseline ranking and baseline-relative discipline do not depend on this file

| Row | Field | Severity | Current failure | Required fix |
|---|---|---|---|---|
| FUND001 | source_note | warn | optional source_note contains sample/demo marker | Replace only if you want optional real-holding overlay |
| FUND003 | source_note | warn | optional source_note contains sample/demo marker | Replace only if you want optional real-holding overlay |
| FUND004 | source_note | warn | optional source_note contains sample/demo marker | Replace only if you want optional real-holding overlay |
| FUND005 | source_note | warn | optional source_note contains sample/demo marker | Replace only if you want optional real-holding overlay |

### benchmark_history

- Production file: `data/manual/benchmark_price_history.csv`
- Intake file: `n/a`
- Helper files: `outputs/preflight/benchmark_smoke_latest.md`
- Accepted sources: MooMoo, official index/exchange provider, or exact public aggregation fallback with metadata
- Source rule: MooMoo/official preferred; public_aggregation is warning-only and cannot override higher-priority conflict
- Freshness rule: Must cover 1m, 3m, and recent 10 trading-day windows
- Unlock effect: Maintains Shanghai Composite and S&P 500 benchmark comparison windows

| Row | Field | Severity | Current failure | Required fix |
|---|---|---|---|---|
| 000001.SH | source_type | warn | Shanghai Composite uses public aggregation fallback | Prefer moomoo or official source when available |
| SPX | source_type | warn | S&P 500 uses public aggregation fallback | Prefer moomoo or official source when available |

