# KMFA Automation Takeover Handoff

更新时间: 2026-07-10

## 当前目标

接手 KMFA 相关 Codex Desktop Scheduled automations 的稳定性维护。用户的真实问题不是卡片消失，而是 automation 长期存在但不能稳定自动运行、运行内容错误、反复回到旧工作区或旧 prompt。

## 当前结论

根因已经定位并修复: 本机曾存在两个同名 `CodexProject` 项目，KMFA automations 绑定到了旧 July 5 工作树，导致 repo 里修好的 prompt、skill、validator 没有被实际定时运行使用。

当前 canonical repo:

```text
/Users/linzezhang/CodexProject
```

当前 GitHub source of truth:

```text
LinzeColin/CodexProject main
```

当前已推送修复提交:

```text
c69d00805f63f1b982a641a919b43fcbedec86e1
KMFA automation: repair Codex project binding
```

## 当前 active automation 表

| ID | 名称 | 工作区 | 说明 |
|---|---|---|---|
| `kmfa` | `KMFA｜每日钉钉考勤检查｜晨报` | `/Users/linzezhang/CodexProject` | S19 晨报，Asia/Shanghai 10:35 |
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | `/Users/linzezhang/CodexProject` | S19 晚报，Asia/Shanghai 20:05 |
| `kmfa-4` | `KMFA｜钉钉工作检查` | `/Users/linzezhang/CodexProject` | S20 routine check，Asia/Shanghai 11:35 和 17:05 |
| `kmfa-5` | `KMFA｜资金周报自动化` | `/Users/linzezhang/CodexProject` | S21 fund weekly，Australia/Sydney 周一/周六 11:00 |
| `kmfa-dws` | `KMFA｜上游每日钉钉DWS归档` | `/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p` | 独立 DWS archive producer，不属于 KMFA 工作树 |

不要把 DWS archive 工作区加入 `kmfa`、`kmfa-3`、`kmfa-4`、`kmfa-5`。KMFA 四个 automation 只能使用 `/Users/linzezhang/CodexProject`。

## 已完成验证

### Automation / repo consistency

```bash
git -C /Users/linzezhang/CodexProject log -1 --oneline --decorate
git -C /Users/linzezhang/CodexProject ls-remote origin refs/heads/main
python3 KMFA/fund-weekly-analysis-skill/tools/check_codex_app_automation.py
```

已观察到:

```text
HEAD == origin/main == c69d00805f63f1b982a641a919b43fcbedec86e1
CODEX_AUTOMATION_READY
```

### Skill validators

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 KMFA/fund-weekly-analysis-skill/tools/validate_taskpack.py
```

已观察到:

```text
PASS
daily-routine-check skill validation PASS
PASS
```

### Focused tests

```bash
python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
python3 -m unittest KMFA.tests.test_daily_routine_check -q
```

已观察到:

```text
S19 attendance: 66 tests OK
S20 routine check: 19 tests OK
```

### Source readiness

```bash
python3 KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py --repo-root /Users/linzezhang/CodexProject --timezone Australia/Sydney
```

已观察到:

```text
status=READY
file_count=292
unreadable_count=0
```

### DWS archive preflight

在 DWS archive project cwd:

```bash
dws doctor --format json
/usr/bin/python3 scripts/archive_dingtalk_all_files.py --plan-only --run-source codex_automation --automation-name "每日钉钉DWS归档"
```

已观察到:

```text
DingTalk Doctor: 3 pass, 1 version warning, 0 fail
DWS plan-only: success=true, groups_planned=9
```

版本 warning 是 `dws v1.0.46 -> v1.0.50`，不是当前 blocker。

## 已完成真实发送测试

用户明确授权后，已执行一次张霖泽个人真实测试，未发送生产管理群。

执行命令:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai --work-date 2026-07-10 --notification-targets personal --allow-dws-commands
```

结果:

```text
status=COMPLETED
collection_status=DWS_LIVE_COLLECTION_WRITTEN
notification_status=SENT
target=张霖泽
target_type=personal
channel=dws_open_dingtalk_id_chat
run_id=s19_morning_20260710_103500
work_date=2026-07-10
```

发送正文:

```text
开明考勤提醒｜2026-07-10｜晨报

截止 10:35

本次44人全部考勤正常
```

私有证据路径:

```text
/Users/linzezhang/OneDrive/dingtalk_attendance/202607/s19_morning_20260710_103500.dispatch.json
/Users/linzezhang/OneDrive/dingtalk_attendance/202607/s19_morning_20260710_103500.manifest.json
```

注意: 只能确认 DingTalk send 返回 `SENT`；不能从本地证明手机端已读。

## 关键文件

优先读这些文件，不要先全仓扫描:

```text
KMFA/metadata/automation/bug_log.md
KMFA/metadata/automation/HANDOFF_20260710_kmfa_automation_takeover.md
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
KMFA/daily_routine_check_skill/SKILL.md
KMFA/fund-weekly-analysis-skill/automation/codex_app_automation.contract.toml
KMFA/fund-weekly-analysis-skill/automation/weekly_mon_sat_1100_sydney.prompt.md
KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md
KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md
KMFA/metadata/daily_routine_check/codex_automation/automation_manifest.json
```

本地 automation TOML 只用于 readback，不要手改:

```text
/Users/linzezhang/.codex/automations/kmfa/automation.toml
/Users/linzezhang/.codex/automations/kmfa-3/automation.toml
/Users/linzezhang/.codex/automations/kmfa-4/automation.toml
/Users/linzezhang/.codex/automations/kmfa-5/automation.toml
/Users/linzezhang/.codex/automations/kmfa-dws/automation.toml
```

如果需要改 Codex Desktop Scheduled automation，必须使用官方 `automation_update` 工具，然后 readback 验证 project/cwd、rrule、prompt、status。

## 新线程启动 Prompt

把下面这段直接贴给新线程:

```text
接手 KMFA automation 稳定性维护。先读：
/Users/linzezhang/CodexProject/KMFA/metadata/automation/HANDOFF_20260710_kmfa_automation_takeover.md
/Users/linzezhang/CodexProject/KMFA/metadata/automation/bug_log.md

当前目标不是重新创建 automation，而是保持现有 5 个 automation 正常：
- kmfa
- kmfa-3
- kmfa-4
- kmfa-5
- kmfa-dws

重要边界：
1. /Users/linzezhang/CodexProject 是 KMFA 四个业务 automation 唯一工作区。
2. kmfa-dws 是独立 DWS archive producer，固定在 /Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p。
3. 不要创建 branch、PR、worktree。
4. 不要手改 ~/.codex/automations/*/automation.toml；用 Codex automation_update 工具，并 readback 验证。
5. 不要发送 DingTalk 真实消息，除非我在当前线程明确授权。
6. 不要提交 private runtime、DWS raw、SQLite、token、webhook、resolved IDs、员工考勤明文或报告正文。

当前已验证：
- GitHub main: c69d00805f63f1b982a641a919b43fcbedec86e1
- kmfa-5: CODEX_AUTOMATION_READY
- attendance skill: PASS
- daily routine skill: PASS
- fund source readiness: READY, 292 files, 0 unreadable
- DWS doctor: 3 pass, 1 warning, 0 fail
- 张霖泽 personal-only live test: SENT, run_id s19_morning_20260710_103500

先做只读 readback 和 healthcheck，不要擅自扩大修复范围。
```

## 当前风险和下一步

| 风险 | 状态 | 下一步 |
|---|---|---|
| 下一次 Codex Desktop 到点触发是否稳定 | 未自然等待验证 | 等最近一个 scheduled run 完成后，核对 run 输出和工作区 |
| DWS CLI 版本 warning | 非阻塞 | 后续可单独评估 `dws upgrade`，不要混进 automation 修复 |
| UI 卡片缓存/registry 热目录漂移 | 已清理过，仍需观察 | 如再复发，先检查 `~/.codex/automations` 是否又出现 backup/orphan 目录 |
| 用户侧已读确认 | 本地无法证明 | 让张霖泽确认是否收到测试消息 |

## 当前 worktree 状态

当前 repo 有三个 unrelated untracked 文件，属于 `OpenAIDatabase/session_history` 临时文件，不属于 KMFA 本轮修复，不要触碰:

```text
OpenAIDatabase/session_history/.tmp_backup_paths
OpenAIDatabase/session_history/.tmp_backup_summary
OpenAIDatabase/session_history/.tmp_manifest_rows
```

## 停止条件

新线程遇到以下情况应停止并报告，而不是继续改 prompt:

1. live automation readback 又出现旧 July 5 工作树。
2. `HEAD != origin/main` 且不是本线程造成的变更。
3. healthcheck 不再是 `READY`。
4. DWS doctor 出现 login/network/cache fail。
5. private target config 缺失导致 personal target 不可用。
6. 任何命令准备向 GitHub 提交 raw zip、raw JSONL/GZ、SQLite、secret、resolved ID 或报告正文。
