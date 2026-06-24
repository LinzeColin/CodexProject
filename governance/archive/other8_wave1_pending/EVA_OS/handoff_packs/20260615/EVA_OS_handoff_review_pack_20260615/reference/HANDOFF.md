# EVA_OS Handoff

Last updated: 2026-06-13 Australia/Sydney

This file is the public-safe handoff for `LinzeColin/EVA_OS`. It is designed so a future agent can continue development without replaying the previous Codex thread. Local private run history, private holdings/imports, runtime SQLite state, and raw account screenshots are intentionally excluded from the public repository.

## Current Objective

EVA_OS is the renamed product direction for the former EVA_OS / QuantLab workspace. The current goal is to turn the personal research middle-platform into a lower-token, reproducible, product-grade research operating system.

Primary product boundaries:

- research, evidence, backtesting, simulation, reports, review queues, and human-approved order intents only;
- no autonomous real-money trading;
- no unattended broker order placement;
- no stored brokerage passwords, tokens, or API secrets;
- no private holdings/import screenshots in public GitHub.

## Current Source Of Truth

GitHub project:

```text
https://github.com/LinzeColin/EVA_OS
```

Current local working copy:

```text
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance
```

Historical duplicate source path before slimming:

```text
/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance
```

The historical path was a subset of the current working copy at this handoff and can be removed after GitHub push verification.

## Start Here

Future agents should read these files first:

1. `README.md`
2. `AGENT_CONTINUITY.md`
3. `15_OPEN_QUESTIONS.md`
4. `UPLOAD_MANIFEST.md`
5. `cleanup/EVA_OS_GitHub_Sync_Local_Slimming_20260613.md`
6. `docs/EVA_OS.md`
7. `docs/Index.md`

## Delivery Standard

For every meaningful subsystem run:

- work on one subsystem at a time unless the user explicitly expands scope;
- update `HANDOFF.md` only when the status materially changes;
- update docs/tests/scripts affected by the change;
- run focused validation or explain exactly why it could not run;
- keep public GitHub free of private holdings, account screenshots, raw imports, secrets, venvs, caches, logs, locks, and SQLite runtime state;
- push continuity-critical changes to `LinzeColin/EVA_OS`.

## Completed Foundation

| Area | Status | Main artifacts |
| --- | --- | --- |
| EVA_OS rename direction | Partial | `README.md`, `docs/EVA_OS.md`, `AGENT_CONTINUITY.md` |
| Market Event Layer MVP | Complete MVP | `src/quantlab/data/market_events.py`, `scripts/marketEventLayer.sh`, `docs/MarketEventLayer.md` |
| Reproducible Data Lake MVP | Complete MVP | `src/quantlab/data/lake.py`, `scripts/dataLakeManifest.sh`, `docs/ReproducibleDataLake.md` |
| Event Replay MVP | Complete MVP | `src/quantlab/data/replay.py`, `scripts/eventReplay.sh`, `docs/EventReplay.md` |
| Executive Command Center | Partial product | `src/quantlab/executive/command_center.py`, `scripts/commandCenter.sh`, `docs/ExecutiveCommandCenter.md` |
| Token ROI | Partial product | `docs/TokenROI.md`, `data/value/*latest*` |
| Cashflow / policy / consumption | Partial product | `docs/CompanyCashFlowCommand.md`, `docs/PolicyIntelligenceRadar.md`, `docs/ConsumptionGuard.md` |
| macOS entry apps | Complete launcher | `macos/EVA_OS.app`, `scripts/installEVAOSEntryApps.sh` |

## Latest Verified Engineering Step

Latest verified engineering step:

```text
EVA_OS app identity, icon, and legacy launcher cleanup
```

Verified evidence from the implementation run:

```text
EVA_OS app plist/icon check: passed for Desktop, Downloads, and Applications
legacy app cleanup: deleted all old visible app bundles from Desktop, Downloads, and Applications
legacy-name scan: no deprecated product-name text or filename residue in scoped project
target report regeneration: Token ROI, Policy Radar, Consumption Guard, Report Decision Support, and Command Center regenerated
deleted old legacy PDFs: 3 historical 2026-06-07 PDFs
py_compile: passed for renamed app/report/data/integration modules
target pytest: 28 passed in 31.48s
```

Important environment note:

```text
The old local .venv was deleted during slimming. The five report scripts used in this run now fall back to QUANTLAB_PYTHON or system python3 when .venv is absent. For full-suite work, recreate .venv or provide a complete QUANTLAB_PYTHON runtime.
```

Suggested setup:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,app,data]'
PYTHONPATH=src .venv/bin/python -m pytest tests/test_event_replay.py tests/test_data_lake_manifest.py tests/test_market_event_layer.py tests/test_scripts.py -q -p no:cacheprovider
```

## Current macOS Entry Points

Installed local entry apps:

```text
/Users/linzezhang/Desktop/EVA_OS.app
/Users/linzezhang/Downloads/EVA_OS.app
/Applications/EVA_OS.app
```

Portable template in repo:

```text
macos/EVA_OS.app
```

Reinstall command:

```bash
./scripts/installEVAOSEntryApps.sh
```

The app searches known local checkout paths, starts `StartQuantLab.command` in Terminal, and falls back to opening the GitHub repo if no local project is found.

## Current Unresolved Work

High-priority remaining items:

1. `Vectorized Research Mode MVP`: read `data/replay/EventReplay_latest.json`, build stable OHLCV DataFrame input, and expose a fast parameter-scan adapter.
2. `Discrete Event Simulation Mode`: deterministic event-loop simulation over replay batches.
3. `Agent Market Simulation Mode`: ABIDES/StockSim-style research simulation boundary, no real orders.
4. TradingView-like chart and strategy UX.
5. Moomoo-like realtime research adapter, read-only quote/research flow.
6. 52ETF integration.
7. Hotspot analysis runtime optimization and token-pressure reduction.
8. Merge workbench flows to reduce token/context pressure.
9. Productize Token ROI, cashflow, policy, and consumption subsystems with real input refresh, evidence gates, and UI workflows.

## Current Known Issues

- Full local test coverage still needs a recreated `.venv` or a complete `QUANTLAB_PYTHON` runtime; this run used a temporary `/tmp` dependency target for `requests` and `pytest`.
- Public GitHub intentionally excludes private holdings/imports and runtime SQLite state; restore those only from local private sources if needed.
- `DataLakeManifest_latest.json` currently indexes the MVP event log only; broader bar cache/tick/news/policy assets are future work.
- Event replay currently supports local `market_events` JSONL only.
- Full regression was not completed after Event Replay; only focused validation and interrupted full-suite progress are known.

## Recommended Next Run Contract

Target:

```text
Vectorized Research Mode MVP
```

Minimal scope:

- add `src/quantlab/research/vectorized.py` or equivalent local-pattern module;
- read `data/replay/EventReplay_latest.json`;
- convert replay bar events into a stable DataFrame keyed by symbol/time;
- expose deterministic parameter-scan input for existing strategy logic;
- add focused tests and one CLI smoke script;
- do not modify UI, realtime adapters, or broker-adjacent flows in this run.

Stop condition:

- focused tests pass, smoke command produces a stable output, docs and `HANDOFF.md` are updated, and the change is pushed to GitHub.

## Public Upload Boundary

Include in GitHub:

- source code, tests, scripts, docs, task pack, public-safe handoff files, public-safe deterministic sample data, and macOS launcher template.

Exclude from GitHub:

- `.venv`, caches, `.env`, secrets, `data/holdings/**`, `data/imports/**`, `data/researchBus/*.sqlite*`, private screenshots, local logs, pid files, and locks.

## Local Private Continuity

This run preserved the old long-form local handoff as:

```text
HANDOFF_PRIVATE_LOCAL.md
```

It is ignored by git and must not be uploaded to the public repository.
