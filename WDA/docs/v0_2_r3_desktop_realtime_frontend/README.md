# WDA v0.2-R3 Desktop Realtime Frontend

This folder contains repo-safe docs for WDA v0.2-R3 P1. It describes the local runtime, FastAPI service, dashboard, launcher, update scripts, scheduler template, report quality bar, data boundary, and current acceptance evidence.

## Local Outputs

- Runtime root: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/`
- Dashboard snapshot: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/dashboard/index.html`
- State: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/state/`
- Logs: `/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/logs/`
- App entry: `/Users/linzezhang/Downloads/WDA.app`
- Fallback entry: `/Users/linzezhang/Downloads/WDA.command`

## Repo Outputs

- `WDA/app_api/core.py`
- `WDA/app_api/main.py`
- `WDA/app_api/cli.py`
- `WDA/scripts/wda_app_start.sh`
- `WDA/scripts/wda_app_stop.sh`
- `WDA/scripts/wda_app_status.sh`
- `WDA/scripts/wda_app_update.sh`
- `WDA/scripts/install_wda_app_launcher.sh`
- `WDA/scripts/install_wda_launch_agent.sh`
- `WDA/scripts/uninstall_wda_launch_agent.sh`
- `WDA/tests/test_v0_2_r3_app.py`

## Current Status

R3 P1 is implemented and locally verified. R3 P2 remains planned for report v2 copy quality, richer evidence drill-down, and final product-grade UX hardening.
