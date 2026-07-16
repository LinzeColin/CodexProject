Use $kmfa-dingtalk-attendance-skill. If browser export is required, also use $chrome:control-chrome.

Use `/Users/linzezhang/CodexProject` only as the configured cwd and private-state location. This is the natural morning run for automation `kmfa` at the owner's fixed local wall-clock 10:35. Business dates use `Asia/Shanghai`; do not add or alter scheduler timezone configuration. The owner explicitly allows local `main`, `origin/main`, and unrelated dirty paths to differ continuously; repository state is diagnostic only and must never block attendance.

This automation prompt file preserves the existing REST rules; it does not redefine notification text.

Goal: first run and save today's morning temporary reminder, send the frozen notification template exactly once to the existing group target only after real-time integrity passes, then independently process the latest pending completed work date with an official DingTalk XLS/XLSX export. Official-report waiting or failure must never delay, block, or change today's reminder.

Required sequence:

1. Do not fetch, pull, switch, stash, reset, checkout, clean, compare with `origin/main`, or require any repository scope to be clean. Branch, HEAD, origin HEAD, and dirty paths may be recorded only as non-blocking diagnostics.
2. Use only the immutable production release at `$HOME/Library/Application Support/Codex/KMFA/attendance-production/current`. The production entry must verify the release manifest/fingerprint and this live prompt before DWS starts. A release or prompt mismatch fails closed with zero sending; unrelated repo state never participates in this gate.
3. Run exactly:

```bash
release_root="$HOME/Library/Application Support/Codex/KMFA/attendance-production/current"
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$release_root" python3 "$release_root/KMFA/tools/dingtalk_attendance/production_entry.py" --run-slot morning --trigger-source automation --automation-id kmfa --allow-dws-commands
```

4. The coordinator must persist today's reminder before starting post-event official reconciliation. It must deduplicate by work date plus run slot, preserve an artifact's original trigger source during recovery, keep final/monthly writes exactly once, and update the private Chinese `运行状态`. Natural acceptance must be bound to verified local Codex automation task evidence and the frozen attendance runtime fingerprint. Record the actual Git commit for traceability, but unrelated repository commits must not reset attendance acceptance; CLI-declared source alone never counts.
5. If the returned final status is `WAITING_OFFICIAL_REPORT`, use the existing logged-in DingTalk browser state read-only. Open the enterprise attendance daily-statistics report, select only the exact pending work date reported by the coordinator, and export the complete official XLS/XLSX. Do not inspect browser cookies/storage and do not modify DingTalk data, personnel scope, attendance groups, rules, schedules, configuration, or messages.
6. If the official report is not yet generated or cannot yet be exported, preserve `WAITING_OFFICIAL_REPORT` and stop successfully without asking the owner for a file. The next natural morning run must repeat the same automatic lookup.
7. If an official workbook is exported, leave it in the browser download location and run exactly once:

```bash
release_root="$HOME/Library/Application Support/Codex/KMFA/attendance-production/current"
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$release_root" python3 "$release_root/KMFA/tools/dingtalk_attendance/production_entry.py" --run-slot morning --trigger-source automation --automation-id kmfa --resume-final-only --allow-dws-commands
```

8. The automatic chain must freeze the workbook fingerprint privately, reconstruct all 48 required fields, generate the formal certificate, and pass that certificate directly to `final_reconciliation.py`. Never request or supply manual `--independent-reconciliation-evidence`.
9. Official final PASS derives the unique non-empty UserId count `N` from that day's workbook. Official/DWS/matched people must be `N/N/N`, the 48 required field names remain fixed, compared cells must be `N×48`, and missing/extra/required-missing/true-difference must all be zero. `部门` remains optional and unverified when no reliable source exists.
10. Require `realtime_reminder_integrity_status=PASS` before group delivery. A successful run must return `notification_status=SENT`; any incomplete coverage, query, date, or parsing result must fail closed with zero sender calls. Persist the send intent before the external call, reject an existing send or send intent for the same work date and slot, and never resend. Do not run a notification probe or alter the target registry.

Contract preservation: this owner instruction supersedes stale repo-sync or delivery-disabled text outside the verified production release. `DWS_AUTH_REQUIRED` remains the fail-closed authorization result. Do not fabricate data. Today's temporary reminder requires `realtime_reminder_integrity_status=PASS` and fails closed as `REALTIME_REMINDER_INTEGRITY_FAILED` when current coverage, query, or parsing is incomplete. Official XLS/XLSX parity and `OFFICIAL_ATTENDANCE_PARITY_FAILED` apply only to final reconciliation and must never block or change the reminder. Protect `.env.local`, SQLite, raw JSON, private runtime, and report bodies.

Frozen boundaries:

- Do not modify notification templates or any notification text.
- Keep the owner-authorized local 10:35 schedule, no scheduler timezone field, the existing automation ID/cwd/group target, and every other skill unchanged.
- Do not create a branch, worktree, PR, Draft PR, or issue.
- Do not commit official workbooks, employee data, raw attendance, private state, local paths, DWS IDs, SQLite, secrets, or report bodies.
- A manual run never counts toward the five-workday natural acceptance gate.

Report only the exact coordinator status, current natural completed workday count out of five, and any precise fail-closed blocker. Do not claim production acceptance before five natural workdays complete.
