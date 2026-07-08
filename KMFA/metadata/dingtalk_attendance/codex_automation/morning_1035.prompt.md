# 每日早晚钉钉考勤检查｜晨报

Use $kmfa-dingtalk-attendance-skill.

如果当前 Codex agent 不能自动解析 repo-scoped skill，读取并遵守：

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

每天北京时间 10:35 在 KMFA local main checkout 执行。当前部署 cwd 为 `/Users/linzezhang/CodexProject`；迁移到新电脑时使用同一 GitHub repo 的 `main` checkout。

运行约束：
1. 确认 cwd 是 KMFA 所在的 `LinzeColin/CodexProject` checkout，branch 为 `main`，且 `HEAD == origin/main`。
2. 确认 `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` 存在。
3. 设置 `TZ=Asia/Shanghai` 和 `KMFA_RUN_SLOT=morning`。
4. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh`。
5. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`。
6. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`。
7. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot morning --print-json`。
8. 运行 `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`。
9. 只有在本机授权允许时才执行晨报入口；否则 fail closed，报告 `DWS_AUTH_REQUIRED` 或配置 blocker。Do not fabricate data。
10. 晨报不执行 stage-2 acceptance，不提升 Q5，不生成 payroll baseline。
11. 休息提醒规则必须来自 skill：`REST_REQUIRED_THRESHOLD_DAYS = 23`；`丁春法` 和 `李永占` 只排除出 `需要休息`，其他状态照常统计。
12. 如果用户明确要求指定日期测试且只发张霖泽个人，入口必须加 `--work-date YYYY-MM-DD --notification-targets personal`；不得发送生产管理群。
13. 如果本次 run 修改 skill、automation prompt、metadata、validator 或相关配置，必须完成验证、commit，并 push 到 GitHub `main` 后再报告完成。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai
```

指定日期个人测试示例（仅 owner 明确要求时使用）：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai --work-date 2026-07-06 --notification-targets personal
```

硬边界：
- 不提交 secrets、`.env.local`、resolved DWS IDs、SQLite、raw JSON/JSONL/GZ、员工明文、OneDrive raw archives 或 report bodies。
- 不创建 branch、PR、issue 或 worktree。
- `KMFA/metadata` 只保存 public metadata/config；private runtime 和 DingTalk raw payloads 必须保持 ignored/private。

输出中文摘要：取数状态、异常人数、管理报告状态、HR 报告状态、通知状态、OneDrive 归档状态、清理状态、数据库大小、泄密风险。
