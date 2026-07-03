# WDA

WDA is a local-first WeChat Data Analysis control plane. The active delivery line is `v0.2-R3 Desktop Realtime Frontend`: a double-click local entry, FastAPI local service, Chinese dashboard, manual update runtime, launchd scheduler template, and repo-safe operating docs on top of the verified v0.2-R2 local Data Core.

## Current State

- project_id: `WDA`
- version: `0.2-r3`
- local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- branch: `codex/wda`
- local Data Core: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r2/full_auto_workspace/data_core/wda_v0_2_r2.sqlite`
- R3 runtime root: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime`
- local app entry: `/Users/linzezhang/Downloads/WDA.app`
- fallback entry: `/Users/linzezhang/Downloads/WDA.command`
- local service: `http://127.0.0.1:18730/`

## What Exists

- `WDA/app_api/`: FastAPI app and local runtime core.
- `WDA/scripts/wda_app_start.sh`: prepare local venv, start service, open dashboard.
- `WDA/scripts/wda_app_update.sh`: refresh R3 local status, report index, dashboard snapshot, and logs.
- `WDA/scripts/wda_app_status.sh`: print current local status JSON.
- `WDA/scripts/install_wda_app_launcher.sh`: install `WDA.app` and `WDA.command`.
- `WDA/scripts/install_wda_launch_agent.sh`: write optional launchd scheduled update plist.
- `WDA/docs/v0_2_r3_desktop_realtime_frontend/`: repo-safe R3 docs and acceptance evidence.

## Data Boundary

Do not commit raw messages, SQLite DB files, Raw Import Packs, transfer bundles, keys, decrypted DBs, private report content, local venvs, logs, or runtime state. Full-sensitive outputs stay under `/Users/linzezhang/Downloads/WDA_MetaData`.

## Verification

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest WDA.tests.test_v0_2_r3_app
WDA/scripts/wda_app_update.sh
WDA/scripts/wda_app_start.sh
curl -sS http://127.0.0.1:18730/api/health
curl -sS http://127.0.0.1:18730/api/status
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

## Remaining Work

R3 P1 is a usable local skeleton. R3 P2 still needs product-grade Chinese report rewriting, deeper evidence drill-down, responsive/detail-page QA, and final acceptance audit before claiming full product-grade completion.
