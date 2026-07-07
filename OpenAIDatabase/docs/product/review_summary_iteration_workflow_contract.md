# Memory Atlas Review / Summary / Iteration 工作流合同

适用版本：Memory Atlas v1.1.6 Stage 4 Phase 2

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、Search 2.0 runtime、Data Map 2.0、写回逻辑、agent apply 或长期记忆。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 目标

Stage 4 Phase 2 定义 `review_summary_iteration_workflow`。复盘、总结与迭代不应只是摘要卡片，而必须回答用户能直接用来判断和行动的问题，并能把不确定判断转入 proposal-only 流程。

本 phase 只定义工作流区域、八个复盘问题、输出 schema、iteration backlog、proposal 判断、安全边界和验收，不实现 React runtime、不改 CSS、不读取 raw/private、不写 active memory、不进入 Data Map 2.0、不执行 Stage 4 整体复审。

## 2. 工作流区域

后续实现必须至少包含：

| region | 目的 | 最低可见内容 |
|---|---|---|
| `review_period_selector` | 选择复盘周期和范围 | time window、source scope、topic scope、confidence threshold |
| `theme_change_panel` | 回答主题增强/衰退 | dominant_topics、strengthening_topics、declining_topics、evidence_refs |
| `opportunity_panel` | 识别新机会 | new_opportunities、why_now、expected_roi、first_next_step |
| `low_value_loop_panel` | 暴露低价值循环 | low_value_loops、loop_cost、suggested_stop_or_delegate |
| `decision_change_panel` | 追踪决策变化 | decision_changes、old_position、new_position、reason、evidence_refs |
| `next_action_panel` | 汇总下一步动作 | next_actions、owner_mode、priority、due_window |
| `proposal_decision_panel` | 判断是否需要 proposal | proposal_candidate、target_type、field、reason、rollback_hint |
| `iteration_backlog` | 保存下一轮迭代入口 | iteration_items、acceptance_hint、blocked_reason、review_again_at |

## 3. 必须回答的八个问题

每次 review summary 必须显式回答：

1. 本期主导主题是什么。
2. 哪些主题增强。
3. 哪些主题衰退。
4. 哪些新机会出现。
5. 哪些低价值循环出现。
6. 哪些决策变化。
7. 下一步动作是什么。
8. 是否需要生成 proposal。

不能只输出“整体良好”“继续观察”这类不可执行总结。

## 4. Review output schema

每个 review summary 至少包含：

```json
{
  "review_id": "string",
  "review_schema_version": "memory_atlas_review_summary.v1",
  "time_window": "string",
  "source_scope": "redacted-source-scope",
  "dominant_topics": [],
  "strengthening_topics": [],
  "declining_topics": [],
  "new_opportunities": [],
  "low_value_loops": [],
  "decision_changes": [],
  "next_actions": [],
  "proposal_candidate": false,
  "evidence_refs": ["redacted-evidence-id"],
  "confidence": "low|medium|high",
  "iteration": {
    "iteration_items": [],
    "acceptance_hint": "string",
    "blocked_reason": null,
    "review_again_at": "ISO-8601 or null"
  }
}
```

`evidence_refs` 只能指向 redacted evidence id。不得保存 raw/private/cookie/session/secret、本地绝对私有路径、record hash 或 active memory row 全量拷贝。

## 5. Iteration 规则

`iteration_backlog` 必须把复盘结论变成下一轮可执行入口：

1. 每个 `iteration_item` 必须有 `title`、`why_it_matters`、`next_step`、`acceptance_hint` 和 `priority`。
2. 如果证据不足，必须写 `blocked_reason`，不能伪造确定性。
3. 如果需要调整 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 或 confidence_note，必须通过 Stage 3 proposal-only 工作区。
4. 如果只是需要继续观察，必须给出 `review_again_at` 或明确的触发条件。

## 6. Proposal handoff

`proposal_candidate = true` 只表示建议生成 proposal，不表示已经写入 proposal queue 或 active memory。后续必须沿用 Stage 3 边界：

- no direct active memory write。
- requires_conflict_check。
- requires_agent_or_human_apply。
- rollback_hint required。

## 7. 与 Search 2.0 的关系

Review / Summary / Iteration 可以从 Search 2.0 结果进入，但本 phase 不实现 Search 2.0 runtime。Search 2.0 提供 query context、matched_reason 和 result refs；本工作流负责把这些证据汇总成复盘结论和 iteration items。

## 8. 安全边界

工作流只能显示 redacted summary、聚合结论和 evidence_refs。禁止：

- 读取 raw/private/cookie/session/secret。
- 显示 raw conversation text。
- 显示本地绝对私有路径。
- 显示 record hash 或 active memory row 全量拷贝。
- 前端直接写长期记忆或 proposal queue。
- 自动上传 GitHub main。

## 9. 非目标

本 phase 不覆盖：

- React/CSS runtime UI。
- 浏览器截图和 Playwright 验收。
- Search 2.0 runtime。
- Data Map 2.0。
- agent apply。
- active memory 写回。
- Stage 4 整体复审。
- Stage 5 work。
- GitHub main upload。

## 10. 验收

Stage 4 Phase 2 通过条件：

1. 合同覆盖 `review_summary_iteration_workflow`、八个复盘问题和八个输出类别。
2. 合同覆盖 review_period_selector、theme_change_panel、opportunity_panel、low_value_loop_panel、decision_change_panel、next_action_panel、proposal_decision_panel 和 iteration_backlog。
3. 合同覆盖 dominant_topics、strengthening_topics、declining_topics、new_opportunities、low_value_loops、decision_changes、next_actions、proposal_candidate、evidence_refs、confidence 和 iteration。
4. 合同明确 proposal-only handoff、no raw/private data read、no direct writeback、no GitHub main upload。
5. 本 phase 不修改运行时。

## 11. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不生成 runtime review data 或长期数据，因此不需要数据回滚。

## Memory Atlas v1.1.7 Stage 7 Phase 7.2 Runtime Addendum

- task_id: `MA-V117-S7P02`
- acceptance_id: `ACC-MA-V117-S7P02`
- status: `phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review`
- runtime_version: `review_summary_iteration_runtime.v1_1_7_stage7_phase2`
- review_schema_version: `memory_atlas_review_summary.v1_1_7_stage7_phase2`
- validators: `validate:v1.1.7-stage7-phase2`; `validate:review-summary-iteration-browser`

Stage 7 Phase 7.2 将本合同从 v1.1.6 合同层推进到 production `summary` view runtime。运行时必须在同一页提供 `review_period_selector`、`theme_change_panel`、`opportunity_panel`、`low_value_loop_panel`、`decision_change_panel`、`next_action_panel`、`proposal_decision_panel` 和 `iteration_backlog`。

本 runtime 必须回答八个问题：本期主导主题是什么、哪些主题增强、哪些主题衰退、哪些新机会出现、哪些低价值循环出现、哪些决策变化、下一步动作是什么、是否需要生成 proposal。输出必须包含 `proposal_candidate`、`evidence_refs` 和 `iteration_backlog`，且 proposal handoff 仍为 proposal-only。

Boundaries: No Stage 8 summary closure; No direct active-memory writeback; No raw/private/cookie/session/secret data access; No GitHub main upload. 本 phase 不写 proposal queue，不执行 agent apply，不上传 GitHub main。
