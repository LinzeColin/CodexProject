# Memory Atlas tier asset lane 可见性验收

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 3

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 2 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 `tier_asset_lane` 的资产卡信息层级、字段、排序、比较、Inspector 交接和 proposal-only 边界。通过本验收只表示 Stage 2 Phase 3 的合同完整，不表示运行时 lane 或截图验收已完成。

## 2. 信息层级检查

必须覆盖三层：

1. `asset_scan_row`：title、asset_tier、importance、priority、confidence、staleness_status、evidence_count。
2. `asset_decision_row`：summary、recommended_asset_action、linked_action_ids、linked_theme_ids、linked_time_range。
3. `asset_evidence_drawer`：evidence_refs、source_scope、last_seen_range、proposal_hint、rollback_hint。

只展示 title 或一句摘要即失败。

## 3. 字段检查

| 字段 | 通过标准 | 失败示例 |
|---|---|---|
| asset_id | 有稳定 ID | 只有标题 |
| asset_tier | core_profile/project/decision/workflow/knowledge/opportunity/stale | 任意自由文本 |
| title | 中文短标题 | 长句塞进标题 |
| summary | 两行内人类可读摘要 | 只有数据库字段 |
| importance | high/medium/low | 无重要性 |
| priority | p0/p1/p2/p3/watch | 无优先级 |
| confidence | high/medium/low | 无置信度 |
| staleness_status | current/needs_review/stale/unknown | 无有效性判断 |
| evidence_count | 脱敏证据数量 | 只说“有证据” |
| evidence_refs | redacted evidence 或 Inspector 引用 | 直接贴 raw text |
| source_scope | all/memory_atlas/codex | 来源不明 |
| linked_action_ids | 能关联建议动作 | 资产与行动断开 |
| linked_theme_ids | 能关联主题 | 伪造主题分类已完成 |
| linked_time_range | 能关联时间河窗口 | 时间来源不明 |
| recommended_asset_action | keep/review/consolidate/lower_priority/validate/defer | 没有下一步 |
| proposal_hint | 是否建议 proposal-only | 暗示直接应用 |
| rollback_hint | 后续应用后如何撤回 | 没有撤回路径 |

## 4. 分组、排序与徽标检查

必须覆盖：

- 分组：core_profile、project、decision、workflow、knowledge、opportunity、stale。
- 排序：importance、priority、staleness_status、confidence、evidence_count、selection_focus。
- 徽标：high_importance、medium_importance、low_importance。
- 徽标：p0、p1、p2、p3、watch。
- 徽标：current、needs_review、stale、unknown。
- 徽标：evidence_ready、evidence_thin、missing_evidence。
- 徽标：proposal_recommended、proposal_not_needed。

只按创建时间或数组顺序展示即失败。

## 5. 展开与比较检查

必须支持：

- expand asset。
- compare assets。
- pin asset。
- mark reviewed。
- jump to linked action。
- clear temporary state。

pin asset 和 mark reviewed 只能是前端临时状态或 proposal hint，不得直接写 active memory。

## 6. Inspector 交接检查

Inspector handoff 至少包含：

- source_lane = tier_asset_lane。
- target_type = tier_asset。
- asset_id。
- asset_tier。
- title。
- summary。
- importance。
- priority。
- confidence。
- staleness_status。
- evidence_refs。
- source_scope。
- linked_action_ids。
- linked_theme_ids。
- linked_time_range。
- recommended_asset_action。
- proposal_hint。
- rollback_hint。

点击资产卡后无法解释重要性、优先级、有效性、证据、关联动作或下一步即失败。

## 7. 空态、错误态与低证据态

必须覆盖：

- empty_state。
- low_evidence_state。
- stale_conflict_state。
- error_state。
- loading_state。

字段缺失时必须显示合同错误，不得用 mock 数据伪造层级资产。

## 8. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类资产分组至少三个可见，至少一条资产展开 |
| Tablet 768x1024 | 资产卡堆叠可读，展开内容不遮挡 Inspector 或导航 |
| Mobile 390x844 | asset_scan_row 不溢出，tier、importance、priority、staleness 和动作入口可点击 |

## 9. 安全失败条件

任一情况出现即失败：

1. 合同允许 lane 直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 asset_scan_row、asset_decision_row 或 asset_evidence_drawer。
4. 合同缺少 importance、priority、staleness_status、evidence_refs、linked_action_ids、recommended_asset_action 或 rollback_hint。
5. 合同把 Search 2.0、复盘、Data Map、完整 proposal editor 或 agent apply 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 低证据或 stale 资产被静默隐藏或用 mock 数据补足。

## 10. 通过条件

Stage 2 Phase 3 通过时必须有：

1. `docs/product/tier_asset_lane_visibility_contract.md`。
2. `docs/acceptance/tier_asset_lane_visibility_acceptance.md`。
3. `validate:v1.1.6-stage2-phase3`。
4. 三文件和模型参数记录中登记 `MA-V116-S2P03`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
