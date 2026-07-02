# Memory Atlas 明细可见性工作台验收

适用版本：Memory Atlas v1.1.6 Stage 2 Phase 1

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 2 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定明细可见性工作台的 IA、展开、筛选、排序、Inspector 交接和安全边界。通过本验收只表示 Stage 2 Phase 1 的合同完整，不表示运行时工作台或截图验收已完成。

## 2. 工作台区域检查

必须覆盖以下区域：

1. `workbench_header`。
2. `scope_controls`。
3. `density_mode`。
4. `suggested_action_lane`。
5. `tier_asset_lane`。
6. `topic_classification_lane`。
7. `inspector_handoff`。
8. `proposal_entry_hint`。
9. `empty_state`。
10. `error_state`。

任一区域缺失即失败。

## 3. 三类 lane 检查

| lane | 必须字段 | 失败示例 |
|---|---|---|
| suggested_action_lane | action_id、title、action_type、reason、roi_score、effort_cost、urgency、confidence、evidence_count、next_step、proposal_hint、open_inspector | 只有短句建议，没有 ROI、证据或下一步 |
| tier_asset_lane | asset_id、asset_tier、title、summary、importance、priority、confidence、staleness_status、evidence_count、linked_action_ids、recommended_asset_action、proposal_hint、open_inspector | 只有资产名称，没有重要性、优先级或证据 |
| topic_classification_lane | topic_id、topic_label、topic_state、topic_strength、trend、confidence、record_count、evidence_count、linked_asset_ids、linked_action_ids、recommended_topic_action、proposal_hint、open_inspector | 只有 tag 列表，没有趋势、强度或关联动作 |

## 4. 展开交互检查

每条明细必须支持：

- collapsed summary。
- expanded detail。
- open_inspector。
- jump_to_related。
- proposal_only_entry。

展开明细必须显示 redacted evidence_refs、reason 或 matched_reason、linked ids、proposal_hint 和 rollback_hint。只显示 hover tooltip 或只显示摘要即失败。

## 5. 筛选与排序检查

必须覆盖：

- source_scope：all / memory_atlas / codex。
- confidence：high / medium / low。
- evidence_count：has_evidence / missing_evidence。
- proposal_hint：recommended / none。
- urgency。
- effort_cost。
- action_type。
- asset_tier。
- importance。
- priority。
- staleness_status。
- topic_state。
- trend。
- clear_filters。

筛选后空结果必须说明“无匹配”或“数据缺失”，不得用 mock 数据填充。

## 6. Inspector 交接检查

Inspector handoff 至少包含：

- source_lane。
- target_id。
- target_type。
- display_title。
- status_or_state。
- confidence。
- evidence_refs。
- linked_action_ids。
- linked_asset_ids。
- linked_topic_ids。
- reason_or_matched_reason。
- recommended_next_step。
- proposal_hint。
- rollback_hint。

任一明细点击后无法说明来源、证据、下一步或回滚路径即失败。

## 7. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 三个 lane 同屏或可清晰切换，至少各有一条展开明细 |
| Tablet 768x1024 | lane 可堆叠，展开明细不遮挡 Inspector 或导航 |
| Mobile 390x844 | 单 lane 可切换，标签、按钮和证据数量不溢出 |

## 8. 安全失败条件

任一情况出现即失败：

1. 合同允许工作台直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 suggested_action_lane、tier_asset_lane 或 topic_classification_lane。
4. 合同缺少 expanded detail、open_inspector 或 proposal_only_entry。
5. 合同把 Search 2.0、复盘、Data Map、完整 proposal editor 或 agent apply 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 空态或错误态使用 mock 数据伪造明细。

## 9. 通过条件

Stage 2 Phase 1 通过时必须有：

1. `docs/product/detail_visibility_workbench_contract.md`。
2. `docs/acceptance/detail_visibility_workbench_acceptance.md`。
3. `validate:v1.1.6-stage2-phase1`。
4. 三文件和模型参数记录中登记 `MA-V116-S2P01`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 10. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
