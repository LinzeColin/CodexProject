# EVA/EVA_OS Agent Continuity

Last updated: 2026-06-13

This repository is the handoff surface for continuing EVA_OS / EVA_OS development without replaying the full Codex thread. Treat the files in this repo as the current engineering source of truth, then verify with local commands before making changes.

## Current Operating Name

- Product name: `EVA_OS`
- Historical / repo name: `EVA_OS`
- Quant subsystem name retained in code: `QuantLab`

## Current Local Source

The latest prepared workspace at the time of upload was:

```text
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance
```

The workspace was copied from the historical implementation path:

```text
/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance
```

The upload intentionally excludes virtual environments, caches, private holdings/imports, raw video frames, local logs, SQLite runtime state, and secrets. See `UPLOAD_MANIFEST.md`.

## Local App Entry Points

Installed local launchers:

```text
/Users/linzezhang/Desktop/EVA_OS.app
/Users/linzezhang/Downloads/EVA_OS.app
/Applications/EVA_OS.app
```

Repository template and installer:

```text
macos/EVA_OS.app
scripts/installEVAOSEntryApps.sh
```

## Start Here

Read these first, in order:

1. `README.md`
2. `HANDOFF.md`
3. `docs/EVA_OS.md`
4. `docs/Index.md`
5. `15_OPEN_QUESTIONS.md`
6. `UPLOAD_MANIFEST.md`

## Completed Foundation

The system already has these productized layers or MVPs:

| Layer | Current artifact |
| --- | --- |
| Market Event Layer | `src/quantlab/data/market_events.py`, `scripts/marketEventLayer.sh`, `docs/MarketEventLayer.md` |
| Reproducible Data Lake | `src/quantlab/data/lake.py`, `scripts/dataLakeManifest.sh`, `docs/ReproducibleDataLake.md` |
| Event Replay MVP | `src/quantlab/data/replay.py`, `scripts/eventReplay.sh`, `docs/EventReplay.md` |
| macOS EVA_OS entry apps | `macos/EVA_OS.app`, `scripts/installEVAOSEntryApps.sh` |
| Token ROI Ledger | `docs/TokenROI.md`, `data/value/*latest*` |
| Company CashFlow Command | `docs/CompanyCashFlowCommand.md`, `data/cashflow` excluded unless explicitly restored locally |
| Policy Intelligence Radar | `docs/PolicyIntelligenceRadar.md`, latest public-safe summaries only |
| Consumption Guard | `docs/ConsumptionGuard.md`, latest public-safe summaries only |
| Executive Command Center | `src/quantlab/executive/command_center.py`, `scripts/commandCenter.sh`, `docs/ExecutiveCommandCenter.md` |

## Current Architecture Direction

EVA_OS is moving toward:

1. event-driven market layer,
2. reproducible data lake,
3. deterministic event replay,
4. three-mode backtest/simulation core,
5. TradingView-like chart and strategy UX,
6. Moomoo-like realtime research workflow,
7. fail-closed evidence, risk, and approval gates.

The reference concepts are LEAN, vectorbt, Kafka, Arrow, QuestDB, ClickHouse, ABIDES, and StockSim. These are architecture references, not mandatory dependencies.

## Latest Verified Run

Latest verified engineering step: `EVA_OS app identity, icon, and legacy launcher cleanup`.

Validated evidence from the implementation run:

```text
EVA_OS app plist/icon check: passed for Desktop, Downloads, and Applications
legacy-name scan: no deprecated product-name text or filename residue in scoped project
target report regeneration: Token ROI, Policy Radar, Consumption Guard, Report Decision Support, and Command Center regenerated
deleted old legacy PDFs: 3 historical 2026-06-07 PDFs
py_compile: passed for renamed app/report/data/integration modules
target pytest: 28 passed in 31.48s
```

Do not claim the full suite passed. The old historical `.venv` was deleted during slimming. The five report scripts used in the latest run fall back to `QUANTLAB_PYTHON` or system `python3`; recreate full dependencies before broad testing:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,app,data]'
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_replay.py tests/test_data_lake_manifest.py tests/test_market_event_layer.py tests/test_scripts.py -q -p no:cacheprovider
```

## Safety Boundaries

- No autonomous real-money trading.
- No unattended broker order placement.
- No stored brokerage passwords or API secrets.
- No automatic payments, bank transfers, tax filings, or government submissions.
- All trading-adjacent outputs are research, review queues, simulations, or broker-ready intents requiring explicit human confirmation.

## Recommended Next Run

Next subsystem: `Vectorized Research Mode MVP`.

Minimal target:

1. read `data/replay/EventReplay_latest.json`,
2. convert replay records to a stable OHLCV DataFrame,
3. expose a thin API for fast strategy parameter scans,
4. keep it read-only and deterministic,
5. add focused tests and one CLI smoke command,
6. do not modify UI or realtime adapters yet.

See `15_OPEN_QUESTIONS.md` for remaining scope and sequencing.

## Latest Sync And Slimming Run

The 2026-06-13 GitHub sync and local slimming run added public-safe launcher templates, refreshed handoff boundaries, and documented local retention/deletion policy in:

```text
cleanup/EVA_OS_GitHub_Sync_Local_Slimming_20260613.md
```
