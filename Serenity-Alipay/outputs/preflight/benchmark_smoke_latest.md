# Benchmark Source Smoke

- Generated at: 2026-06-29T17:31:30+08:00
- Window: 2025-05-29 to 2026-06-29 (dynamic_latest_weekday)
- Production ready: True

## MooMoo Candidates

- Shanghai Composite `SH.000001` (exact_index): fail - No permission to get quotes for SH.000001. Please check CN MarketIndixes quote permissions.
- S&P 500 `US..SPX` (exact_index): fail - US stock indices are not supported
- S&P 500 `US.SPX` (exact_index): fail - Unknown stock. SPX
- S&P 500 `US.SPY` (proxy_etf): pass - ok
- S&P 500 `US.VOO` (proxy_etf): pass - ok

## Public Aggregation Exact Fallback

- Shanghai Composite `000001.SS` (exact_index_fallback): pass rows=263 - ok
- S&P 500 `^GSPC` (exact_index_fallback): pass rows=271 - ok

## Thematic Benchmark Sources

- Nasdaq 100 `NDX` via `^NDX` (thematic_index): pass rows=271 - ok
- Hang Seng TECH ETF proxy `HSTECH_PROXY` via `3033.HK` (thematic_proxy): pass rows=266 - ok
- ChiNext Index `399006.SZ` via `0.399006` (thematic_index): fail rows=0 - RemoteDisconnected: Remote end closed connection without response
- CNI Chip Index `CNI_CHIP` via `0.980017` (thematic_index): fail rows=0 - RemoteDisconnected: Remote end closed connection without response
- CSI All Share Semiconductor Index `H30184.CSI` via `2.H30184` (thematic_index): fail rows=0 - RemoteDisconnected: Remote end closed connection without response
- CSI Semiconductor Index `931865.CSI` via `2.931865` (thematic_index): fail rows=0 - RemoteDisconnected: Remote end closed connection without response
- CSI Artificial Intelligence Index `930713.CSI` via `2.930713` (thematic_index): fail rows=0 - RemoteDisconnected: Remote end closed connection without response

## Manual Local History

- Shanghai Composite `000001.SH`: warn, rows=263, sample_like=False
- S&P 500 `SPX`: warn, rows=271, sample_like=False

## Production Gate

- S&P 500: ready
- Shanghai Composite: ready
