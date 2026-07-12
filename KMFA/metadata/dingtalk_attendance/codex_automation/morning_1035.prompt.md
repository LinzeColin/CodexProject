Use $kmfa-dingtalk-attendance-skill. If browser export is required, also use $chrome:control-chrome.

Work only in `/Users/linzezhang/CodexProject` on `main`. This is the natural morning run for automation `kmfa`. Business dates use `Asia/Shanghai`; do not alter the scheduler or its timezone configuration.

This automation prompt file preserves the existing REST rules; it does not redefine notification text.

Goal: run the morning temporary reminder and automatically close the latest pending completed work date with an independent DingTalk official XLS/XLSX export. Delivery is hard-disabled.

Required sequence:

1. Confirm branch `main`, `HEAD == origin/main`, no extra worktree, canonical skill present, and tracked files clean. Do not touch the five unrelated pre-existing untracked files.
2. Run the package preflight, runtime inspection, offline validation, month gate, and attendance config-only healthcheck. Fail closed if current read-only DWS authorization is not ready.
3. Run exactly:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot morning --trigger-source automation --automation-id kmfa --allow-dws-commands
```

4. The coordinator must deduplicate by work date plus run slot, recover completed artifacts after interruption, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Never bypass its state or artifact probes.
5. If the returned final status is `WAITING_OFFICIAL_REPORT`, use the existing logged-in DingTalk browser state read-only. Open the enterprise attendance daily-statistics report, select only the exact pending work date reported by the coordinator, and export the complete official XLS/XLSX. Do not inspect browser cookies/storage and do not modify DingTalk data, personnel scope, attendance groups, rules, schedules, configuration, or messages.
6. If the official report is not yet generated or cannot yet be exported, preserve `WAITING_OFFICIAL_REPORT` and stop successfully without asking the owner for a file. The next natural morning run must repeat the same automatic lookup.
7. If an official workbook is exported, leave it in the browser download location and run exactly once:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot morning --trigger-source automation --automation-id kmfa --resume-final-only --allow-dws-commands
```

8. The automatic chain must freeze the workbook fingerprint privately, reconstruct all 48 required fields, generate the formal certificate, and pass that certificate directly to `final_reconciliation.py`. Never request or supply manual `--independent-reconciliation-evidence`.
9. Official final PASS requires 44/44/44 people, 48 compared columns, 2,112 compared cells, missing/extra/required-missing/true-difference all zero; `部门` remains optional and unverified when no reliable source exists.
10. Require `notification_status=NOT_SENT_OWNER_DISABLED`; message count and target calls must stay zero. Do not probe, resend, or invoke any sender.

Contract preservation: `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. The reminder still requires exact `attendance report columns/query-data`, `official_report_parity_status=PASS`, and fail-closed `OFFICIAL_ATTENDANCE_PARITY_FAILED`. Any changed prompt must be committed and pushed to GitHub `main`. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Do not modify schedule, time, timezone, automation ID, cwd, sending targets, or another skill.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- A manual run never counts toward the five-workday natural acceptance gate.

Report only the exact coordinator status, current natural completed workday count out of five, and any precise fail-closed blocker. Do not claim production acceptance before five natural workdays complete.
