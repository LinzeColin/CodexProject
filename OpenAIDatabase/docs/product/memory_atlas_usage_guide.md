# Memory Atlas Usage Guide

Guide ID: `memory_atlas_usage_guide`

Current package: `v1.1.7 Stage 0 Phase 0.2`

Status: `phase_0_2_usage_help_completed_pending_stage0_review`

## 3-Minute Path

1. `0-1 分钟`：打开记忆总览，先看 Memory Weather、主导主题、风险、机会和近 30 天变化。
2. `1-2 分钟`：点击建议动作、星体或时间事件，同步 Inspector，检查原因、层级、主题、时间和证据。
3. `2-3 分钟`：如果重要性、优先级或结论不准，只生成 proposal JSON；再进入搜索与复盘确认下一步动作，必要时导出或回滚 proposal。

## Reading Modes

- `Presentation`：快速判断方向，优先看全局状态、趋势、机会和风险。
- `Analysis`：展开公式、证据、邻域、性能和 Inspector 上下文，用于核对为什么会这样。

## Empty And Error States

| Situation | Meaning | Next step |
|---|---|---|
| Empty Atlas | 没有读取到可视化用的低敏快照。 | 先生成或导入 Memory Atlas 快照。 |
| No filtered results | 当前筛选条件把数据切片清空。 | 重置筛选，或减少主题、层级、分类、搜索词限制。 |
| WebGL unavailable | 当前浏览器或显卡环境不能启动 Three.js 渲染器。 | 切换 Legacy，或用搜索、复盘、Inspector 查看证据。 |
| Proposal not writable | 写回策略没有满足 proposal-only 安全条件。 | 检查 `source_contract.writeback_policy`，不要直接写长期记忆。 |

## Safety Boundary

Memory Atlas 前端只用于解释、筛选、复盘和生成 proposal。它不得直接写入长期记忆；任何写入必须由受控代理或人工重新读库、检查冲突、生成版本历史并保留回滚路径。
