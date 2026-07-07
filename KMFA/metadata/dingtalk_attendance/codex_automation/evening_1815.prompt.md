# 每日早晚钉钉考勤检查｜晚报

Use $kmfa-dingtalk-attendance-skill.

如果当前 Codex agent 不能自动解析 repo-scoped skill，读取并遵守：

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

每天北京时间 18:15 在 KMFA local main checkout 执行。当前部署 cwd 为 `/Users/linzezhang/CodexProject`；迁移到新电脑时使用同一 GitHub repo 的 `main` checkout。

运行约束：
1. 确认 cwd 是 KMFA 所在的 `LinzeColin/CodexProject` checkout，branch 为 `main`，且 `HEAD == origin/main`。
2. 确认 `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` 存在。
3. 设置 `TZ=Asia/Shanghai` 和 `KMFA_RUN_SLOT=evening`。
4. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`。
5. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`。
6. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`。
7. 运行 `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`。
8. 只有在本机授权允许时才执行晚报入口；否则 fail closed，报告 `DWS_AUTH_REQUIRED` 或配置 blocker。Do not fabricate data。
9. 只能通过 approved local S19/DWS path 获取或 replay DingTalk attendance result/detail evidence。
10. public-safe metadata 写入 `KMFA/metadata`；private raw payloads 保持在 ignored private runtime 或 OneDrive。
11. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot evening --print-json`。
12. 如果处于次月第 1-5 天窗口，运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/run_stage2_evening.sh`。
13. `run_stage2_evening.sh` 只能使用 approved source adapter、显式 `KMFA_STAGE2_SOURCE_JSON` replay snapshot，或 `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` + private `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR`。
14. raw replay day-fact source 只能证明 raw-to-derived reconciliation 和 location evidence；未取得非生产 PostgreSQL execution proof 与 state verification proof 前，database commit/verification gates 必须保持 false。
15. 如果配置了 approved non-production DB target，先生成 pre-consensus DB landing bundle，再 guard-execute PostgreSQL load plan，然后用 `verify_postgres_landing_state.py` 做 read-only row-count verification，最后用 `apply_stage2_database_proof.py` 同时应用 execution proof 和 state verification proof。
16. 如果没有 DB execution proof 或 state verification proof，DB gates 必须保持 false；day-5 consensus 必须 fail closed，不能伪造 database proof。
17. 如果没有 approved source，报告 `STAGE2_ADAPTER_SOURCE_MISSING` 并停止。Do not fabricate data。
18. 第 5 天必须运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/stage2_consensus_gate.py`。
19. 只有五次 canonical hash 完全一致且 P0/P1 unresolved 均为 0，才允许生成 stage-2 consensus certificate 和 payroll baseline candidate。
20. 不一致时生成 divergence report 并停止 promotion。
21. 休息提醒规则必须来自 skill：`REST_REQUIRED_THRESHOLD_DAYS = 23`；`丁春法` 和 `李永占` 只排除出 `需要休息`，其他状态照常统计。
22. 如果本次 run 修改 skill、automation prompt、metadata、validator 或相关配置，必须完成验证、commit，并 push 到 GitHub `main` 后再报告完成。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai
```

硬边界：
- 不提交 secrets、`.env.local`、resolved DWS IDs、SQLite、raw JSON/JSONL/GZ、员工明文、OneDrive raw archives 或 report bodies。
- 不创建 branch、PR、issue 或 worktree。
- 不得在 accepted stage-2 consensus 之前 promote payroll baseline。
- `KMFA/metadata` 只保存 public metadata/config；private runtime 和 DingTalk raw payloads 必须保持 ignored/private。

输出中文摘要：取数状态、异常人数、管理报告状态、HR 报告状态、通知状态、OneDrive 归档状态、清理状态、数据库大小、泄密风险。
