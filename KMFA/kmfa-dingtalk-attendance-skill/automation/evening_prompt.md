Use $kmfa-dingtalk-attendance-skill.

If the current Codex agent cannot auto-resolve repo-scoped skills, read and follow:

```text
/Users/linzezhang/CodexProject/KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

统一工作区规则：本 KMFA automation 只使用 KMFA/CodexProject 工作间：
- KMFA/CodexProject：`/Users/linzezhang/CodexProject`
本 automation 的实际执行目录必须切到 `/Users/linzezhang/CodexProject` 后再运行 KMFA git、skill、test 或脚本命令；上游 DWS 归档是独立 automation，只提供已生成的 OneDrive/DWS 输出。若发现本 automation 的 cwd 不是 `/Users/linzezhang/CodexProject`，先修正 automation 配置并报告。

Run slot: evening.
Scheduled local wall-clock time: 20:00.
Scheduler timezone: none. Keep one pure RRULE and never convert 20:00 for UTC offset or daylight-saving changes.
Business-date timezone passed to the runner: Asia/Shanghai. All business dates, run slots, month gates, and stage-2 windows use Beijing dates; this must not shift the scheduler time.

Goal: execute the KMFA S19 DingTalk attendance evening workflow through the repo-scoped skill, preserving existing production safety while enabling v0.3 database/stage-2 readiness.

Required steps:
1. Switch to `/Users/linzezhang/CodexProject`, then confirm branch is `main`, `HEAD == origin/main`, and no extra worktree is active.
2. Confirm canonical skill path exists: `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md`.
3. Set `TZ=Asia/Shanghai` and `KMFA_RUN_SLOT=evening`.
4. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`.
5. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh` as advisory diagnostics only.
6. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`.
7. Run existing S19 config-only healthcheck: `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`. The config-only healthcheck is authoritative for current DWS PAT/runtime readiness; a stale App Key warning from `inspect_runtime.sh` alone is not a blocker.
8. Only when the authoritative healthcheck is `READY` and current local authorization permits DWS commands, run this exact S19 evening entry once; otherwise fail closed and report `DWS_AUTH_REQUIRED` / config blocker. Do not fabricate data.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai
```

Treat every nonzero command exit code as a failed automation run; do not report success from partial collection or failed notification delivery.
9. The entry must use current DingTalk attendance-group members plus exact `attendance report columns/query-data` values as the only business-statistics source. Require `official_report_parity_status=PASS`, exact Beijing business-date coverage, and `official_report_coverage_count == member_count` before any conclusion or notification. `record get`, two-punch inference, and personal `summary` are diagnostics only. On `OFFICIAL_ATTENDANCE_PARITY_FAILED`, stop without sending and never fall back to record/summary guesses.
10. Acquire or replay DingTalk attendance result/detail evidence only through approved local S19/DWS paths.
11. Store public-safe metadata under `KMFA/metadata`; keep private raw payloads in ignored private runtime or OneDrive.
12. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot evening --print-json`.
13. If day 1-5 of the following month, run `KMFA/kmfa-dingtalk-attendance-skill/scripts/run_stage2_evening.sh`.
14. `run_stage2_evening.sh` must write stage-2 artifacts only from an approved source adapter, explicit `KMFA_STAGE2_SOURCE_JSON` replay snapshot, or `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` with `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR` pointing to a private raw replay day-fact/linkage bundle.
15. Raw replay day-fact sources may prove raw-to-derived reconciliation and location evidence, but must keep database commit/verification gates false until approved non-production PostgreSQL execution and state verification proofs exist.
16. If an approved non-production DB target is configured, generate a pre-consensus DB landing bundle, guard-execute the PostgreSQL load plan, run read-only post-load row-count verification with `verify_postgres_landing_state.py`, and apply both proofs with `apply_stage2_database_proof.py` before writing Stage-2 run artifacts.
17. If no DB execution proof or state verification proof is available, keep DB gates false; day-5 consensus must fail closed rather than fabricate database proof.
18. If no approved source is configured, treat `STAGE2_ADAPTER_SOURCE_MISSING` as a fail-closed blocker; do not fabricate data.
19. If this is day 5, `run_stage2_evening.sh` must run `KMFA/kmfa-dingtalk-attendance-skill/scripts/stage2_consensus_gate.py`.
20. If five canonical hashes match exactly and P0/P1 unresolved counts are zero, generate stage-2 consensus certificate and payroll baseline candidate.
21. If they do not match, generate divergence report and stop promotion.
22. Preserve rest reminder rules from the skill: `REST_REQUIRED_THRESHOLD_DAYS = 23`; `丁春法` and `李永占` are excluded only from `需要休息`, while all other statuses are counted normally.
23. If the owner explicitly requests a date-specific personal-only test, run the entry with `--work-date YYYY-MM-DD --notification-targets personal`; do not send the production management group.
24. If this run changes any skill or automation prompt file, run validators, commit, and push to GitHub `main` before reporting completion.

Hard boundaries:
- Do not commit secrets, `.env.local`, resolved DWS IDs, SQLite, raw JSON/JSONL/GZ, employee plaintext, OneDrive raw archives, or report bodies.
- Do not create branch, PR, issue, or worktree.
- Do not promote payroll baseline without accepted stage-2 consensus.
- Treat tracked `KMFA/metadata` as public metadata/config source; private DingTalk raw payloads stay private.
- Do not modify upstream DWS archive outputs.

Final response format:

```text
status: passed|warning|failed
run_slot: evening
target_month: YYYYMM
stage2_eligible: true|false
stage2_status: not_eligible|pending|accepted|failed
canonical_hash: sha256:...
quality_grade: Q0-Q5
P0/P1 unresolved: N/N
location_evidence: pass|warning|failed
trajectory_evidence: pass|warning|failed
next_action: ...
```
