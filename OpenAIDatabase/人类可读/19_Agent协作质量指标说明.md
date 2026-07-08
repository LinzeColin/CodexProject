# Agent 协作质量指标说明

## 当前结论

任务 ID：`MA-V12-S08P1`

验收 ID：`ACC-MA-V12-S08P1`

当前状态：`phase_s08_p1_collaboration_metrics_completed_pending_s08_p2`

S08 P1 已生成 Codex/Agent 协作质量报告：

`data/derived/agent_collaboration/agent_collaboration_quality_report.json`

下一步只允许进入 S08 P2。

## 这份报告回答什么

- 人负责什么：目标、范围、授权、是否 apply、业务优先级和高风险取舍。
- Agent 负责什么：在明确边界内执行可验证任务、保留证据、运行 validator、说明回滚路径。
- 返工来自哪里：repeated rework、decision debt、scope creep、evidence gap 和 action half-life。
- 哪些任务适合继续交给 Codex/agent：有清晰下一步、可测试输出、可回滚边界和足够证据的任务。
- 哪些必须人工判断：授权 apply、修改 active config、解释冲突证据、业务优先级和范围扩张。

## 指标

- `planning_clarity`：规划清晰度。
- `execution_clarity`：执行清晰度。
- `review_burden`：复审负担健康度，高分表示复审负担较低。
- `rework_count`：返工控制健康度，高分表示返工压力较可控。
- `scope_clarity`：范围清晰度。
- `testability`：可测试性。
- `rollbackability`：可回滚性。

这些分数是内部 proxy，不是对人或 agent 的人格判断，也不是任务价值的绝对排序。

## 边界

S08 P1 不创建多 agent 系统，不实现复杂 Delegation Contract UI，不执行 proposal apply，
不定义授权边界，不生成 stage flight recorder，不修改 raw。

授权边界进入 S08 P2。stage flight recorder 进入 S08 P3。

No GitHub main upload in this phase.
