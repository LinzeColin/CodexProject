# KMFA Daily Routine Check Metadata

Public-safe metadata for `Dingtalk-routine-check / 钉钉工作检查`.

This metadata controls a local skill that reads existing DWS output from OneDrive. The primary input is the zip package:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

The checker streams required CSV members from this complete zip and does not copy or extract the package. It is the only upstream input. A disk `DWS_Outputs/` folder is normally absent and must never be probed, created, materialized, or used as fallback. `DWS_Outputs/<群>/...` is retained only as a member path inside the zip.

It does not create the upstream DWS archive automation.
If `DWS_Outputs.zip` is a OneDrive dataless placeholder or a corrupt zip, healthcheck reports `ZIP_INPUT_UNREADABLE` and asks for a readable hydrated zip.
Scheduled triggers execute exactly one corresponding window once and never run cleanup. The reader does not create a source cache or automatically evict the zip after each run.

Scheduler contract:

```text
one automation only: Dingtalk-routine-check / 钉钉工作检查
business clock: Asia/Shanghai
business 11:35 -> trigger_window=morning_1135
business 17:05 -> trigger_window=evening_1705
current AEST local scheduler: 13:35 and 19:05
RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3
```

The scheduler record has no explicit timezone, `DTSTART`, or `TZID`. The
local-wall-clock hours must be recalculated whenever the host UTC offset
changes; business evaluation remains `Asia/Shanghai`.

Every run log must include `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`. Missing or stale upstream DWS output is recorded as `SOURCE_MISSING` or `SOURCE_STALE`. Routine abnormalities use `abnormal_type=late|review|wrong|merged|missing` plus `reminder_level=P0|P1|P2`.

Morning runs also produce `cash_risk_result` for 杨婷资金账户监控. The public-safe offline implementation extracts `total_available_cash` from DWS message text using configured markers in `cash_monitor.public.yaml`; image/file candidates without a structured amount become `CASH_NEEDS_REVIEW`.

Private runtime data belongs under OneDrive, not inside the Git package:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime/
```

Durable logs and snapshots belong under:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/
```

Public files here:

```text
routine_rules.public.yaml
cash_monitor.public.yaml
database_manifest.json
notification_policy.yaml
onedrive_storage_manifest.yaml
retention_policy.yaml
codex_automation/*.prompt.md
```

Do not commit raw DWS outputs, SQLite ledgers, webhook URLs, token values, OCR raw bodies, screenshots, or robot delivery receipts.
