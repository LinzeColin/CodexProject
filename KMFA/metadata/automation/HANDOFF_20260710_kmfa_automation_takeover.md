# KMFA Automation Takeover Handoff

更新时间: 2026-07-11

## 2026-07-11 `dws-auth-keepalive-2` 自动刷新修复

原始需求是让可刷新的 DWS access token 由 automation 自动续期。旧 live
prompt 没有兑现该要求：它把 `dws auth login --yes --no-browser` 当成“非交互
刷新”，但该命令仍会启动完整 OAuth 授权并等待人工回调。更隐蔽的问题是
`dws auth status --format json` 在刷新失败时仍可能 exit 0、返回
`authenticated=true` 和 `refresh_token_valid=true`，却不返回
`token_valid=true`；旧 prompt 没有对此 fail closed。

当前修复：

- 新增确定性入口 `KMFA/tools/automation/dws_auth_keepalive.py`，自动续期只调用
  DWS CLI 官方 refresh 路径 `dws auth status --format json`，最多 3 次重试。
- 成功硬门固定为 `success=true`、`authenticated=true`、
  `token_valid=true`、`refresh_token_valid=true`、私有固定 profile 匹配、
  access/refresh expiry 均可解析且晚于当前时间，并且 doctor 无 fail；任何单一
  exit code 或布尔值均不能独立判定成功。
- 预期组织 profile 已固定到 active automation 目录下的 machine-private 0600
  文件；status 与 doctor 都显式使用它，禁止依赖可变 `currentProfile`。
- DWS HTTP timeout 固定 20 秒，外层 subprocess timeout 固定 25 秒，给 CLI
  清理/原子 token 写入保留 5 秒 grace，避免在内部默认 30 秒超时前杀进程。
- 删除 automation 的自动 login fallback。失败时只给出一次性
  `dws auth login --device` 下一步，不启动浏览器、loopback listener 或 OAuth。
- doctor 参数修正为 profile-pinned `dws doctor --json --timeout 20`，任何
  fail/unavailable/malformed 结果非零阻断。
- wrapper 确定性管理 24 小时/最后 4 小时提醒去重，并以原子 0600 文件维护最多
  24 条脱敏运行记录；active ledger 不再含 corp/user identity，旧含标识记录仅保留
  在同目录 0600 private legacy 文件中。
- live automation 已按 Git-tracked prompt 更新并只读回读；RRULE 保持
  `RRULE:FREQ=DAILY;BYHOUR=0,4,8,12,16,20;BYMINUTE=20`，无 timezone 字段。
- DWS CLI 已通过官方升级入口从 v1.0.46 升至 v1.0.51；升级不被当作 token
  修复证据。

若 machine-private profile 文件丢失，scheduled run 必须停在
`pin_expected_profile`，不得自行选择组织。仅在 owner 已确认当前 DWS profile 就是
目标组织后，人工执行一次：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /Users/linzezhang/CodexProject/KMFA/tools/automation/dws_auth_keepalive.py --bootstrap-current-profile
```

该命令只读取并固定当前本机 profile，不执行 `auth status`、refresh 或 login。
wrapper 的 `notification_required` 仅表示 Scheduled final/inbox 应通知；在没有
delivery 证据前不得写成外部提醒已送达。

当前真实运行仍 fail closed：现有 access token 已过期，本地 refresh token
元数据尚在有效期，但服务端 exchange 连续 3 次未换得新 access token，wrapper
返回 `auto_refresh_failed`/exit 3。需要 owner 完成一次 `dws auth login --device`
重新取得 token pair；此后还必须等待 access token 自然过期，并由一次自然定时
运行观察到 `refreshed=true`、`token_valid=true` 和新的 expiry，才能关闭长期稳定性
验收门。不得在该门完成前声称自动刷新已恢复生产可用。

## 2026-07-11 `kmfa-4` ZIP-only 与缓存 I/O 修复

用户已澄清：S20 `KMFA｜钉钉工作检查` 的上游输出只可能是 ZIP，目标必须固定为：

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

这不是 “ZIP 优先、目录回退”，而是 **ZIP-only**。同级 `DWS_Outputs/`
文件夹不存在是正常生产状态，不得要求、创建、解压或 materialize 该目录。

### 根因与磁盘证据

- 旧迁移同时保留 `input_zip_default` 和 `input_root_default`，healthcheck 仍逐群
  probe 文件夹，reader/main/prompt 仍保留 folder fallback，导致 agent 可以继续把
  不存在的文件夹误判为启用条件。
- 当前 canonical ZIP 为 `568878497` bytes，实际占盘 `555548 KiB`，约 543 MiB，
  已本地 materialize；`/Users/linzezhang/onedrive/DWS_Outputs.zip` 是同 inode
  别名，不是重复副本。
- OneDrive、别名路径和 Downloads 下均未发现 `DWS_Outputs/` 文件夹；未发现
  routine-check 解压副本。private runtime 约 208 KiB，旧 `/private/tmp` 源码包
  约 156 KiB，均不是主要缓存来源。
- ZIP 约有 1006 entries；S20 实际需要的四个 CSV 在本次只读快照中合计仅
  `267878` bytes 未压缩、`65374` bytes 压缩。主要磁盘成本来自 OneDrive 对整包
  ZIP 的 hydration，而不是目标 CSV 或 SQLite 日志。

### 当前修复状态

- 当前工作树已把 reader、healthcheck 和 CLI 改为 explicit ZIP-only；非 `.zip`
  输入 fail closed，不再派生 sibling ZIP 或读取目录。
- source inspection 复用同一次每群 message snapshot，避免旧实现对每群
  `chat_records.csv` 重复读取两次。
- cleanup 已收紧为显式 `--cleanup --apply` 维护门禁；正式 scheduled command
  已删除这两个参数。官方 automation update 后，live prompt SHA-256 与 canonical prompt
  一致，5 个 automation contract 均无漂移；下一次自然触发仍待确认，因此不得声称
  natural run 已验收。
- 不得自动 evict/逐出 ZIP；否则下一次检查会重新下载约 543 MiB。数量级降低
  hydration 需要上游另产目标专用小 ZIP 或 remote-range reader，属于需单独授权
  的上游范围扩展。

已确认 live prompt 只有 ZIP 目标、没有 folder fallback 或 scheduled cleanup flags；
healthcheck 不输出 direct-folder readiness；手工 cleanup 在 ZIP/业务加载前早退；25 项 routine tests、skill validator、
8 项 automation contract tests、真实 ZIP healthcheck 与两个窗口 dry-run 通过。
接手只需继续确认下一次自然触发只读 ZIP member、没有创建文件夹、没有每 run VACUUM。

## 2026-07-10 `kmfa-3` 固定 20:00 稳定性修复

用户明确要求所有 automation 的 scheduler 不设置时区，并已亲自把晚报
`kmfa-3` 改为本机墙钟 20:00。以后 `kmfa-3` 永久保持这个时间：不得按北京
时间、UTC offset 或夏令时换算。当前 live rule 是：

```text
RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA
```

禁止 `DTSTART`、`TZID`、显式 scheduler timezone 和多 RRULE。runner 内部的
`Asia/Shanghai` 只用于业务日期，不能改变 scheduler 的 20:00。
live checker 同时锁定晚报 prompt 的规范化 SHA-256 和 canonical project id；
以后即使时间没变，只要 prompt 回旧版或重新绑错项目，也必须判 mismatch。
DWS summary 查询使用实际运行瞬间对应的北京时间，不能把本机 scheduler 的
`20:00` 字面量冒充成北京 20:00；契约明确 `fixed_local_wall_clock=true`、
`offset_conversion_allowed=false`。

新的统一 schedule contract 与 live checker：

```text
KMFA/metadata/automation/codex_app_schedules.contract.toml
KMFA/tools/automation/check_kmfa_automation_schedules.py
KMFA/tests/test_automation_schedule_contract.py
```

验收命令：

```bash
python3 KMFA/tools/automation/check_kmfa_automation_schedules.py
python3 -m unittest KMFA.tests.test_automation_schedule_contract -q
```

2026-07-10 automation-created task 已证明 canonical cwd → 真实 S19 DWS runner
→ 44/44 record、44/44 summary、0 command failure → OneDrive 私有归档 → 两个
通知目标均 `SENT`。但该次在 21:18 AEST 启动，属于保存/补触发证据，不是
自然 20:00 调度证据。

仍未完成的唯一 S19 调度验收：等待下一次本机墙钟 20:00 自然触发，确认
只产生一个新 task、cwd 为 `/Users/linzezhang/CodexProject`、真实取数完成、
私有归档成功且通知目标发送成功。

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
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | `/Users/linzezhang/CodexProject` | S19 晚报，本机墙钟固定 20:00；scheduler 无时区 |
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
