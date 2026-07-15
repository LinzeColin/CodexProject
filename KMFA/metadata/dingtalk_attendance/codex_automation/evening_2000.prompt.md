Use $kmfa-dingtalk-attendance-skill.

Work only in `/Users/linzezhang/CodexProject` on `main`. This is the natural evening run for automation `kmfa-3`. The scheduler remains pure local-wall-clock 20:05 with no timezone field; business dates use `Asia/Shanghai` only inside the runner.

The existing stage-2 and payroll baseline behavior is out of scope and must not be changed or promoted by this run.

Goal: run the evening temporary reminder as one idempotent, interruption-safe step and send the frozen notification template exactly once to the existing group target only after real-time integrity passes.

Required sequence:

1. Confirm branch `main`, fetch `origin/main`, require the attendance runtime code, rules, configuration, and both prompt mirrors to match `origin/main`, and require the attendance scope to have no tracked or untracked changes. Unrelated repository migration state must not be inspected, changed, or used to block this attendance run. Do not create an extra worktree.
2. Run the package preflight, runtime inspection, offline validation, attendance config-only healthcheck, and evening month gate. Fail closed if current read-only DWS authorization is not ready.
3. Run exactly:

```bash
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/automatic_closure.py --run-slot evening --trigger-source automation --automation-id kmfa-3 --allow-dws-commands
```

4. The coordinator must deduplicate by work date plus run slot, recover completed artifacts after interruption, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Never bypass its state or artifact probes.
5. Require `realtime_reminder_integrity_status=PASS` for the temporary reminder and `notification_status=SENT` for a successful group delivery. Incomplete current coverage, query, date, or parsing must fail closed as `REALTIME_REMINDER_INTEGRITY_FAILED` with zero sender calls. Persist the send intent before the external call, reject an existing send or send intent for the same work date and slot, and never resend. Do not run a notification probe or alter the target registry.
6. A manual run never counts toward the five-workday natural acceptance gate. Report the exact coordinator status and current natural completed workday count out of five.

Contract preservation: `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. The evening temporary reminder uses only the real-time reminder integrity gate. Official XLS/XLSX parity, 48 required fields, and `OFFICIAL_ATTENDANCE_PARITY_FAILED` belong only to final reconciliation and must not block morning or evening reminders. Any changed prompt must be committed and pushed to GitHub `main`. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Keep the owner-authorized local 20:05 schedule, no scheduler timezone field, the existing automation ID/cwd/group target, and every other skill unchanged.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- Do not claim production acceptance before five natural workdays complete.
