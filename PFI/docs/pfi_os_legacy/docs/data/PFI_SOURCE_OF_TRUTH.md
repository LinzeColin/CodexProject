# PFI Source Of Truth

Version: PFI-001

PFI OS uses one formal source of truth per data responsibility. JSON and CSV are
allowed for import, export, fixture, and cache only; they are not the formal
runtime source of truth.

## Formal Stores

| Responsibility | Store | Notes |
| --- | --- | --- |
| Tasks, approvals, holdings events, trade events, user settings, research records, notifications | Operational SQLite | Stored under `$PFI_OS_DATA_HOME/private/operational/pfi.sqlite` |
| Market, financial, macro, feature, backtest, and analytical time series | DuckDB + Parquet | Point-in-time and reproducible analytical store |
| Immutable source files | Immutable raw file store | Content hash, source id, capture time, license/access notes |
| Document search | Local FTS | MVP text search only |
| Semantic retrieval | Optional vector store | After MVP only when clearly needed |
| Secrets | macOS Keychain or repo-external `.env` | Never committed |

## Processing Layers

```text
D0 Source Registry / Policy
D1 Immutable Raw Capture
D2 Parse / Normalize / Entity Resolution
D3 Point-in-Time Canonical Warehouse
D4 Features / Models / Backtests / Risk
D5 User Projections / Evidence / Decisions
```

No UI page may read directly from provider JSON, raw downloaded files, or
ResearchBus bridge files as its formal data model.

## ResearchBus Role

ResearchBus is demoted to an internal event and workflow compatibility layer.
It may carry requests, heartbeats, adapter status, and migration events. It must
not remain a competing official fact source for holdings, trades, market data,
research conclusions, or strategy results.

## Strategy And Training Truth

- Backtest truth includes data range, provider, adjustment mode, strategy
  version, parameter set, cost model, run id, generated time, and code version.
- Parameter scans, train/test validation, and walk-forward results are evidence
  for strategy validation; they do not create trading instructions.
- Market-feel training truth includes visible-window data, hidden answer
  window, user answer, actual outcome, timing, and post-review note.
