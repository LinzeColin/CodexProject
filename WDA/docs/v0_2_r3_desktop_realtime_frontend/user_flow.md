# User Flow

## Open

1. User double-clicks `/Users/linzezhang/Downloads/WDA.app` or fallback `/Users/linzezhang/Downloads/WDA.command`.
2. The launcher runs `WDA/scripts/wda_app_start.sh`.
3. The script prepares the local runtime venv if needed, starts the FastAPI service, and opens `http://127.0.0.1:18730/`.

## Read

The dashboard opens with:

- Action Center
- Risk Center
- Opportunity Center
- Contact Radar
- Work Handoff
- Personal Behavior Optimization
- data freshness and system state

Technical row counts are available but are not the main experience.

## Update

1. User clicks `立即更新`.
2. Frontend posts to `/api/update/run`.
3. Backend refreshes local status, report index, dashboard snapshot, and logs under the R3 runtime root.
4. User can inspect `/api/update/runs` or the system page.

## Recover

- Stop service: `WDA/scripts/wda_app_stop.sh`
- Check status: `WDA/scripts/wda_app_status.sh`
- Reinstall launcher: `WDA/scripts/install_wda_app_launcher.sh`
- Rebuild runtime snapshot: `WDA/scripts/wda_app_update.sh`
