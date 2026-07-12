Use $kmfa-dingtalk-attendance-skill. If browser export is required, also use $chrome:control-chrome.

Work only in `/Users/linzezhang/CodexProject` on `main`. This is the natural morning run for automation `kmfa`. Business dates use `Asia/Shanghai`; do not alter the scheduler or its timezone configuration.

This automation prompt file preserves the existing REST rules; it does not redefine notification text.

Goal: first run and save today's morning temporary reminder, then independently process the latest pending completed work date with an official DingTalk XLS/XLSX export. Official-report waiting or failure must never delay, block, or change today's reminder. Delivery is hard-disabled.

Required sequence:

1. Confirm branch `main`, `HEAD == origin/main`, no extra worktree, canonical skill present, and tracked files clean. Do not touch the five unrelated pre-existing untracked files.
2. Run the package preflight, runtime inspection, offline validation, month gate, and attendance config-only healthcheck. Fail closed if current read-only DWS authorization is not ready.
3. Run exactly:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot morning --trigger-source automation --automation-id kmfa --allow-dws-commands
```

4. The coordinator must persist today's reminder before starting post-event official reconciliation. It must deduplicate by work date plus run slot, preserve an artifact's original trigger source during recovery, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Natural acceptance must be bound to verified local Codex automation task evidence and the exact Git commit plus both prompt fingerprints; CLI-declared source alone never counts.
5. If the returned final status is `WAITING_OFFICIAL_REPORT`, use the existing logged-in DingTalk browser state read-only. Open the enterprise attendance daily-statistics report, select only the exact pending work date reported by the coordinator, and export the complete official XLS/XLSX. Do not inspect browser cookies/storage and do not modify DingTalk data, personnel scope, attendance groups, rules, schedules, configuration, or messages.
6. If the official report is not yet generated or cannot yet be exported, preserve `WAITING_OFFICIAL_REPORT` and stop successfully without asking the owner for a file. The next natural morning run must repeat the same automatic lookup.
7. If an official workbook is exported, leave it in the browser download location and run exactly once:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot morning --trigger-source automation --automation-id kmfa --resume-final-only --allow-dws-commands
```

8. The automatic chain must freeze the workbook fingerprint privately, reconstruct all 48 required fields, generate the formal certificate, and pass that certificate directly to `final_reconciliation.py`. Never request or supply manual `--independent-reconciliation-evidence`.
9. Official final PASS derives the unique non-empty UserId count `N` from that day's workbook. Official/DWS/matched people must be `N/N/N`, the 48 required field names remain fixed, compared cells must be `N×48`, and missing/extra/required-missing/true-difference must all be zero. `部门` remains optional and unverified when no reliable source exists.
10. Require `notification_status=NOT_SENT_OWNER_DISABLED`; message count and target calls must stay zero. Do not probe, resend, or invoke any sender.

Contract preservation: `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. The reminder still requires exact `attendance report columns/query-data`, `official_report_parity_status=PASS`, and fail-closed `OFFICIAL_ATTENDANCE_PARITY_FAILED`. Any changed prompt must be committed and pushed to GitHub `main`. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Do not modify schedule, time, timezone, automation ID, cwd, sending targets, or another skill.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- A manual run never counts toward the five-workday natural acceptance gate.

Report only the exact coordinator status, current natural completed workday count out of five, and any precise fail-closed blocker. Do not claim production acceptance before five natural workdays complete.
