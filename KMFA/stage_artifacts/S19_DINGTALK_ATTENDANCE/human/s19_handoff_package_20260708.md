# S19 DingTalk Attendance Handoff Package

更新时间: 2026-07-08

## 1. 接手目标

让新线程、任意 Codex agent 或新电脑从 GitHub `main` checkout 后，可以直接接手 `KMFA/kmfa-dingtalk-attendance-skill` 与晨晚 Codex automation，不丢失规则、运行命令、数据边界、验证方式和当前 blocker。

推荐新线程启动 prompt：

```text
继续维护 /Users/linzezhang/CodexProject/KMFA 的 kmfa-dingtalk-attendance-skill 与晨晚 Codex automation；保持 GitHub main 同步、DWS fail-closed、敏感数据私有、北京时间运行；当前调度晨报 10:35、晚报 20:05；通知只展示当天命中异常，缺卡/未打卡/旷工/迟到/早退进入今日异常/无考勤，月累计只做注释，空板块不渲染，无异常且取数完整输出“本次 N 人全部考勤正常”；删除待审批/待补卡/待核查用户可见板块；休息提醒从自然月第 23 个有效考勤日开始，丁春法/李永占只排除出需要休息；先读 SKILL.md、KMFA/HANDOFF.md、此 handoff package，验证本机 automation-3/4 和 origin/main，再执行任何 DWS/live 发送。
```

## 2. 第一批必读文件

从 repo 根目录 `/Users/linzezhang/CodexProject` 读取：

```text
KMFA/kmfa-dingtalk-attendance-skill/SKILL.md
KMFA/kmfa-dingtalk-attendance-skill/references/runbook.md
KMFA/kmfa-dingtalk-attendance-skill/references/configuration.md
KMFA/kmfa-dingtalk-attendance-skill/references/operating_contract.md
KMFA/kmfa-dingtalk-attendance-skill/references/source_of_truth_contract.md
KMFA/HANDOFF.md
KMFA/metadata/dingtalk_attendance/README.md
KMFA/stage_artifacts/S19_DINGTALK_ATTENDANCE/human/s19_handoff_package_20260708.md
```

若 agent 无法自动解析 repo-scoped skill `$kmfa-dingtalk-attendance-skill`，直接读取 `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` 并按同一规则执行。

## 3. 当前 Git 基线

- 仓库: `LinzeColin/CodexProject`
- 本机 canonical checkout: `/Users/linzezhang/CodexProject`
- 分支策略: 直接在 `main` 工作；不得自行创建 branch、PR、issue 或 worktree。
- S19 规则修复基线提交: `dff96f8ae4c9867f09135c0d6d7d93c6540d2eeb`
- 本交接包提交前的 `main` 基线: `bd5fc36cea66ce6d728914b254da447a163ef253`
- 本交接包提交后，接手线程应重新验证 `HEAD == origin/main`。

注意：当前工作树可能存在非 S19 的 fund-weekly 或 KMFA 全局文档未归属修改。接手 S19 时只 stage/commit S19 范围内文件，不能回滚、覆盖或顺手提交不相关改动。

## 4. Automation 真相

本机 Codex automation：

| Local id | 名称 | 北京时间 | 执行 | 关键目录 |
| --- | --- | --- | --- | --- |
| `automation-3` | `每日早晚钉钉考勤检查｜晨报` | 10:35 | local, `gpt-5.3-codex-spark`, `xhigh` | `/Users/linzezhang/CodexProject` |
| `automation-4` | `每日早晚钉钉考勤检查｜晚报` | 20:05 | local, `gpt-5.3-codex-spark`, `xhigh` | `/Users/linzezhang/CodexProject` |

两张 automation 卡的 cwd list 应包含：

```text
/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p
/Users/linzezhang/CodexProject
```

运行 KMFA git、skill、tests、scripts 时必须先切到 `/Users/linzezhang/CodexProject`。DWS 归档项目只用于上游输出和诊断可见，不允许修改上游归档输出。

GitHub portable prompt mirror：

```text
KMFA/kmfa-dingtalk-attendance-skill/automation/morning_prompt.md
KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md
KMFA/metadata/dingtalk_attendance/codex_automation/morning_1035.prompt.md
KMFA/metadata/dingtalk_attendance/codex_automation/evening_2005.prompt.md
KMFA/kmfa-dingtalk-attendance-skill/automation/codex_automation_manifest.md
```

任何 skill、automation prompt、schedule、cwd、model、reasoning、validator 或相关配置变更，都必须验证、commit、push 到 GitHub `main` 后才能声称可移交。

## 5. 通知规则清单

- 所有 business date、run slot、month gate 使用 `Asia/Shanghai`。
- 晨报固定 10:35；晚报固定 20:05。
- `今日异常 / 无考勤` 只由当天 `work_date` 命中的状态驱动。
- `缺卡`、`未打卡`、`旷工`、`迟到`、`早退` 都计入 `今日异常 / 无考勤`。
- 当前自然月累计次数只能作为今天命中人员的注释，不能反向制造今天异常。
- 不能把当月自然月以来历史累计名单渲染成今天未打卡或今天异常。
- `待审批 / 待补卡 / 待核查` 不作为用户可见板块渲染；如有后台状态，只能留在 manifest、receipt、automation JSON 或私有机器状态。
- 空板块不显示标题，也不显示 `无`，必须完全不渲染。
- 当天无异常且取数完整，输出 `本次 N 人全部考勤正常`。
- 后台开发诊断，例如 DWS record/summary 失败、权限核查、gateway timeout，不进入用户面向通知、管理报告或 HR 报告正文。
- 每个状态板块人数小于等于 10 时展示全量；超过 10 时展示总数加 Top 10。

## 6. 人员与休息规则

- 已知无 record 人员：张霖泽、林全意。只豁免他们自己的 no-record 条件，不做全局隐藏。
- `NOTIFICATION_HIDDEN_NAMES` 必须保持空，除非用户明确授权展示层隐藏。
- 休息提醒从自然月第 23 个有效考勤日开始。
- 有效考勤日定义：同一个自然日同时存在上班与下班打卡。
- 丁春法、李永占只从 `需要休息` 和私有 ledger `rest_required_snapshots` 中排除；迟到、早退、缺卡、旷工、未打卡、其他统计仍照常计入。

## 7. 数据与隐私边界

允许进入 Git：

```text
代码
测试
public-safe manifests
public-safe prompts
路径和聚合验证证据
schema、policy、templates
```

禁止进入 Git：

```text
.env.local
webhook URL、signing key、app secret、token、password
DWS resolved IDs、open_dingtalk_id、group conversation id
SQLite
raw JSON/JSONL/GZ
真实员工考勤明文
管理/HR 报告正文
OneDrive 私有 raw archive
```

公开 `KMFA/metadata` 是 metadata/config 层。真实 DingTalk raw payload、dispatch receipt、report body 和 SQLite 留在 ignored private runtime 或 OneDrive：

```text
KMFA/metadata/dingtalk_attendance/private_runtime/
/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/
```

## 8. 只读/离线验证清单

从 `/Users/linzezhang/CodexProject` 执行：

```bash
git status --short --branch
git fetch origin main
git rev-parse HEAD origin/main
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py --pathspec KMFA/kmfa-dingtalk-attendance-skill KMFA/metadata/dingtalk_attendance KMFA/tools/dingtalk_attendance KMFA/tests/test_dingtalk_attendance.py KMFA/stage_artifacts/S19_DINGTALK_ATTENDANCE
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/check_s19_dingtalk_attendance.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
TZ=Asia/Shanghai KMFA_RUN_SLOT=morning KMFA/kmfa-dingtalk-attendance-skill/scripts/preflight.sh
TZ=Asia/Shanghai KMFA_RUN_SLOT=morning KMFA/kmfa-dingtalk-attendance-skill/scripts/inspect_runtime.sh
TZ=Asia/Shanghai KMFA_RUN_SLOT=morning KMFA/kmfa-dingtalk-attendance-skill/scripts/validate_offline.sh
TZ=Asia/Shanghai KMFA_RUN_SLOT=morning python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot morning --print-json
TZ=Asia/Shanghai KMFA_RUN_SLOT=evening python3 KMFA/kmfa-dingtalk-attendance-skill/scripts/month_gate.py --run-slot evening --print-json
git diff --check
```

`preflight.sh` 在工作树存在未归属改动时可能给出 warning；这是 fail-closed 运行前需要解释的状态，不代表可忽略。

## 9. Live DWS/发送清单

没有用户在当前线程明确授权时，不运行 DWS live 命令，不发送钉钉消息。

运行前守门：

```bash
pgrep -af 'run_attendance|dingtalk_attendance|(^|/)dws( |$)|open-dev\.dingtalk|personalAuthorization'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
```

Live DWS 需要：

```text
KMFA_S19_ALLOW_DWS_COMMANDS=1
KMFA_S19_DWS_BROWSER_POLICY_PATH 可用，或默认 ~/.dws/pat_policy.json 可用
browser policy: default.openBrowser=false
DWS auth 可用
无 stale dws/run_attendance 进程
```

生产晨报：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai --allow-dws-commands
```

生产晚报：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai --allow-dws-commands
```

指定日期 owner-only 测试，必须只发个人，不触达生产管理群：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai --work-date YYYY-MM-DD --notification-targets personal --allow-dws-commands
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai --work-date YYYY-MM-DD --notification-targets personal --allow-dws-commands
```

## 10. 最近验证摘要

- S19 规则修复提交前，focused unit test、S19 contract validator、skill package validator、sensitive scan、config healthcheck、offline validator 已通过。
- 2026-07-06 晨报 owner-only live 测试：个人目标发送成功；dispatch 仅含 personal target；用户正文没有 `待审批 / 待补卡 / 待核查` 板块，也没有后台 DWS/record/summary 诊断；今日异常由当天命中驱动，月累计只作为注释。
- 2026-07-06 晚报 owner-only live 测试：DWS department discovery gateway timeout/code 6 阻断；未生成报告，未发送个人或群；recovery event 已记录并 finalize failed。
- S19 规则修复提交为 `dff96f8ae4c9867f09135c0d6d7d93c6540d2eeb`；本交接包提交前的 `main` 基线为 `bd5fc36cea66ce6d728914b254da447a163ef253`。接手线程必须以最新 `HEAD == origin/main` 为准。

不要把上面 live 测试中的真实员工名单、报告正文、raw hash 或 private dispatch 明细复制到 GitHub。

## 11. 已知 blocker 和处理原则

- DWS gateway timeout/code 6 属于外部 live 取数阻断；必须 fail closed，不允许用历史累计、样例数据或局部缓存补成当天报告。
- 如果 DWS record/summary 或 department discovery 部分失败，后台错误只能进入 manifest/receipt/automation 状态；用户面向报告不显示开发诊断。
- 如果当天异常为空但取数不完整，不能输出“全部考勤正常”；必须保留 partial/failure 状态。
- 如果工作树存在非 S19 改动，先隔离 stage 范围；不要回滚用户或其他 agent 的改动。
- 如果 automation 本机卡片、repo prompt mirror、metadata prompt mirror 不一致，先同步并 commit/push，再声称可移交。

## 12. 接手验收标准

新线程接手后，最小验收为：

1. `git rev-parse HEAD origin/main` 两行一致。
2. 本机 `automation-3` 是 10:35，北京时间，prompt 使用 `$kmfa-dingtalk-attendance-skill`。
3. 本机 `automation-4` 是 20:05，北京时间，prompt 使用 `$kmfa-dingtalk-attendance-skill`。
4. repo prompt mirror 与本机 automation 的时间、cwd、hard boundaries 不冲突。
5. `validate_skill_package.py` 通过。
6. `validate_no_sensitive_git.py` 对 S19 范围通过。
7. `check_s19_dingtalk_attendance.py` 通过。
8. `python3 -m unittest KMFA.tests.test_dingtalk_attendance -q` 通过。
9. 未把真实考勤明文、raw、SQLite、secret、resolved ID、报告正文提交到 Git。
10. 若执行 live run，有当前线程授权，并明确说明发送目标是 `all` 还是 `personal`。
