# PFI 参数变更记录

参数版本：`v0.2.2`

任务名：`PFI v0.2.2 E2E 逻辑优化`

本文件从 Stage 0 开始记录参数、公式、阈值、分类、标签、Interconnection、汇率和 Runtime Diff 规则的变更。每条记录必须说明旧值、新值、原因和影响范围。

## 变更记录

| 时间 | Stage/Phase/Task | 字段 | 旧值 | 新值 | 原因 | 影响范围 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-28 | `S0-P2-T1` | `parameter_version` | `v0.2.1 前端优化` | `v0.2.2` | 锁定本轮为数据库治理和 E2E 逻辑优化。 | 三基文件、Stage 0 baseline、后续参数一致性测试。 |
| 2026-06-28 | `S0-P2-T1` | `task_name` | `OWNER-APPROVED-NEXT-ROADMAP` | `PFI v0.2.2 E2E 逻辑优化` | 用户提供 Stage -> Phase -> Task roadmap，需建立正式任务入口。 | 开发记录、模型参数文件、功能清单、roadmap lock。 |
| 2026-06-28 | `S0-P1-T3` | `uiux_scope` | `v0.2.1 HTML Web Shell` | `v0.2.1 HTML Web Shell 继续作为 UIUX 基线；v0.2.2 Stage 0 不改前端显示` | 用户明确 HTML 模板只是帮助理解，不是要求修改 UIUX。 | Stage 0 合同、baseline report、测试。 |
| 2026-06-28 | `S0-P2-T2` | `parameter_changelog` | `无独立文件` | `PFI/config/parameter_changelog.md` | Roadmap Stage 0 Phase 0.2 要求新增参数变更记录文件。 | 后续所有参数变更必须写入本文件。 |

## 记录规则

每次后续 Stage 修改参数时，必须新增一行，字段如下：

- `时间`：本地日期。
- `Stage/Phase/Task`：例如 `S1-P1-T2`。
- `字段`：参数 key、公式名或规则名。
- `旧值`：变更前的值；首次新增写 `无`。
- `新值`：变更后的值。
- `原因`：中文业务解释。
- `影响范围`：直接影响的页面、报告、测试、指标或数据表。

禁止只改代码或 UI 而不记录参数变更。
