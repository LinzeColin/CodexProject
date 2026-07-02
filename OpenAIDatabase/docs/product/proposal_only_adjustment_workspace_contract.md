# Memory Atlas proposal-only 调整工作区合同

适用版本：Memory Atlas v1.1.6 Stage 3 Phase 1

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑、agent apply 逻辑或长期记忆。

## 1. 目标

Stage 3 Phase 1 把 Stage 1 的 proposal-only 调整入口升级为完整 proposal-only adjustment workspace 的产品合同。它解决的问题是：用户可以提出重要性、优先级、主题分类、动作状态、时间窗口、隐藏、stale 覆盖和置信说明的修正，但系统必须把这些修正保存在 proposal draft 语义里，而不是直接写 active memory。

本 phase 只定义 proposal-only 调整工作区的信息架构、字段、状态、diff preview、安全说明和 rollback 边界，不实现 React/CSS、不启动浏览器、不生成真实 proposal 文件、不执行 agent apply、不进入 Search 2.0、Review / Summary / Iteration 或 Data Map 2.0。

## 2. 工作区区域

proposal-only adjustment workspace 必须包含以下区域：

| region | 中文名 | 作用 |
|---|---|---|
| `proposal_queue` | proposal 队列 | 列出本地待处理 proposal draft，不直接 apply |
| `target_context_panel` | 目标上下文面板 | 展示 target_type、target_id、来源页面和 Inspector 摘要 |
| `field_editor_panel` | 字段编辑面板 | 选择允许字段、输入 proposed_value、reason 和 confidence note |
| `proposal_diff_preview` | proposal diff 预览 | 比较 old_value 与 proposed_value，禁止显示 raw/private 全文 |
| `safety_review_panel` | 安全复核面板 | 显示 conflict check、agent/human apply、no-direct-writeback 和 forbidden payload |
| `rollback_panel` | 回滚说明面板 | 显示 rollback_hint、parent_snapshot_id 和未来版本链要求 |

## 3. 允许目标类型

| target_type | 中文名 | 可调整内容 |
|---|---|---|
| `overview_signal` | 总览信号 | 重要性、隐藏窗口、置信说明 |
| `suggested_action` | 建议动作 | 重要性、优先级、动作状态、due window、隐藏窗口、置信说明 |
| `tier_asset` | 层级资产 | 重要性、优先级、主题分类、stale 覆盖、隐藏窗口、置信说明 |
| `topic_classification` | 主题分类 | 重要性、优先级、主题分类、stale 覆盖、隐藏窗口、置信说明 |

工作区不得允许调整 raw text、cookie/session、secret、未脱敏证据、GitHub 数据、模型参数或本地绝对私有路径。

## 4. 允许字段

| field | old_value 来源 | proposed_value 约束 |
|---|---|---|
| `importance` | Inspector 或 redacted snapshot | high / medium / low 或数值分桶 |
| `priority` | action / asset / topic 当前优先级 | p0 / p1 / p2 / p3 / watch |
| `topic_category` | 当前主题或资产归类 | 现有 topic id 或待复核新主题 |
| `action_status` | 建议动作当前状态 | continue / review / done / defer / watch |
| `due_window` | 建议动作时间窗口 | now / this_week / later / watch |
| `hidden_until` | 当前显示策略 | ISO date、next_review 或 clear |
| `stale_override` | 当前 stale 状态 | current / needs_review / stale / unknown |
| `confidence_note` | 人工说明 | 中文短说明，不含 raw/private 内容 |

字段编辑必须保留 reason、evidence_refs、confidence 和 rollback_hint。缺少 reason 或 rollback_hint 时，proposal 只能停留在 `draft` 或 `needs_review`。

## 5. Proposal draft schema

每个 proposal draft 至少包含：

```json
{
  "proposal_id": "string",
  "proposal_schema_version": "memory_atlas_proposal_workspace.v1",
  "parent_snapshot_id": "string",
  "source_surface": "proposal_only_adjustment_workspace",
  "entry_surface": "inspector",
  "target_type": "tier_asset",
  "target_id": "string",
  "field": "importance",
  "old_value": "medium",
  "old_value_ref": "redacted-snapshot-ref",
  "proposed_value": "high",
  "reason": "string",
  "evidence_refs": ["redacted-evidence-id"],
  "confidence": "medium",
  "status": "draft",
  "created_at": "ISO-8601",
  "created_by": "human_or_agent",
  "requires_conflict_check": true,
  "requires_agent_or_human_apply": true,
  "rollback_hint": "string"
}
```

`old_value` 只能来自已脱敏 snapshot、Inspector 字段或现有 contract 字段，不得复制 raw/private 内容。`proposal_id` 必须稳定可引用，`parent_snapshot_id` 必须能让后续 agent/human apply 做冲突检查。

## 6. Proposal 状态

| status | 中文名 | 允许动作 |
|---|---|---|
| `draft` | 草稿 | 编辑字段、reason、confidence_note 和 rollback_hint |
| `needs_review` | 待复核 | 补证据、补冲突说明、回到 draft |
| `ready_for_agent_apply` | 可交给 agent/human apply | 仅表示可交接，不表示已写入 |
| `rejected` | 已拒绝 | 保留原因和 rollback hint，不 apply |
| `superseded` | 已被替代 | 链接 replacement proposal，不 apply |

任何状态都不能由前端直接修改 active memory。`ready_for_agent_apply` 只表示进入后续独立 apply gate。

## 7. Inspector 交接

从 Inspector 进入工作区时必须传递：

- source_surface。
- entry_surface。
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
- proposal-only 安全说明。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 8. 安全复核规则

工作区必须默认显示以下安全事实：

1. proposal-only，不直接写长期记忆。
2. active memory 不会在前端被修改。
3. apply 必须由 agent/human 在独立 gate 完成。
4. apply 前必须重新读取当前 snapshot 并执行 conflict check。
5. apply 后必须写 history、版本链和 rollback 信息。
6. raw/private/cookie/session/secret/local absolute path 不得进入 payload。

禁止使用“已应用”“已保存到长期记忆”“已更新数据库”等文案。允许使用“创建草案”“等待复核”“可交给 agent/human apply”。

## 9. 与后续 stage 的边界

本 phase 不覆盖：

- React/CSS runtime UI。
- 浏览器截图和 Playwright 验收。
- 本地 proposal queue 持久化实现。
- agent apply CLI 或自动 apply。
- active memory 写回。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- GitHub main upload。

这些必须在后续 phase 或 stage 单独交付和验收。

## 10. 验收

Stage 3 Phase 1 通过条件：

1. 合同覆盖 proposal_queue、target_context_panel、field_editor_panel、proposal_diff_preview、safety_review_panel 和 rollback_panel。
2. 合同覆盖 overview_signal、suggested_action、tier_asset 和 topic_classification。
3. 合同覆盖 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 和 confidence_note。
4. 合同定义 proposal_id、parent_snapshot_id、target_id、field、old_value、proposed_value、reason、created_at、rollback_hint、requires_conflict_check 和 requires_agent_or_human_apply。
5. 合同覆盖 draft、needs_review、ready_for_agent_apply、rejected 和 superseded。
6. 合同明确 Inspector 交接和 proposal-only 安全说明。
7. 合同明确 raw/private 边界、no direct active memory write、agent apply 后续 gate 和 rollback。
8. 本 phase 不修改运行时。

## 11. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI、数据或长期记忆回滚。
