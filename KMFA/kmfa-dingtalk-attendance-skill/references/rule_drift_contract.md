# Rule Drift Contract

## Why this exists

The main accuracy risk is not token usage. The main risk is rule drift: one rule in Skill, another in repo code, another in DB config, another in historical notes.

## Rule source priority

1. Active user instruction.
2. Repo implementation and tests.
3. Database `policy_version` and `rule_config_snapshot`.
4. Skill reference files.
5. Historical notes.

## Drift checks

Run before stage-2 acceptance:

| Check | Example |
|---|---|
| Personnel category drift | 无需考勤人员 / 只排除休息提醒人员 mismatch. |
| Threshold drift | 自然月第 23 个有效考勤日 mismatch. |
| Target-month drift | 自然月 vs payroll month mismatch. |
| Location rule drift | geofence threshold changed without policy version bump. |
| Shift rule drift | shift definition changed after derived facts generated. |
| Approval rule drift | correction/leave approval handling changed. |

## Stop rule

If any P0/P1 drift exists, do not mark stage-2 accepted. Produce `rule_drift_report.md` and keep all run artifacts.
