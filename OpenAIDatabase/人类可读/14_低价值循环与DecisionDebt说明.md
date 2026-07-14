# 低价值循环与 Decision Debt 说明

## 当前结论

S06 P2 已完成。任务 ID 为 `MA-V12-S06P2`，验收 ID 为 `ACC-MA-V12-S06P2`，
状态为 `phase_s06_p2_low_value_loops_completed_pending_s06_p3`。

`scripts/build_memory_atlas_low_value_loops.py` 从
`data/derived/behavior_intelligence/events.json` 和
`data/derived/behavior_intelligence/clusters.json` 生成
`data/derived/behavior_intelligence/low_value_loops.json`。该文件服务于后续机会发现、
ROI 和协作质量复盘，但本阶段只实现低价值循环候选、Decision Debt Ledger 和
Action Half-Life。

## 低价值循环是什么

这里的低价值循环是工作流复盘里的候选模式，不是心理诊断，也不是对个人能力或状态的判断。
每个候选都必须有 `evidence_refs`，并且只描述可观察的工作流信号。

当前支持四类候选：

- `repeated_rework`：重复返工。
- `discussion_without_landing`：反复讨论未落地。
- `over_optimization`：当前价值不足以支撑的过度优化。
- `scope_creep`：目标范围持续扩张。

## Decision Debt Ledger

Decision Debt Ledger 用来记录没有及时收口的决策债。每条记录都绑定一个
low-value loop，并提供一个建议收口问题，例如是否需要定义完成标准、owner、交付件、
质量上限或后续 backlog。

它的用途是减少重复讨论和反复返工，不是制造新的任务压力。

## Action Half-Life

Action Half-Life 表示一个候选循环在多少天内没有形成明确交付件、owner 或停止条件时，
行动价值会开始快速衰减。这个数值用于帮助排序复盘，不代表必须立刻执行。

## 证据边界

低价值循环、Decision Debt Ledger 和 Action Half-Life 均来自已有 event 与 cluster
的证据引用。没有证据的项目不应进入输出。S06 P2 不生成 S06 P3 opportunity cards，
不修改 raw，不上传 GitHub main。

下一步只允许进入 S06 P3。
