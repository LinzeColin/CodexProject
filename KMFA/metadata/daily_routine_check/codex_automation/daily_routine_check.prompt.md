# Codex Desktop Automation Prompt｜Dingtalk-routine-check

Run locally from:

```text
/Users/linzezhang/CodexProject
```

Automation:

```text
Dingtalk-routine-check / 钉钉工作检查
Timezone: Asia/Shanghai
Triggers: daily 11:35 and daily 17:05 Beijing time
```

Do not create one automation per rule. Use this single automation with the two trigger windows below.

11:35 command:

```bash
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window morning_1135 --send --cleanup --apply
```

17:05 command:

```bash
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window evening_1705 --send --cleanup --apply
```

Responsibilities:

1. Read OneDrive DWS outputs for `付款请示群` and `生产管理群`.
2. At `morning_1135`, check 付款请示群 daily items, 杨婷现金 OCR 风险, and Monday-only items when applicable.
3. At `evening_1705`, check 生产管理群 daily/Thursday/Friday items and monthly third-Friday payment tax items when applicable.
4. Use configured DWS text extraction first for 杨婷 `资金账户明细表`; image/file-only cash candidates without structured amount become `CASH_NEEDS_REVIEW` unless private OCR is explicitly configured.
5. Separately process `资金账户明细表` and `资金流水明细/资金明细`.
6. Log `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`.
7. Include `cash_risk_result` for `morning_1135`.
8. Record `SOURCE_MISSING` or `SOURCE_STALE` if upstream OneDrive DWS output is missing or stale.
8a. If healthcheck reports `SOURCE_INPUT_FOLDER_MISSING`, report the direct-folder enable conditions instead of treating `DWS_Outputs.zip` or `DWS_Archive/` as sufficient input.
9. Notify 张霖泽 only for missing, late, low-confidence, P0, P1, NO_DATA, NEEDS_REVIEW, SOURCE_MISSING, or SOURCE_STALE.
10. Run cleanup only through `--cleanup --apply`, which performs SQLite WAL checkpoint/VACUUM and `cleanup_events`; never delete DWS input.
11. Do not generate Excel.
12. Do not modify upstream DWS archive outputs.

Before live notification, verify private target config exists:

```text
KMFA/metadata/daily_routine_check/private_runtime/notification_targets.local.json
```
