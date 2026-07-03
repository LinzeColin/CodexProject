# Auto Update Runtime

## Manual Update

Manual update is available from:

- Dashboard button `立即更新`
- `POST /api/update/run`
- `WDA/scripts/wda_app_update.sh`

## Runtime Files

The update writes under:

```text
/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime/
```

Key files:

- `state/status.json`
- `state/last_run.json`
- `reports/report_index.json`
- `dashboard/index.html`
- `dashboard/dashboard_payload.json`
- `logs/<run_id>.log`

## Current Update Scope

R3 P1 refreshes status, report index, dashboard snapshot, and local logs from the v0.2-R2 Data Core and report workspace. It does not rerun old-computer export, transfer, or full import.

## Recovery

If update fails:

1. Check `state/last_run.json`.
2. Check `logs/`.
3. Run `WDA/scripts/wda_app_status.sh`.
4. Re-run `WDA/scripts/wda_app_update.sh`.
