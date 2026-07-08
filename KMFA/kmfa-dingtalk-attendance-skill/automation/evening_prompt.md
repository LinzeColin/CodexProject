Use $kmfa-dingtalk-attendance-skill.

If the current Codex agent cannot auto-resolve repo-scoped skills, read and follow:

```text
/Users/linzezhang/CodexProject/KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

统一工作区规则：本 automation 与上游每日钉钉DWS归档、钉钉工作检查、KMFA资金周报日报自动化使用同一组 Codex cwds：
- DWS 归档项目：`/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p`
- KMFA/CodexProject：`/Users/linzezhang/CodexProject`
本 automation 的实际执行目录必须切到 `/Users/linzezhang/CodexProject` 后再运行 KMFA git、skill、test 或脚本命令；DWS 归档项目只作为上游输出和诊断可见工作区。若发现这些上游/下游 automation 的 cwds 不一致，先修正 automation 配置并报告。

Run slot: evening.
Scheduled Beijing time: 20:05.
Timezone: Asia/Shanghai. All business dates, run slots, month gates, and stage-2 windows are Beijing time.

Goal: execute the KMFA S19 DingTalk attendance evening workflow through the repo-scoped skill, preserving existing production safety while enabling v0.3 database/stage-2 readiness.

Required steps:
1. Switch to `/Users/linzezhang/CodexProject`, then confirm branch is `main`, `HEAD == origin/main`, and no extra worktree is active.
2. Confirm canonical skill path exists: `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md`.
3. Set `TZ=Asia/Shanghai` and `KMFA_RUN_SLOT=evening`.
4. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`.
5. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`.
6. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`.
7. Run existing S19 config-only healthcheck: `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`.
8. Run the existing S19 evening entry only if current local authorization permits it; otherwise fail closed and report `DWS_AUTH_REQUIRED` / config blocker. Do not fabricate data.
9. Acquire or replay DingTalk attendance result/detail evidence only through approved local S19/DWS paths.
10. Store public-safe metadata under `KMFA/metadata`; keep private raw payloads in ignored private runtime or OneDrive.
11. Run `KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot evening --print-json`.
12. If day 1-5 of the following month, run `KMFA/kmfa-dingtalk-attendance-skill/scripts/run_stage2_evening.sh`.
13. `run_stage2_evening.sh` must write stage-2 artifacts only from an approved source adapter, explicit `KMFA_STAGE2_SOURCE_JSON` replay snapshot, or `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` with `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR` pointing to a private raw replay day-fact/linkage bundle.
14. Raw replay day-fact sources may prove raw-to-derived reconciliation and location evidence, but must keep database commit/verification gates false until approved non-production PostgreSQL execution and state verification proofs exist.
15. If an approved non-production DB target is configured, generate a pre-consensus DB landing bundle, guard-execute the PostgreSQL load plan, run read-only post-load row-count verification with `verify_postgres_landing_state.py`, and apply both proofs with `apply_stage2_database_proof.py` before writing Stage-2 run artifacts.
16. If no DB execution proof or state verification proof is available, keep DB gates false; day-5 consensus must fail closed rather than fabricate database proof.
17. If no approved source is configured, treat `STAGE2_ADAPTER_SOURCE_MISSING` as a fail-closed blocker; do not fabricate data.
18. If this is day 5, `run_stage2_evening.sh` must run `KMFA/kmfa-dingtalk-attendance-skill/scripts/stage2_consensus_gate.py`.
19. If five canonical hashes match exactly and P0/P1 unresolved counts are zero, generate stage-2 consensus certificate and payroll baseline candidate.
20. If they do not match, generate divergence report and stop promotion.
21. Preserve rest reminder rules from the skill: `REST_REQUIRED_THRESHOLD_DAYS = 23`; `丁春法` and `李永占` are excluded only from `需要休息`, while all other statuses are counted normally.
22. If the owner explicitly requests a date-specific personal-only test, run the entry with `--work-date YYYY-MM-DD --notification-targets personal`; do not send the production management group.
23. If this run changes any skill or automation prompt file, run validators, commit, and push to GitHub `main` before reporting completion.

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
