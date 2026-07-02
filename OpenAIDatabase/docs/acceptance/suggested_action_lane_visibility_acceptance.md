# Memory Atlas suggested action lane 可见性验收

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 2

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 2 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 `suggested_action_lane` 的行动卡信息层级、字段、排序、比较、Inspector 交接和 proposal-only 边界。通过本验收只表示 Stage 2 Phase 2 的合同完整，不表示运行时 lane 或截图验收已完成。

## 2. 信息层级检查

必须覆盖三层：

1. `scan_row`：title、action_type、urgency、roi_score、effort_cost、confidence、evidence_count。
2. `decision_row`：reason、next_step、recommended_time_window、linked_theme_ids、linked_asset_ids。
3. `evidence_drawer`：evidence_refs、source_scope、matched_reason、proposal_hint、rollback_hint。

只展示 title 或一句建议即失败。

## 3. 字段检查

| 字段 | 通过标准 | 失败示例 |
|---|---|---|
| action_id | 有稳定 ID | 只有标题 |
| title | 中文短标题 | 长句塞进标题 |
| action_type | continue/review/consolidate/explore/defer | 任意自由文本 |
| reason | 人类可读推荐原因 | 只有模型字段 |
| roi_score | 可比较 ROI | 没有收益判断 |
| effort_cost | low/medium/high | 没有成本 |
| urgency | now/this_week/later/watch | 没有时间窗口 |
| confidence | high/medium/low | 无置信度 |
| evidence_count | 脱敏证据数量 | 只说“有证据” |
| evidence_refs | redacted evidence 或 Inspector 引用 | 直接贴 raw text |
| source_scope | all/memory_atlas/codex | 来源不明 |
| linked_theme_ids | 能关联主题 | 行动与主题断开 |
| linked_asset_ids | 能关联层级资产 | 行动与资产断开 |
| next_step | 下一步明确 | 只说“处理一下” |
| recommended_time_window | 执行窗口明确 | 没有时间判断 |
| proposal_hint | 是否建议 proposal-only | 暗示直接应用 |
| rollback_hint | 后续应用后如何撤回 | 没有撤回路径 |

## 4. 分组、排序与徽标检查

必须覆盖：

- 分组：now、this_week、later、watch。
- 排序：roi_score、urgency、effort_cost、confidence、evidence_count、selection_focus。
- 徽标：high_roi、medium_roi、low_roi。
- 徽标：low_effort、medium_effort、high_effort。
- 徽标：urgent_now、this_week、later、watch。
- 徽标：evidence_ready、evidence_thin、missing_evidence。
- 徽标：proposal_recommended、proposal_not_needed。

只按创建时间或数组顺序展示即失败。

## 5. 展开与比较检查

必须支持：

- expand action。
- compare actions。
- pin action。
- mark reviewed。
- clear temporary state。

pin action 和 mark reviewed 只能是前端临时状态或 proposal hint，不得直接写 active memory。

## 6. Inspector 交接检查

Inspector handoff 至少包含：

- source_lane = suggested_action_lane。
- target_type = suggested_action。
- action_id。
- title。
- action_type。
- reason。
- roi_score。
- effort_cost。
- urgency。
- confidence。
- evidence_refs。
- linked_theme_ids。
- linked_asset_ids。
- next_step。
- recommended_time_window。
- proposal_hint。
- rollback_hint。

点击行动卡后无法解释 ROI、努力成本、紧急度、证据或下一步即失败。

## 7. 空态、错误态与低证据态

必须覆盖：

- empty_state。
- low_evidence_state。
- error_state。
- loading_state。

字段缺失时必须显示合同错误，不得用 mock 数据伪造建议动作。

## 8. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | now / this_week / later / watch 至少两个组可见，至少一条行动展开 |
| Tablet 768x1024 | 行动卡堆叠可读，展开内容不遮挡 Inspector 或导航 |
| Mobile 390x844 | scan_row 不溢出，徽标、ROI、effort、urgency 和动作入口可点击 |

## 9. 安全失败条件

任一情况出现即失败：

1. 合同允许 lane 直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 scan_row、decision_row 或 evidence_drawer。
4. 合同缺少 roi_score、effort_cost、urgency、evidence_refs、next_step 或 rollback_hint。
5. 合同把 Search 2.0、复盘、Data Map、完整 proposal editor 或 agent apply 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 低证据动作被静默隐藏或用 mock 数据补足。

## 10. 通过条件

Stage 2 Phase 2 通过时必须有：

1. `docs/product/suggested_action_lane_visibility_contract.md`。
2. `docs/acceptance/suggested_action_lane_visibility_acceptance.md`。
3. `validate:v1.1.6-stage2-phase2`。
4. 三文件和模型参数记录中登记 `MA-V116-S2P02`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
