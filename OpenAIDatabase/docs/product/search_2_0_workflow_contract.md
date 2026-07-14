# Memory Atlas Search 2.0 工作流合同

适用版本：Memory Atlas v1.1.6 Stage 4 Phase 1；Memory Atlas v1.1.7 Stage 7 Phase 7.1 Runtime Addendum

状态：v1.1.6 baseline 为 contract-only；v1.1.7 Stage 7 Phase 7.1 在同一合同下补运行时 addendum。v1.1.6 phase 不修改运行时 UI、CSS、路由、索引器、数据生成、写回逻辑、Review / Summary / Iteration、Data Map 2.0 或长期记忆。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 目标

Stage 4 Phase 1 定义 `search_2_0_workflow`。Search 2.0 不再只是关键词命中列表，而是用于“找到、理解、跳转、复盘、提出下一步”的工作流入口。

本 phase 只定义搜索工作流的信息架构、结果字段、跳转动作、空结果恢复、proposal handoff、安全边界和验收，不实现 React runtime、不改 CSS、不建立真实搜索索引、不读取 raw/private、不写 active memory、不进入 Review / Summary / Iteration 或 Data Map 2.0。

## 2. 工作流区域

Search 2.0 后续实现必须至少包含：

| region | 目的 | 最低可见内容 |
|---|---|---|
| `query_input` | 接收用户查询和筛选条件 | query、scope、time window、tier、topic、importance filter |
| `filter_state` | 解释当前过滤器 | active filters、结果数、是否包含 stale/black hole/proto-star |
| `result_list` | 呈现可操作搜索结果 | title、summary、source、tier、topic、recency、importance、matched_reason |
| `result_action_bar` | 让搜索结果进入上下文 | jump_to_starfield、jump_to_river、open_inspector |
| `search_session_summary` | 总结本次搜索发现 | dominant matches、missing evidence、next step、proposal_candidate |
| `zero_result_recovery` | 空结果时指导继续 | broaden query、remove filter、try related topic、open review workflow hint |

## 3. Result schema

每条搜索结果必须能被渲染为 redacted summary，不得依赖 raw/private 全文：

```json
{
  "result_id": "string",
  "title": "string",
  "summary": "redacted summary",
  "source": "snapshot/source label",
  "tier": "core_profile|project|decision|workflow|knowledge|opportunity|stale",
  "topic": "string",
  "recency": "recent|active|stale|archival",
  "importance": "low|medium|high|critical",
  "matched_reason": "why this result matched the query",
  "evidence_refs": ["redacted evidence id"],
  "jump_to_starfield": "starfield target ref",
  "jump_to_river": "river event or time band ref",
  "open_inspector": "inspector target ref",
  "proposal_candidate": false
}
```

`matched_reason` 必须是人能读懂的原因说明，不能只显示 scoring number 或内部字段名。

## 4. 查询与排序

Search 2.0 必须支持以下查询语义：

1. 自然语言 query。
2. tier filter：core_profile、project、decision、workflow、knowledge、opportunity、stale。
3. topic filter：主题分类名称或 topic id。
4. recency filter：recent、active、stale、archival。
5. importance filter：low、medium、high、critical。
6. evidence filter：只显示有 evidence_refs 的结果。

默认排序应先按解释价值和行动价值，而不是只按关键词频次：

1. exact semantic match。
2. importance。
3. recency。
4. evidence_count。
5. related action/proposal availability。

## 5. 跳转动作

每条结果必须提供三个明确动作：

- `jump_to_starfield`：跳到记忆星系的主题或资产位置。
- `jump_to_river`：跳到记忆时间河的相关事件、时间带或 pulse。
- `open_inspector`：打开 Inspector 查看原因、证据、相关建议动作和 proposal-only 入口。

动作缺失时必须显示原因，例如 `no_starfield_mapping`、`no_river_event_ref` 或 `inspector_target_missing`。

## 6. Session summary

`search_session_summary` 必须把一次搜索变成可复盘结论：

- `query`：用户查询。
- `result_count`：结果数量。
- `dominant_topics`：本次命中的主导主题。
- `high_importance_hits`：高重要性结果摘要。
- `stale_or_black_hole_hits`：可能需要处理的 stale/black hole 结果。
- `missing_evidence`：证据不足的结果或主题。
- `next_step`：建议下一步。
- `proposal_candidate`：是否建议生成 proposal。

## 7. Zero result recovery

空结果不是失败页。`zero_result_recovery` 必须给出可执行恢复路径：

1. broaden query。
2. remove or relax filters。
3. try related topic。
4. search stale/archive。
5. open Review / Summary / Iteration hint for later stage。

本 phase 只定义 hint，不实现 Review / Summary / Iteration。

## 8. Proposal handoff

Search 2.0 可以标记 `proposal_candidate`，但不得直接写 proposal queue 或 active memory。后续 proposal-only 入口必须沿用 Stage 3 的 proposal workspace 和 proposal queue 边界：

- no direct active memory write。
- requires_conflict_check。
- requires_agent_or_human_apply。
- rollback_hint required。

## 9. 安全边界

Search 2.0 结果只能显示 redacted summary 和 evidence_refs。禁止：

- 读取 raw/private/cookie/session/secret。
- 显示 raw conversation text。
- 显示本地绝对私有路径。
- 显示 record hash 或 active memory row 全量拷贝。
- 前端直接写长期记忆。
- 把搜索结果自动推送到 GitHub main。

## 10. 非目标

本 phase 不覆盖：

- React/CSS runtime UI。
- 搜索索引实现。
- 浏览器截图和 Playwright 验收。
- Review / Summary / Iteration。
- Data Map 2.0。
- agent apply。
- active memory 写回。
- Stage 4 整体复审。
- Stage 5 work。
- GitHub main upload。

## 11. 验收

Stage 4 Phase 1 通过条件：

1. 合同覆盖 `search_2_0_workflow`、`query_input`、`filter_state`、`result_list`、`matched_reason`、`search_session_summary` 和 `zero_result_recovery`。
2. 合同覆盖 title、summary、source、tier、topic、recency、importance、evidence_refs、jump_to_starfield、jump_to_river、open_inspector 和 proposal_candidate。
3. 合同明确 Search 2.0 是工作流入口，不是普通数据库列表。
4. 合同明确 no runtime UI、no raw/private data read、no direct writeback、no GitHub main upload。
5. 本 phase 不修改运行时。

## 12. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不生成 runtime search index 或长期数据，因此不需要数据回滚。

## 13. Memory Atlas v1.1.7 Stage 7 Phase 7.1 Runtime Addendum

Task ID: `MA-V117-S7P01`

Acceptance ID: `ACC-MA-V117-S7P01`

Status: `phase_7_1_search_2_0_runtime_completed_pending_stage7_review`

Runtime version: `search_2_0_runtime.v1_1_7_stage7_phase1`

Session summary version: `search_2_0_session_summary.v1_1_7_stage7_phase1`

Validator: `validate:v1.1.7-stage7-phase1`

Browser validator: `validate:search-2-0-browser`

This addendum implements the production Search 2.0 runtime slice for v1.1.7
Stage 7 Phase 7.1. It turns the previous contract-only `search_2_0_workflow`
into a safe frontend workbench over the existing redacted derived atlas
snapshot.

The runtime covers:

1. `query_input` with query, tier, topic, recency, importance and evidence-only
   filters.
2. `filter_state` with active filter explanation and result count.
3. `result_list` with title, summary, source, tier, topic, recency, importance,
   `matched_reason`, `evidence_refs` and `proposal_candidate`.
4. `result_action_bar` with `jump_to_starfield`, `jump_to_river` and
   `open_inspector`.
5. `search_session_summary` with dominant topics, high-importance hits,
   stale/archive hits, missing evidence, next step and proposal candidate
   judgment.
6. `zero_result_recovery` with broaden query, remove filter, related topic,
   stale/archive search and later review hint.

Safety boundaries:

- No Review / Summary / Iteration runtime in this phase.
- No direct active-memory writeback.
- No raw/private/cookie/session/secret data access.
- No proposal queue write from Search 2.0.
- No agent apply.
- No deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Rollback: revert the Stage 7 Phase 7.1 commit. This removes the runtime
Search 2.0 workbench, scoped CSS, validators, acceptance and records without
changing the redacted source snapshot or long-term memory data.
