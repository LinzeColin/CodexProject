# Memory Atlas Review / Summary / Iteration 工作流验收

适用版本：Memory Atlas v1.1.6 Stage 4 Phase 2

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS、不读取 raw/private、不写长期记忆、不执行 agent apply、不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 `review_summary_iteration_workflow` 的复盘问题、总结输出、iteration backlog、proposal 判断和安全边界。通过本验收只表示 Stage 4 Phase 2 的合同完整，不表示运行时复盘、浏览器截图、Data Map 2.0 或 Stage 4 整体复审已完成。

## 2. 八个问题检查

每次 review summary 必须回答：

| 问题 | 最低通过标准 | 失败示例 |
|---|---|---|
| 本期主导主题是什么 | 显示 `dominant_topics` 与证据 | 只写“主题很多” |
| 哪些主题增强 | 显示 `strengthening_topics`、趋势和 evidence_refs | 无趋势解释 |
| 哪些主题衰退 | 显示 `declining_topics` 和可能原因 | 忽略衰退 |
| 哪些新机会出现 | 显示 `new_opportunities`、why_now、next step | 只列关键词 |
| 哪些低价值循环出现 | 显示 `low_value_loops`、loop_cost、处理建议 | 不指出循环成本 |
| 哪些决策变化 | 显示 `decision_changes`、old/new position 和 reason | 无法追踪变化 |
| 下一步动作是什么 | 显示 `next_actions`、priority、due_window | 没有行动 |
| 是否需要生成 proposal | 显示 `proposal_candidate`、target_type、field、reason | 无法调整或回滚 |

## 3. 区域检查

必须覆盖：

- `review_period_selector`
- `theme_change_panel`
- `opportunity_panel`
- `low_value_loop_panel`
- `decision_change_panel`
- `next_action_panel`
- `proposal_decision_panel`
- `iteration_backlog`

缺少任一核心区域即失败。

## 4. Output schema 检查

review output 必须包含：

- `review_id`
- `review_schema_version`
- `time_window`
- `source_scope`
- `dominant_topics`
- `strengthening_topics`
- `declining_topics`
- `new_opportunities`
- `low_value_loops`
- `decision_changes`
- `next_actions`
- `proposal_candidate`
- `evidence_refs`
- `confidence`
- `iteration`

`iteration` 至少包含 `iteration_items`、`acceptance_hint`、`blocked_reason` 和 `review_again_at`。

## 5. Proposal 判断检查

当 `proposal_candidate = true` 时，必须显示：

1. target_type。
2. field。
3. reason。
4. rollback_hint。
5. requires_conflict_check。
6. requires_agent_or_human_apply。

缺少任一项即失败。proposal 判断不能直接写 active memory。

## 6. 响应式截图入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 八个问题、主题变化、下一步动作和 proposal 判断可见或清晰分区 |
| Tablet 768x1024 | panels 可折叠但八个答案和 next_actions 不丢失 |
| Mobile 390x844 | question label、summary、next_actions、proposal_candidate 不溢出 |

本 phase 只定义截图入口，不启动浏览器。

## 7. 安全检查

必须满足：

1. 不读取 raw/private/cookie/session/secret。
2. 不显示 raw conversation text。
3. 不显示本地绝对私有路径。
4. 不显示 record hash 或 active memory row 全量拷贝。
5. 不直接写 proposal queue 或 active memory。
6. `proposal_candidate` 只能进入 proposal-only handoff。
7. 不自动上传 GitHub main。

## 8. 安全失败条件

任一情况出现即失败：

1. 复盘结论需要 raw/private/cookie/session/secret 才能解释。
2. 八个问题任意一个没有回答。
3. 只有总结，没有 next_actions。
4. 只有行动，没有 evidence_refs 或 confidence。
5. 需要修改重要性/优先级却没有 proposal_candidate 判断。
6. 合同把 Data Map 2.0 或 Stage 4 整体复审冒充为本 phase 已完成。
7. 合同允许前端直接修改 active memory。
8. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 9. 通过条件

Stage 4 Phase 2 通过时必须有：

1. `docs/product/review_summary_iteration_workflow_contract.md`。
2. `docs/acceptance/review_summary_iteration_workflow_acceptance.md`。
3. `validate:v1.1.6-stage4-phase2`。
4. 三文件和模型参数记录中登记 `MA-V116-S4P02`。
5. Changelog 明确 No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。

## 10. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时或数据回滚。
