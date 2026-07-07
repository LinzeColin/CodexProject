# KMFA Daily Routine Check Metadata

Public-safe metadata for `Dingtalk-routine-check / 钉钉工作检查`.

This metadata controls a local skill that reads existing DWS output from OneDrive:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/
```

It does not create the upstream DWS archive automation.
If only `DWS_Outputs.zip` or `DWS_Archive/` exists, healthcheck reports
`SOURCE_INPUT_FOLDER_MISSING`; the checker requires direct group folders with
`chat_records/chat_records.csv` and `_manifest/manifest.csv`.

Scheduler contract:

```text
one automation only: Dingtalk-routine-check / 钉钉工作检查
timezone: Asia/Shanghai
daily 11:35 -> trigger_window=morning_1135
daily 17:05 -> trigger_window=evening_1705
```

Every run log must include `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`. Missing or stale upstream DWS output is recorded as `SOURCE_MISSING` or `SOURCE_STALE`. Routine abnormalities use `abnormal_type=late|review|wrong|merged|missing` plus `reminder_level=P0|P1|P2`.

Morning runs also produce `cash_risk_result` for 杨婷资金账户监控. The public-safe offline implementation extracts `total_available_cash` from DWS message text using configured markers in `cash_monitor.public.yaml`; image/file candidates without a structured amount become `CASH_NEEDS_REVIEW`.

Private runtime data belongs under:

```text
KMFA/metadata/daily_routine_check/private_runtime/
```

OneDrive durable logs and snapshots belong under:

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
