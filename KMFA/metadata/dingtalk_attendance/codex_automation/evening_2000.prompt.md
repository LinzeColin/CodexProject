Use $kmfa-dingtalk-attendance-skill.

Work only in `/Users/linzezhang/CodexProject` on `main`. This is the natural evening run for automation `kmfa-3`. The scheduler remains pure local-wall-clock 20:00 with no timezone field; business dates use `Asia/Shanghai` only inside the runner.

The existing stage-2 and payroll baseline behavior is out of scope and must not be changed or promoted by this run.

Goal: run the evening temporary reminder as one idempotent, interruption-safe, no-send step in the automatic attendance closure.

Required sequence:

1. Confirm branch `main`, `HEAD == origin/main`, no extra worktree, canonical skill present, and tracked files clean. Do not touch the five unrelated pre-existing untracked files.
2. Run the package preflight, runtime inspection, offline validation, attendance config-only healthcheck, and evening month gate. Fail closed if current read-only DWS authorization is not ready.
3. Run exactly:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot evening --trigger-source automation --automation-id kmfa-3 --allow-dws-commands
```

4. The coordinator must deduplicate by work date plus run slot, recover completed artifacts after interruption, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Never bypass its state or artifact probes.
5. Require official-report parity for the temporary reminder and `notification_status=NOT_SENT_OWNER_DISABLED`; message count and target calls must stay zero. Do not probe, resend, or invoke any sender.
6. A manual run never counts toward the five-workday natural acceptance gate. Report the exact coordinator status and current natural completed workday count out of five.

Contract preservation: `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. The reminder still requires exact `attendance report columns/query-data`, `official_report_parity_status=PASS`, and fail-closed `OFFICIAL_ATTENDANCE_PARITY_FAILED`. Any changed prompt must be committed and pushed to GitHub `main`. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Do not modify schedule, time, timezone, automation ID, cwd, sending targets, or another skill.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- Do not claim production acceptance before five natural workdays complete.
