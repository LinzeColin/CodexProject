# 每日早晚钉钉考勤检查｜晚报

Use $kmfa-dingtalk-attendance-skill.

如果当前 Codex agent 不能自动解析 repo-scoped skill，读取并遵守：

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

每天本机墙钟 20:00 在 KMFA local main checkout 执行。scheduler 不设置时区，只保留一个纯 RRULE；不得因 UTC offset 或夏令时变化换算 20:00。考勤 runner 内部仍使用 `Asia/Shanghai` 判定业务日期，但不能据此平移 scheduler 时间。当前部署 cwd 为 `/Users/linzezhang/CodexProject`；迁移到新电脑时使用同一 GitHub repo 的 `main` checkout。

统一工作区规则：本 automation 只使用 KMFA/CodexProject：`/Users/linzezhang/CodexProject`。本 automation 的实际执行目录必须切到该目录后再运行 KMFA git、skill、test 或脚本命令；上游 DWS 归档是独立 automation，只提供已生成输出。若本 automation 的 cwd 不一致，先修正 automation 配置并报告。

运行约束：
1. 切到 `/Users/linzezhang/CodexProject`，再确认 branch 为 `main`，且 `HEAD == origin/main`。
2. 确认 `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` 存在。
3. 设置 `TZ=Asia/Shanghai` 和 `KMFA_RUN_SLOT=evening`。
4. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`。
5. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`，只把它作为诊断信息。
6. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`。
7. 运行 `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`；这个 config-only healthcheck 是当前 DWS PAT/runtime readiness 的权威门禁，`inspect_runtime.sh` 单独出现旧 App Key warning 不能覆盖 READY 结果。
8. 只有在权威 healthcheck 为 `READY` 且本机授权允许时，才执行下方唯一晚报入口一次；否则 fail closed，报告 `DWS_AUTH_REQUIRED` 或配置 blocker。Do not fabricate data。命令非零退出时必须把 automation 标为失败，不能把部分取数或通知失败报告为成功。
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
22. 如果用户明确要求指定日期测试且只发张霖泽个人，入口必须加 `--work-date YYYY-MM-DD --notification-targets personal`；不得发送生产管理群。
23. 如果本次 run 修改 skill、automation prompt、metadata、validator 或相关配置，必须完成验证、commit，并 push 到 GitHub `main` 后再报告完成。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai
```

指定日期个人测试示例（仅 owner 明确要求时使用）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai --work-date 2026-07-06 --notification-targets personal
```

硬边界：
- 不提交 secrets、`.env.local`、resolved DWS IDs、SQLite、raw JSON/JSONL/GZ、员工明文、OneDrive raw archives 或 report bodies。
- 不创建 branch、PR、issue 或 worktree。
- 不得在 accepted stage-2 consensus 之前 promote payroll baseline。
- `KMFA/metadata` 只保存 public metadata/config；private runtime 和 DingTalk raw payloads 必须保持 ignored/private。
- 不修改上游 DWS 归档输出。

输出中文摘要：取数状态、异常人数、管理报告状态、HR 报告状态、通知状态、OneDrive 归档状态、清理状态、数据库大小、泄密风险。
