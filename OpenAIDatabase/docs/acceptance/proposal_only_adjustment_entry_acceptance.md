# Memory Atlas proposal-only 调整入口验收

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 5

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 1 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 proposal-only 调整入口的安全边界和可理解性底线。通过本验收只表示 Stage 1 Phase 5 的合同完整，不表示完整 proposal 编辑工作区、agent apply 或运行时 UI 已完成。

## 2. 入口检查

必须覆盖五类入口：

1. `memory_overview` / 记忆总览。
2. `suggested_action_detail` / 建议动作明细。
3. `tier_asset_detail` / 层级资产明细。
4. `topic_classification_detail` / 主题分类明细。
5. `inspector` / Inspector。

任一入口缺失即失败。

## 3. 目标类型检查

必须覆盖四类目标：

| target_type | 通过标准 | 失败示例 |
|---|---|---|
| overview_signal | 能从总览信号创建 proposal draft | 总览只能看，不能提出修正 |
| suggested_action | 能从建议动作创建 proposal draft | 动作状态只能直接应用 |
| tier_asset | 能从层级资产创建 proposal draft | 资产重要性无调整入口 |
| topic_classification | 能从主题分类创建 proposal draft | 主题归类无法建议变更 |

## 4. 字段检查

| field | 通过标准 | 失败示例 |
|---|---|---|
| importance | 可建议重要性变化 | 直接改 active memory importance |
| priority | 可建议优先级变化 | 没有 reason 或 evidence |
| topic_category | 可建议主题归类变化 | 直接覆盖主题字段 |
| action_status | 可建议动作状态变化 | 按钮文案显示已完成 |
| due_window | 可建议时间窗口 | 没有 rollback hint |
| hidden_until | 可建议延后显示 | 永久隐藏且不可追踪 |
| stale_override | 可建议复活或过期覆盖 | 没有冲突检查 |
| confidence_note | 可补充人工置信说明 | 写入 raw/private 内容 |

## 5. Proposal draft schema 检查

每个 proposal draft 至少包含：

- `proposal_id`。
- `proposal_schema_version`。
- `parent_snapshot_id`。
- `entry_surface`。
- `target_type`。
- `target_id`。
- `field`。
- `old_value_ref`。
- `proposed_value`。
- `reason`。
- `evidence_refs`。
- `confidence`。
- `created_at`。
- `created_by`。
- `requires_conflict_check`。
- `requires_agent_or_human_apply`。
- `rollback_hint`。

缺少任一字段即失败。

## 6. 用户可读说明检查

后续实现 phase 必须让用户明确理解：

- proposal draft 不会直接写 active memory。
- draft 需要冲突检查。
- apply 必须由 agent/human 执行。
- apply 后必须有 history、版本链和 rollback。
- 入口文案不得暗示“已应用”或“已保存到长期记忆”。

## 7. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 至少一个建议动作、一个层级资产和一个主题能显示 proposal-only 入口 |
| Tablet 768x1024 | proposal-only 说明不遮挡 Inspector 或导航 |
| Mobile 390x844 | 入口按钮、字段名、reason 输入提示和安全说明不溢出 |

## 8. 安全失败条件

任一情况出现即失败：

1. 合同允许前端直接修改 active memory 或长期记忆。
2. 合同要求显示 raw/private/cookie/session/secret 数据。
3. 合同缺少 requires_conflict_check 或 requires_agent_or_human_apply。
4. 合同缺少 rollback_hint。
5. 合同把完整 proposal 编辑工作区、agent apply、Search 2.0、复盘或 Data Map 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。
7. 用户可读说明暗示 proposal 已应用或已保存到长期记忆。

## 9. 通过条件

Stage 1 Phase 5 通过时必须有：

1. `docs/product/proposal_only_adjustment_entry_contract.md`。
2. `docs/acceptance/proposal_only_adjustment_entry_acceptance.md`。
3. `validate:v1.1.6-stage1-phase5`。
4. 三文件和模型参数记录中登记 `MA-V116-S1P05`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 10. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
