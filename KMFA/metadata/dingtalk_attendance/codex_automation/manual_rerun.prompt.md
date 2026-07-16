# 每日早晚钉钉考勤检查｜手动补跑

Use $kmfa-dingtalk-attendance-skill.

如果当前 Codex agent 不能自动解析 repo-scoped skill，读取并遵守：

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
```

手动补跑时只允许选择 `morning` 或 `evening`，所有业务日期和 run slot 都按北京时间 `Asia/Shanghai`。当前部署 cwd 为 `/Users/linzezhang/CodexProject`；迁移到新电脑时使用同一 GitHub repo 的 `main` checkout。

运行约束：
1. cwd 只作为私有状态位置；branch、HEAD、origin HEAD 和 dirty paths 仅作诊断，不得阻断。不得为补跑执行 stash、reset、checkout、clean 或覆盖 owner 开发内容。
2. 确认 `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` 存在。
3. 设置 `TZ=Asia/Shanghai`，并按补跑目标设置 `KMFA_RUN_SLOT=morning` 或 `KMFA_RUN_SLOT=evening`。
4. 只从已验证的 immutable production release 运行；固定入口为 `$HOME/Library/Application Support/Codex/KMFA/attendance-production/current` 下的 `KMFA/tools/dingtalk_attendance/production_entry.py`。repo preflight 只记录诊断，不得要求与 `origin/main` 同步或 clean。
5. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh`。
6. 运行 `KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh`。
7. 运行 `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only`。
8. 只有在本机授权允许时才执行补跑入口；否则 fail closed，报告 `DWS_AUTH_REQUIRED` 或配置 blocker。Do not fabricate data。入口必须以当前钉钉考勤组成员为统计范围，并以精确的 `attendance report columns/query-data` 官方列值作为唯一业务统计源。
9. 发送任何结论前必须满足 `official_report_parity_status=PASS`、北京时间目标业务日完全覆盖且 `official_report_coverage_count == member_count`。出现 `OFFICIAL_ATTENDANCE_PARITY_FAILED` 时停止且不发送，禁止回退到 record/summary、两卡数量或个人 summary child 猜数。
10. 若补跑 `evening` 且涉及 stage-2，必须继承晚报 prompt 的 DB proof、state verification、five-run consensus 和 payroll baseline fail-closed 边界。
11. 休息提醒规则必须来自 skill：`REST_REQUIRED_THRESHOLD_DAYS = 23`；`丁春法` 和 `李永占` 只排除出 `需要休息`，其他状态照常统计。
12. 如果本次 run 修改 skill、automation prompt、metadata、validator 或相关配置，必须完成验证、commit，并 push 到 GitHub `main` 后再报告完成。

```bash
release_root="$HOME/Library/Application Support/Codex/KMFA/attendance-production/current"
TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$release_root" python3 "$release_root/KMFA/tools/dingtalk_attendance/production_entry.py" --run-slot morning --trigger-source manual --automation-id kmfa --allow-dws-commands
```

硬边界：
- 不提交 secrets、`.env.local`、resolved DWS IDs、SQLite、raw JSON/JSONL/GZ、员工明文、OneDrive raw archives 或 report bodies。
- 不创建 branch、PR、issue 或 worktree。
- 不得伪造 DWS、database proof、state verification proof、stage-2 consensus 或 payroll baseline。
- `KMFA/metadata` 只保存 public metadata/config；private runtime 和 DingTalk raw payloads 必须保持 ignored/private。

补跑仍需遵守 live-only、OneDrive 私有归档、三天 operational cache 清理和泄密扫描。
