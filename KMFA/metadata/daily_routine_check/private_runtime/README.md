# Daily Routine Check Private Runtime

This directory is a Git-tracked placeholder only.

Do not place active runtime files here. Active runtime files live in OneDrive:

```text
local-resource://PRIVATE_RUNTIME/daily_routine_check/
```

Expected OneDrive private runtime files include:

- `daily_routine_check.sqlite`
- `daily_routine_check.sqlite-wal`
- `daily_routine_check.sqlite-shm`
- `.env.local`
- `notification_targets.local.json`

Do not commit SQLite files, raw DWS exports, OCR raw bodies, webhook URLs, tokens, resolved DingTalk IDs, screenshots, or notification receipts.
