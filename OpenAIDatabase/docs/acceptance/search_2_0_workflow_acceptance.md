# Memory Atlas Search 2.0 工作流验收

适用版本：Memory Atlas v1.1.6 Stage 4 Phase 1

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS、不建立真实搜索索引、不读取 raw/private、不写长期记忆、不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 `search_2_0_workflow` 的搜索结果结构、解释字段、跳转动作、空结果恢复和 proposal handoff。通过本验收只表示 Stage 4 Phase 1 的合同完整，不表示运行时搜索、浏览器截图、复盘总结或 Data Map 2.0 已完成。

## 2. 查询区检查

必须覆盖：

| 项 | 通过标准 | 失败示例 |
|---|---|---|
| `query_input` | 支持自然语言 query 和 scope | 只有内部字段搜索 |
| `filter_state` | 显示 active filters、结果数和 stale/black hole/proto-star 状态 | 用户不知道为什么看不到结果 |
| tier filter | 覆盖 core_profile、project、decision、workflow、knowledge、opportunity、stale | 只能按项目名搜 |
| topic filter | 可按主题分类聚焦 | 主题分类不可查 |
| recency filter | 可区分 recent、active、stale、archival | 时间状态不可解释 |
| importance filter | 可筛 high/critical | 不能找重要记忆 |

## 3. Result list 检查

每条 `result_list` 结果必须显示：

- `title`
- `summary`
- `source`
- `tier`
- `topic`
- `recency`
- `importance`
- `matched_reason`
- `evidence_refs` 或 evidence count
- `jump_to_starfield`
- `jump_to_river`
- `open_inspector`

缺少任一核心字段即失败。`matched_reason` 必须解释为什么命中，不能只显示 score。

## 4. 跳转动作检查

| 动作 | 通过标准 | 失败示例 |
|---|---|---|
| `jump_to_starfield` | 可定位到记忆星系的主题/资产 ref | 搜索结果只能停留列表 |
| `jump_to_river` | 可定位到时间河 event/time band/pulse ref | 不能追溯形成过程 |
| `open_inspector` | 可进入 Inspector 看原因、证据和 proposal-only 入口 | 无法解释或调整 |

缺少映射时必须显示 `no_starfield_mapping`、`no_river_event_ref` 或 `inspector_target_missing` 这类原因。

## 5. Session summary 检查

`search_session_summary` 必须包含：

1. query。
2. result_count。
3. dominant_topics。
4. high_importance_hits。
5. stale_or_black_hole_hits。
6. missing_evidence。
7. next_step。
8. proposal_candidate。

缺少 next_step 或 proposal_candidate 判断时，搜索不能通过“工作流”验收。

## 6. Zero result recovery 检查

`zero_result_recovery` 必须给出可执行恢复动作：

- broaden query。
- remove or relax filters。
- try related topic。
- search stale/archive。
- later Review / Summary / Iteration hint。

空结果只显示 “No results” 即失败。

## 7. 响应式截图入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | query、filters、result list、matched_reason、three jump actions 和 session summary 同屏或清晰分区 |
| Tablet 768x1024 | filters 可折叠但 result fields 和 open_inspector 不丢失 |
| Mobile 390x844 | title、summary、matched_reason、importance 和 action buttons 不溢出 |

本 phase 只定义截图入口，不启动浏览器。

## 8. 安全检查

必须满足：

1. 不读取 raw/private/cookie/session/secret。
2. 不显示 raw conversation text。
3. 不显示本地绝对私有路径。
4. 不显示 record hash 或 active memory row 全量拷贝。
5. 不直接写 proposal queue 或 active memory。
6. `proposal_candidate` 只能进入 proposal-only handoff。
7. 不自动上传 GitHub main。

## 9. 安全失败条件

任一情况出现即失败：

1. 搜索结果需要 raw/private/cookie/session/secret 才能解释。
2. `matched_reason` 只显示内部 score，不能让人理解。
3. 搜索没有 `jump_to_starfield`、`jump_to_river` 或 `open_inspector`。
4. 空结果没有 `zero_result_recovery`。
5. 合同把 Review / Summary / Iteration 或 Data Map 2.0 冒充为本 phase 已完成。
6. 合同允许搜索结果直接修改 active memory。
7. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 10. 通过条件

Stage 4 Phase 1 通过时必须有：

1. `docs/product/search_2_0_workflow_contract.md`。
2. `docs/acceptance/search_2_0_workflow_acceptance.md`。
3. `validate:v1.1.6-stage4-phase1`。
4. 三文件和模型参数记录中登记 `MA-V116-S4P01`。
5. Changelog 明确 No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时或数据回滚。
