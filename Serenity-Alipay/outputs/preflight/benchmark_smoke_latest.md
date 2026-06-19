# Benchmark Source Smoke

- Generated at: 2026-06-14T10:06:56+08:00
- Window: 2026-03-01 to 2026-06-12 (dynamic_latest_weekday)
- Production ready: True

## MooMoo Candidates

- Shanghai Composite `SH.000001` (exact_index): fail - No permission to get quotes for SH.000001. Please check CN MarketIndixes quote permissions.
- S&P 500 `US..SPX` (exact_index): fail - US stock indices are not supported
- S&P 500 `US.SPX` (exact_index): fail - Unknown stock. SPX
- S&P 500 `US.SPY` (proxy_etf): pass - ok
- S&P 500 `US.VOO` (proxy_etf): pass - ok

## Public Aggregation Exact Fallback

- Shanghai Composite `000001.SS` (exact_index_fallback): pass rows=71 - ok
- S&P 500 `^GSPC` (exact_index_fallback): pass rows=73 - ok

## Manual Local History

- Shanghai Composite `000001.SH`: warn, rows=71, sample_like=False
- S&P 500 `SPX`: warn, rows=73, sample_like=False

## Production Gate

- S&P 500: ready
- Shanghai Composite: ready
