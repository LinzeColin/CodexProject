# Benchmark Source Smoke

- Generated at: 2026-06-24T12:20:31+08:00
- Window: 2025-05-24 to 2026-06-24 (dynamic_latest_weekday)
- Production ready: True

## MooMoo Candidates

- None

## Public Aggregation Exact Fallback

- Shanghai Composite `000001.SS` (exact_index_fallback): pass rows=263 - ok
- S&P 500 `^GSPC` (exact_index_fallback): pass rows=270 - ok

## Thematic Benchmark Sources

- Nasdaq 100 `NDX` via `^NDX` (thematic_index): pass rows=270 - ok
- Hang Seng TECH ETF proxy `HSTECH_PROXY` via `3033.HK` (thematic_proxy): pass rows=265 - ok
- ChiNext Index `399006.SZ` via `0.399006` (thematic_index): pass rows=263 - ok
- CNI Chip Index `CNI_CHIP` via `0.980017` (thematic_index): pass rows=263 - ok
- CSI All Share Semiconductor Index `H30184.CSI` via `2.H30184` (thematic_index): pass rows=263 - ok
- CSI Semiconductor Index `931865.CSI` via `2.931865` (thematic_index): pass rows=263 - ok
- CSI Artificial Intelligence Index `930713.CSI` via `2.930713` (thematic_index): pass rows=263 - ok

## Manual Local History

- Shanghai Composite `000001.SH`: warn, rows=263, sample_like=False
- S&P 500 `SPX`: warn, rows=270, sample_like=False

## Production Gate

- Shanghai Composite: ready
- S&P 500: ready
