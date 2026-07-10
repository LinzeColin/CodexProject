# Codex Desktop Automation Prompt｜Dingtalk-routine-check

Run locally from:

```text
/Users/linzezhang/CodexProject
```

Automation:

```text
Dingtalk-routine-check / 钉钉工作检查
Business clock: Asia/Shanghai
Business triggers: daily 11:35 and daily 17:05 Beijing time
Current AEST scheduler wall clock: 13:35 and 19:05
```

Do not create one automation per rule. Use this single automation with the two trigger windows below.
Each scheduled trigger must execute exactly one matching window command once.
Never execute both window commands in one task. If the current Beijing trigger
cannot be identified unambiguously, fail closed without running or notifying.

The saved scheduler must contain exactly one pure local-wall-clock rule and no
explicit timezone, `DTSTART`, `TZID`, or second RRULE line:

```text
RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3
```

`BYSETPOS=2,3` prevents the unwanted 13:05 and 19:35 Cartesian-product runs.
Recalculate the local hours whenever the host UTC offset changes.

11:35 command:

```bash
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window morning_1135 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --send
```

17:05 command:

```bash
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window evening_1705 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --send
```

Responsibilities:

1. Treat `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip` as the only upstream input. Stream only the required ZIP members for `付款请示群` and `生产管理群`.
1a. A disk `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/` folder is not an input and is normally absent. Never probe, create, materialize, copy, extract, or fall back to that folder. `DWS_Outputs/<群>/...` is allowed only as a member path inside the ZIP.
1b. Do not copy the ZIP or its members into a local cache and do not automatically evict the ZIP after each run. Read member streams in place; source-cache lifecycle remains under OneDrive/user control.
2. At `morning_1135`, check 付款请示群 daily items, 杨婷现金 OCR 风险, and Monday-only items when applicable.
3. At `evening_1705`, check 生产管理群 daily/Thursday/Friday items and monthly third-Friday payment tax items when applicable.
4. Use configured DWS text extraction first for 杨婷 `资金账户明细表`; image/file-only cash candidates without structured amount become `CASH_NEEDS_REVIEW` unless private OCR is explicitly configured.
5. Separately process `资金账户明细表` and `资金流水明细/资金明细`.
6. Log `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`.
6a. If a group source is `SOURCE_MISSING` or `SOURCE_STALE`, list its rules in `rules_blocked_by_source` and do not convert the source problem into routine `MISSING` or `CASH_NO_DATA` false positives.
7. Include `cash_risk_result` for `morning_1135`.
8. Record `SOURCE_MISSING` or `SOURCE_STALE` if upstream OneDrive DWS output is missing or stale.
8a. If healthcheck reports `ZIP_INPUT_MISSING` or `ZIP_INPUT_UNREADABLE`, fail closed and report that the sole OneDrive ZIP must be hydrated or replaced. Do not search for a directory alternative.
9. Notify 张霖泽 only for missing, late, low-confidence, P0, P1, NO_DATA, NEEDS_REVIEW, SOURCE_MISSING, or SOURCE_STALE.
10. Do not run cleanup during a scheduled routine check. `--cleanup` is a separate manually initiated maintenance action only; it must never delete or auto-evict the source ZIP.
11. Do not generate Excel.
12. Do not modify upstream DWS archive outputs.

Before live notification, verify private target config exists:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime/notification_targets.local.json
```
