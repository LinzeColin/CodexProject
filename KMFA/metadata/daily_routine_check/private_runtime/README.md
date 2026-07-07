# Daily Routine Check Private Runtime

This directory is for local-only runtime files used by `Dingtalk-routine-check / 钉钉工作检查`.

Allowed local files include:

- `daily_routine_check.sqlite`
- `daily_routine_check.sqlite-wal`
- `daily_routine_check.sqlite-shm`
- `.env.local`
- `notification_targets.local.json`

Do not commit SQLite files, raw DWS exports, OCR raw bodies, webhook URLs, tokens, resolved DingTalk IDs, screenshots, or notification receipts.
