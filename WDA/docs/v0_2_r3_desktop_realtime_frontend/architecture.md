# Architecture

```text
/Users/linzezhang/Downloads/WDA.app or WDA.command
  -> WDA/scripts/wda_app_start.sh
  -> /Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/.venv
  -> FastAPI service on 127.0.0.1:18730
  -> read-only v0.2-R2 Data Core
  -> local dashboard, status, report index, logs
```

## Components

- `WDA/app_api/core.py`: local runtime, read-only SQLite status, report index, dashboard rendering, update run records.
- `WDA/app_api/main.py`: FastAPI routes and HTML pages.
- `WDA/app_api/cli.py`: command-line entry for init, status, update, serve, open, and background start.
- `WDA/scripts/*.sh`: app start/stop/status/update, launcher install, scheduler install/uninstall.
- Runtime root: local full-sensitive operational outputs under `WDA_MetaData`.

## Dependency Strategy

The repo does not vendor FastAPI dependencies. `wda_app_start.sh` creates a local runtime venv under `WDA_MetaData/v0_2_r3_app_runtime/.venv` and installs `WDA/requirements-v0_2_r3.txt` there if needed. This keeps the system Python unchanged.

## Current Tradeoff

R3 P1 uses a lightweight app bundle plus FastAPI instead of Tauri/Electron. That maximizes local usability and verification speed while preserving a later packaging upgrade path.
