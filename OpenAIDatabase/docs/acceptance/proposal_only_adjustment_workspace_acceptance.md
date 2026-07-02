# Memory Atlas proposal-only 调整工作区验收

适用版本：Memory Atlas v1.1.6 Stage 3 Phase 1

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS、不生成真实 proposal 文件、不执行 agent apply。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 proposal-only 调整工作区的信息架构、安全边界和可解释底线。通过本验收只表示 Stage 3 Phase 1 的合同完整，不表示运行时编辑器、agent apply、持久化队列或截图验收已完成。

## 2. 工作区区域检查

必须覆盖六个区域：

1. `proposal_queue`：列出 proposal draft，并显示状态。
2. `target_context_panel`：显示 target_type、target_id、来源和 Inspector 摘要。
3. `field_editor_panel`：选择允许字段并填写 proposed_value、reason、confidence_note。
4. `proposal_diff_preview`：比较 old_value 与 proposed_value。
5. `safety_review_panel`：显示 conflict check、agent/human apply 和 forbidden payload。
6. `rollback_panel`：显示 rollback_hint、parent_snapshot_id 和版本链提示。

缺少任一区域即失败。

## 3. 目标类型检查

| target_type | 通过标准 | 失败示例 |
|---|---|---|
| overview_signal | 可创建重要性、隐藏窗口或置信说明 proposal | 总览信号只能直接隐藏 |
| suggested_action | 可创建 priority、action_status 或 due_window proposal | 动作状态按钮显示已完成 |
| tier_asset | 可创建 importance、priority、topic_category 或 stale_override proposal | 资产重要性被前端直接覆盖 |
| topic_classification | 可创建 topic_category、importance、priority 或 stale_override proposal | 主题归类直接写 active memory |

## 4. 字段检查

| field | 通过标准 | 失败示例 |
|---|---|---|
| importance | 显示 old_value、proposed_value、reason 和 evidence_refs | 只显示新值，无旧值来源 |
| priority | 支持 p0 / p1 / p2 / p3 / watch | 直接改排序且无 proposal |
| topic_category | 只能建议归类或合并 | 自动创建永久主题 |
| action_status | 支持 continue / review / done / defer / watch | 文案暗示已应用 |
| due_window | 支持 now / this_week / later / watch | 缺 rollback_hint |
| hidden_until | 支持 ISO date、next_review 或 clear | 永久隐藏且不可复核 |
| stale_override | 支持 current / needs_review / stale / unknown | 无 conflict check |
| confidence_note | 只能写脱敏人工说明 | 写入 raw/private 内容 |

## 5. Proposal draft schema 检查

每个 proposal draft 至少包含：

- `proposal_id`。
- `proposal_schema_version`。
- `parent_snapshot_id`。
- `source_surface`。
- `entry_surface`。
- `target_type`。
- `target_id`。
- `field`。
- `old_value`。
- `old_value_ref`。
- `proposed_value`。
- `reason`。
- `evidence_refs`。
- `confidence`。
- `status`。
- `created_at`。
- `created_by`。
- `requires_conflict_check`。
- `requires_agent_or_human_apply`。
- `rollback_hint`。

缺少任一字段即失败。

## 6. 状态检查

必须覆盖五种状态：

| status | 通过标准 | 失败示例 |
|---|---|---|
| draft | 可继续编辑，不可 apply | 草稿直接写入 active memory |
| needs_review | 明确需要补证据或冲突说明 | 待复核仍可直接应用 |
| ready_for_agent_apply | 只表示可交接 agent/human | 文案显示已保存到长期记忆 |
| rejected | 保留拒绝原因 | 删除且无法复盘 |
| superseded | 链接替代 proposal | 覆盖历史链 |

## 7. Inspector 与 diff 检查

从 Inspector 进入工作区时必须保留：

- target_type。
- target_id。
- field。
- old_value。
- old_value_ref。
- proposed_value。
- reason。
- evidence_refs。
- confidence。
- rollback_hint。

`proposal_diff_preview` 必须展示 old_value 和 proposed_value 的差异，但不能显示 raw/private/cookie/session/secret、本地绝对私有路径或未脱敏证据全文。

## 8. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | proposal_queue、field_editor_panel、proposal_diff_preview 和 safety_review_panel 同屏可读 |
| Tablet 768x1024 | 工作区区域可折叠，安全说明不遮挡字段 |
| Mobile 390x844 | 字段名、reason 输入提示、rollback_hint 和 proposal-only 说明不溢出 |

## 9. 安全失败条件

任一情况出现即失败：

1. 合同允许前端直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 requires_conflict_check 或 requires_agent_or_human_apply。
4. 合同缺少 rollback_hint 或 parent_snapshot_id。
5. 合同把 agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 用户可读说明暗示 proposal 已应用或已保存到长期记忆。

## 10. 通过条件

Stage 3 Phase 1 通过时必须有：

1. `docs/product/proposal_only_adjustment_workspace_contract.md`。
2. `docs/acceptance/proposal_only_adjustment_workspace_acceptance.md`。
3. `validate:v1.1.6-stage3-phase1`。
4. 三文件和模型参数记录中登记 `MA-V116-S3P01`。
5. Changelog 明确 No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
