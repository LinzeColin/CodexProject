# Memory Atlas topic classification lane 可见性验收

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 4

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 2 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 `topic_classification_lane` 的主题卡信息层级、字段、排序、比较、Inspector 交接和 proposal-only 边界。通过本验收只表示 Stage 2 Phase 4 的合同完整，不表示运行时 lane 或截图验收已完成。

## 2. 信息层级检查

必须覆盖三层：

1. `topic_scan_row`：topic_label、topic_state、topic_strength、trend、confidence、record_count、evidence_count。
2. `topic_decision_row`：matched_reason、recommended_topic_action、linked_asset_ids、linked_action_ids、related_topic_ids。
3. `topic_evidence_drawer`：evidence_refs、source_scope、linked_starfield_cluster_id、linked_river_range、proposal_hint、rollback_hint。

只展示 tag 名称或一句摘要即失败。

## 3. 字段检查

| 字段 | 通过标准 | 失败示例 |
|---|---|---|
| topic_id | 有稳定 ID | 只有 tag 名称 |
| topic_label | 中文短标签 | 长句塞进标签 |
| topic_state | dominant/rising/declining/emerging/conflict/black_hole/stale | 任意自由文本 |
| topic_strength | 主题强度可比较 | 没有强弱判断 |
| trend | up/down/flat/new/volatile | 没有趋势 |
| confidence | high/medium/low | 无置信度 |
| record_count | 关联脱敏记录数量 | 只说“很多记录” |
| evidence_count | 脱敏证据数量 | 只说“有证据” |
| evidence_refs | redacted evidence 或 Inspector 引用 | 直接贴 raw text |
| source_scope | all/memory_atlas/codex | 来源不明 |
| linked_asset_ids | 能关联层级资产 | 主题与资产断开 |
| linked_action_ids | 能关联建议动作 | 主题与行动断开 |
| linked_starfield_cluster_id | 能关联记忆星系 cluster | 星系入口缺失 |
| linked_river_range | 能关联记忆时间河窗口 | 时间来源不明 |
| related_topic_ids | 能追踪相关主题 | 关系不可追踪 |
| matched_reason | 人类可读归类原因 | 只有模型字段 |
| recommended_topic_action | continue/review/consolidate/validate/reduce_noise/defer/watch | 没有下一步 |
| proposal_hint | 是否建议 proposal-only | 暗示直接应用 |
| rollback_hint | 后续应用后如何撤回 | 没有撤回路径 |

## 4. 分组、排序与徽标检查

必须覆盖：

- 分组：dominant、rising、emerging、conflict、black_hole、declining、stale。
- 排序：topic_strength、trend、confidence、record_count、evidence_count、selection_focus。
- 徽标：high_strength、medium_strength、low_strength。
- 徽标：trend_up、trend_down、trend_flat、trend_new、trend_volatile。
- 徽标：high_confidence、medium_confidence、low_confidence。
- 徽标：evidence_ready、evidence_thin、missing_evidence。
- 徽标：proposal_recommended、proposal_not_needed。

只按创建时间或数组顺序展示即失败。

## 5. 展开与比较检查

必须支持：

- expand topic。
- compare topics。
- pin topic。
- mark reviewed。
- jump to linked asset。
- jump to linked action。
- jump to starfield。
- jump to river。
- clear temporary state。

pin topic 和 mark reviewed 只能是前端临时状态或 proposal hint，不得直接写 active memory。

## 6. Inspector 交接检查

Inspector handoff 至少包含：

- source_lane = topic_classification_lane。
- target_type = topic_classification。
- topic_id。
- topic_label。
- topic_state。
- topic_strength。
- trend。
- confidence。
- record_count。
- evidence_count。
- evidence_refs。
- source_scope。
- linked_asset_ids。
- linked_action_ids。
- linked_starfield_cluster_id。
- linked_river_range。
- related_topic_ids。
- matched_reason。
- recommended_topic_action。
- proposal_hint。
- rollback_hint。

点击主题卡后无法解释主题强度、趋势、置信度、证据、关联资产/动作、星系/时间河入口或下一步即失败。

## 7. 空态、错误态与低证据态

必须覆盖：

- empty_state。
- low_evidence_state。
- conflict_state。
- black_hole_state。
- stale_state。
- error_state。
- loading_state。

字段缺失时必须显示合同错误，不得用 mock 数据伪造主题分类。

## 8. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类主题状态至少四类可见，至少一条主题展开 |
| Tablet 768x1024 | 主题卡堆叠可读，展开内容不遮挡 Inspector 或导航 |
| Mobile 390x844 | topic_scan_row 不溢出，state、strength、trend、confidence 和动作入口可点击 |

## 9. 安全失败条件

任一情况出现即失败：

1. 合同允许 lane 直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 topic_scan_row、topic_decision_row 或 topic_evidence_drawer。
4. 合同缺少 topic_strength、trend、confidence、record_count、evidence_refs、linked_asset_ids、linked_action_ids、matched_reason、recommended_topic_action 或 rollback_hint。
5. 合同把 Search 2.0、复盘、Data Map、完整 proposal editor 或 agent apply 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 低证据、conflict、black_hole 或 stale 主题被静默隐藏或用 mock 数据补足。

## 10. 通过条件

Stage 2 Phase 4 通过时必须有：

1. `docs/product/topic_classification_lane_visibility_contract.md`。
2. `docs/acceptance/topic_classification_lane_visibility_acceptance.md`。
3. `validate:v1.1.6-stage2-phase4`。
4. 三文件和模型参数记录中登记 `MA-V116-S2P04`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
