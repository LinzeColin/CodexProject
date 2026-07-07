Use $kmfa-dingtalk-attendance-skill.

If the current Codex agent cannot auto-resolve repo-scoped skills, read and follow:

```text
/Users/linzezhang/CodexProject/KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

Run slot: evening.
Timezone: Asia/Shanghai. All business dates, run slots, month gates, and stage-2 windows are Beijing time.

Goal: execute the KMFA S19 DingTalk attendance evening workflow through the repo-scoped skill, preserving existing production safety while enabling v0.3 database/stage-2 readiness.

Required steps:
1. Confirm cwd is `/Users/linzezhang/CodexProject`, branch is `main`, `HEAD == origin/main`, and no extra worktree is active.
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
14. Raw replay day-fact sources may prove raw-to-derived reconciliation and location evidence, but must keep database commit/verification gates false until an approved non-production PostgreSQL execution proof exists.
15. If an approved non-production DB target is configured, generate a pre-consensus DB landing bundle, guard-execute the PostgreSQL load plan, and apply the execution proof with `apply_stage2_database_proof.py` before writing Stage-2 run artifacts.
16. If no DB execution proof is available, keep DB gates false; day-5 consensus must fail closed rather than fabricate database proof.
17. If no approved source is configured, treat `STAGE2_ADAPTER_SOURCE_MISSING` as a fail-closed blocker; do not fabricate data.
18. If this is day 5, `run_stage2_evening.sh` must run `KMFA/kmfa-dingtalk-attendance-skill/scripts/stage2_consensus_gate.py`.
19. If five canonical hashes match exactly and P0/P1 unresolved counts are zero, generate stage-2 consensus certificate and payroll baseline candidate.
20. If they do not match, generate divergence report and stop promotion.
21. Preserve rest reminder rules from the skill: `REST_REQUIRED_THRESHOLD_DAYS = 23`; `丁春法` and `李永占` are excluded only from `需要休息`, while all other statuses are counted normally.
22. If this run changes any skill or automation prompt file, run validators, commit, and push to GitHub `main` before reporting completion.

Hard boundaries:
- Do not commit secrets, `.env.local`, resolved DWS IDs, SQLite, raw JSON/JSONL/GZ, employee plaintext, OneDrive raw archives, or report bodies.
- Do not create branch, PR, issue, or worktree.
- Do not promote payroll baseline without accepted stage-2 consensus.
- Treat tracked `KMFA/metadata` as public metadata/config source; private DingTalk raw payloads stay private.

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
