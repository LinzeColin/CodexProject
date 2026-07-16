Use $kmfa-dingtalk-attendance-skill.

Use `/Users/linzezhang/CodexProject` only as the configured cwd and private-state location. This is the natural evening run for automation `kmfa-3`. The scheduler remains pure local-wall-clock 20:05 with no timezone field; business dates use `Asia/Shanghai` only inside the runner. The owner explicitly allows local `main`, `origin/main`, and unrelated dirty paths to differ continuously; repository state is diagnostic only and must never block attendance.

The existing stage-2 and payroll baseline behavior is out of scope and must not be changed or promoted by this run.

Goal: run the evening temporary reminder as one idempotent, interruption-safe step and send the frozen notification template exactly once to the existing group target only after real-time integrity passes.

Required sequence:

1. Do not fetch, pull, switch, stash, reset, checkout, clean, compare with `origin/main`, or require any repository scope to be clean. Branch, HEAD, origin HEAD, and dirty paths may be recorded only as non-blocking diagnostics.
2. Use only the immutable production release at `$HOME/Library/Application Support/Codex/KMFA/attendance-production/current`. The production entry must verify the release manifest/fingerprint and this live prompt before DWS starts. A release or prompt mismatch fails closed with zero sending; unrelated repo state never participates in this gate.
3. Run exactly:

```bash
release_root="$HOME/Library/Application Support/Codex/KMFA/attendance-production/current"
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$release_root" python3 "$release_root/KMFA/tools/dingtalk_attendance/production_entry.py" --run-slot evening --trigger-source automation --automation-id kmfa-3 --allow-dws-commands
```

4. The coordinator must deduplicate by work date plus run slot, recover completed artifacts after interruption, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Never bypass its state or artifact probes.
5. Require `realtime_reminder_integrity_status=PASS` for the temporary reminder and `notification_status=SENT` for a successful group delivery. Incomplete current coverage, query, date, or parsing must fail closed as `REALTIME_REMINDER_INTEGRITY_FAILED` with zero sender calls. Persist the send intent before the external call, reject an existing send or send intent for the same work date and slot, and never resend. Do not run a notification probe or alter the target registry.
6. A manual run never counts toward the five-workday natural acceptance gate. Report the exact coordinator status and current natural completed workday count out of five.

Contract preservation: this owner instruction supersedes stale repo-sync or delivery-disabled text outside the verified production release. `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. The evening temporary reminder uses only the real-time reminder integrity gate. Official XLS/XLSX parity, 48 required fields, and `OFFICIAL_ATTENDANCE_PARITY_FAILED` belong only to final reconciliation and must not block morning or evening reminders. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Keep the owner-authorized local 20:05 schedule, no scheduler timezone field, the existing automation ID/cwd/group target, and every other skill unchanged.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- Do not claim production acceptance before five natural workdays complete.
