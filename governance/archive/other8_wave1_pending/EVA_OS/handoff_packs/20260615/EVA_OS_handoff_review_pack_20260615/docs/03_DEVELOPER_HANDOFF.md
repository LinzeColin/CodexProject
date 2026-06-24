# 新开发者交接说明

## First Rule

Do not start by changing code. First read the current source of truth:

```text
README.md
HANDOFF.md
AGENT_CONTINUITY.md
15_OPEN_QUESTIONS.md
UPLOAD_MANIFEST.md
docs/EVA_OS.md
docs/Index.md
```

## Local Project

```text
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance
```

GitHub:

```text
https://github.com/LinzeColin/EVA_OS
HEAD: b9a2c0351efaed332bd6f15b677b32c5835576da
```

## Environment Notes

The old `.venv` was removed during slimming. Some scripts now fall back to `QUANTLAB_PYTHON` or system `python3`, but broad development should recreate a full environment.

Recommended setup:

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,app,data]'
```

## Safe Verification Commands

Focused checks used recently:

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_command_center.py \
  tests/test_cashflow_command.py \
  tests/test_policy_radar.py \
  tests/test_consumption_guard.py \
  tests/test_market_event_layer.py \
  tests/test_data_lake_manifest.py \
  tests/test_event_replay.py \
  -q -p no:cacheprovider
```

If `.venv` is unavailable, do not claim the tests passed. Either rebuild `.venv` or document exactly which runtime was used.

## Architecture Map

| Area | Paths |
| --- | --- |
| UI | `src/quantlab/app/streamlit_app.py`, `src/quantlab/app/dashboard.py` |
| Backtest and strategies | `src/quantlab/backtest`, `src/quantlab/strategies`, `src/quantlab/indicators` |
| Data providers and quality | `src/quantlab/data`, `src/quantlab/data/providers` |
| Market events / data lake / replay | `src/quantlab/data/market_events.py`, `src/quantlab/data/lake.py`, `src/quantlab/data/replay.py` |
| Reports | `src/quantlab/reports`, `docs/ReportGuide.md` |
| Executive command center | `src/quantlab/executive/command_center.py` |
| Token ROI | `src/quantlab/value/token_roi.py` |
| Business systems | `src/quantlab/business`, `src/quantlab/policy`, `src/quantlab/consumption` |
| External integrations | `src/quantlab/integrations/site52etf.py` |
| System identity and health | `src/quantlab/system/eva_identity.py`, `src/quantlab/system/health.py` |
| Scripts | `scripts/**` |
| Tests | `tests/**` |

## Development Rules

1. Work on one subsystem at a time.
2. Preserve research-only safety boundaries.
3. Do not upload private holdings, screenshots, SQLite runtime state, secrets, `.env`, logs, or raw imports.
4. Update docs and tests when behavior changes.
5. Push meaningful continuity changes to GitHub.
6. Keep `HANDOFF.md` short and factual.
7. Avoid broad refactors of the 7,000+ line Streamlit app unless the target run is specifically UI modularization.

## Current Highest-ROI Next Run

Default next run: `Vectorized Research Mode MVP`.

Scope:

1. Read `data/replay/EventReplay_latest.json`.
2. Convert replay events to a stable OHLCV DataFrame.
3. Expose a fast parameter-scan adapter.
4. Add focused tests.
5. Keep it read-only and deterministic.
6. Do not add realtime trading or broker execution.

## Definition of Done for New Work

A future change should not be considered done until:

- code is implemented in the smallest relevant modules;
- docs are updated;
- focused tests pass;
- safety boundaries are unchanged or stronger;
- generated artifacts are refreshed only when relevant;
- `HANDOFF.md` is updated if continuity changed;
- GitHub push is complete when the user asked for sync.
