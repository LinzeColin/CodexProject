Use $kmfa-dingtalk-attendance-skill.

If the current Codex agent cannot auto-resolve repo-scoped skills, read and follow:

```text
/Users/linzezhang/CodexProject/KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

统一工作区规则：本 KMFA automation 只使用 KMFA/CodexProject 工作间：
- KMFA/CodexProject：`/Users/linzezhang/CodexProject`
本 automation 的实际执行目录必须切到 `/Users/linzezhang/CodexProject` 后再运行 KMFA git、skill、test 或脚本命令；上游 DWS 归档是独立 automation，只提供已生成的 OneDrive/DWS 输出。若发现本 automation 的 cwd 不是 `/Users/linzezhang/CodexProject`，先修正 automation 配置并报告。

Run slot: morning.
Scheduled Beijing time: 10:35.
Timezone: Asia/Shanghai. All business dates, run slots, and stage gates are Beijing time.

Goal: execute the KMFA 钉钉考勤 skill morning temporary-reminder workflow and finalize the latest pending completed work date from DingTalk's official report. Attendance delivery remains disabled.

Required steps:
1. Switch to `/Users/linzezhang/CodexProject`, then confirm branch is `main`, `HEAD == origin/main`, and no extra worktree is active.
2. Confirm canonical skill path exists: `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md`.
3. Set `TZ=Asia/Shanghai` and `KMFA_RUN_SLOT=morning`.
4. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`.
5. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`.
6. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`.
7. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot morning --print-json`.
8. Run existing attendance skill config-only healthcheck: `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`.
9. When DWS is authorized, first run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/final_reconciliation.py --latest-pending --timezone Asia/Shanghai --allow-dws-commands`. `NO_PENDING_FINAL_RECONCILIATION` is a valid no-op. Any pending work date must reach exact official parity or fail closed. Do not fabricate data or a final result.
9a. Then run the existing attendance skill morning entry as a `TEMPORARY_REMINDER` only if current local authorization through `KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS` permits it; otherwise fail closed and report `DWS_AUTH_REQUIRED` / config blocker. The entry must use current DingTalk attendance-group members plus exact `attendance report columns/query-data` values as the only business-statistics source. `record get`, two-punch inference, and personal `summary` are diagnostics only.
10. Require `official_report_parity_status=PASS`, exact Beijing business-date coverage, and `official_report_coverage_count == member_count` before any temporary reminder or final reconciliation. On `OFFICIAL_ATTENDANCE_PARITY_FAILED`, stop without sending and never fall back to record/summary guesses.
10d. Attendance delivery is owner-disabled. Require `notification_status=NOT_SENT_OWNER_DISABLED`; do not probe targets, resend, or invoke any sender.
10a. The production official collector intentionally skips the legacy per-member record/summary sweep. Do not run that sweep before or after the entry.
10b. Do not interrupt the entry while its process is still inside the runner's bounded DWS timeout/retry budget.
10c. When the authoritative healthcheck is READY, a running process or later timeout must never be reported as DWS_AUTH_REQUIRED; report the entry's exact final JSON status and exit code.
11. Do not perform stage-2 acceptance in the morning run.
12. Do not promote Q5 or payroll baseline in the morning run.
13. Preserve rest reminder rules from the skill: `REST_REQUIRED_THRESHOLD_DAYS = 23`; `丁春法` and `李永占` are excluded only from `需要休息`, while all other statuses are counted normally.
14. If the owner explicitly requests a date-specific personal-only test, run the entry with `--work-date YYYY-MM-DD --notification-targets personal`; do not send the production management group.
15. If this run changes any skill or automation prompt file, run validators, commit, and push to GitHub `main` before reporting completion.

Hard boundaries:
- Do not commit secrets, `.env.local`, resolved DWS IDs, SQLite, raw JSON/JSONL/GZ, employee plaintext, OneDrive raw archives, or report bodies.
- Do not create branch, PR, issue, or worktree.
- Treat tracked `KMFA/metadata` as public metadata/config source; private DingTalk raw payloads stay private.
- Do not modify upstream DWS archive outputs.

Final response format:

```text
status: passed|warning|failed
run_slot: morning
target_month: YYYYMM
stage2_eligible: false
freshness: ok|warning|failed
P0/P1 unresolved: N/N
next_action: ...
```