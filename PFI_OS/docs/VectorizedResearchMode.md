# Vectorized Research Mode MVP

Vectorized Research Mode converts `EventReplay_latest.json` into a stable OHLCV DataFrame, then runs deterministic parameter scans through the existing research experiment runner.

It is a research-only adapter. It does not refresh market data, connect to Moomoo, call brokers, create orders, or mutate holdings.

## Purpose

- Reduce token pressure by passing compact replay files and scan summaries instead of raw event logs.
- Provide a fast path for parameter scanning before building heavier discrete-event or agent-market simulation.
- Create a shared input layer for future TradingView-like charts and hotspot runtime optimization.

## Input

Default input:

```text
data/replay/EventReplay_latest.json
```

The adapter reads only `BarClosed` records with OHLCV payloads and sorts them by `symbol`, `datetime`, `replay_index`, and `event_id`.

## Run

```bash
scripts/vectorizedResearch.sh --symbol SPY --market US --interval 1d --param short_window=2,3 --param long_window=4,5
```

Preview without writing files:

```bash
scripts/vectorizedResearch.sh --json-only --symbol SPY
```

## Output

```text
data/vectorized/VectorizedResearch_<symbol>_<date>.json
data/vectorized/VectorizedResearch_<symbol>_<date>.csv
data/vectorized/VectorizedResearch_<symbol>_<date>.md
data/vectorized/VectorizedResearch_latest.json
data/vectorized/VectorizedResearch_latest.csv
data/vectorized/VectorizedResearch_latest.md
```

## UI Shell

The workspace status page reads `data/vectorized/VectorizedResearch_latest.json` and displays compact summary cards, chart-ready rows, and the latest output paths.

The UI chart uses the shared research chart interaction layer for scroll zoom, drag pan, hover spikes, responsive rendering, and PNG export from the latest compact JSON.

It does not reload `EventReplay_latest.json` or rerun parameter scans during page rendering. Rebuild the latest output explicitly with `scripts/vectorizedResearch.sh`.

## Current Boundary

- MVP strategy: `ma_crossover`.
- Default grid: `short_window=[2,3]`, `long_window=[4,5]`, sized for the current replay sample.
- Invalid parameter grids fail closed as `Blocked`.
- Outputs are research evidence only, not trading instructions.
