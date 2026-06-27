# PFI v0.2.2 Roadmap Lock

版本：`v0.2.2 数据库治理 / E2E 逻辑优化`

追求目标：

```text
建立一个以 CNY 为主口径、以统一账本为事实层、以 Interconnection 为核心关联机制、以参数文件为模型治理中心、以中文可视化为人工验收入口的个人金融 E2E 逻辑系统。
```

## Stage / Milestone 顺序

| Milestone | 名称 | 本轮状态 | 说明 |
| --- | --- | --- | --- |
| 0 | 现状盘点与任务锁定 | 本轮执行 | 只做 baseline，不提前实现后续功能。 |
| 1 | 模型参数文件重构 | 待 owner 开启 | 后续新增 YAML、参数 changelog 和一致性测试。 |
| 2 | CNY 与汇率有效日逻辑 | 待 owner 开启 | 统一 CNY 主口径和 06:00 有效汇率日。 |
| 3 | Economic Event 与 Interconnection | 待 owner 开启 | 新增 economic_event_id、interconnection_group_id、no-double-count。 |
| 4 | 消费分类与标签系统 | 待 owner 开启 | 12 大类、50 中类、标签持久化。 |
| 5 | 消费、投资、现金流模型升级 | 待 owner 开启 | 公式、参数、阈值和现金流 7 窗口。 |
| 6 | Runtime Diff 与 Agent Trigger | 待 owner 开启 | dependency hash、impacted metrics、Codex Review Ticket。 |
| 7 | HTML / UIUX 可视化审查页 | 待 owner 开启 | 未来新增审查页；不影响本轮 Stage 0。 |
| 8 | 2 轮 x 6 Agent 自检和最终交付 | 待 owner 开启 | 所有测试通过后生成正式复审报告。 |

## Stage 0 Acceptance Criteria

- 已列出现有参数与硬编码阈值。
- 已列出现有消费、投资、现金流、建议模块的计算口径。
- 已标记哪些逻辑与 v0.2.2 要求冲突。
- 已确认不会破坏已有 v0.2 Stage 6 基础。
- 已锁定 HTML 模板只是未来逻辑审查参考，不是本轮 UI 修改要求。

## Stage 0 Stop Condition

- 无法定位现有模型参数文件。
- 无法定位现有前端入口。
- 无法判断现有测试框架。
- Stage 0 改动触碰 v0.2.1 正式前端显示。

当前检查结论：以上停止条件均未触发。

## Stage 0 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

