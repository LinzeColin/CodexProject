# Memory Atlas proposal-only 调整入口合同

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 5

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑、proposal apply 逻辑或长期记忆。

## 1. 目标

Stage 1 Phase 5 解决“用户看懂明细后不知道如何安全提出修正”的问题。记忆总览、建议动作明细、层级资产明细和主题分类明细必须能把用户判断转化为 proposal-only draft 入口，而不是暗示前端可以直接修改长期记忆。

本 phase 只定义 proposal-only 调整入口合同，不实现完整 proposal 编辑工作区、不实现 agent apply、不修改数据库、不进入 Search 2.0、复盘、总结迭代、Data Map 或浏览器截图。

## 2. 调整入口定义

proposal-only 调整入口是一个安全过渡层，用来把用户的判断记录为 draft。它必须说明：

1. 用户想调整哪个目标。
2. 调整来自哪个页面、卡片、明细或 Inspector。
3. 用户想调整哪个字段。
4. 原值如何被引用。
5. 建议值是什么。
6. 调整理由和证据是什么。
7. 为什么不能直接写 active memory。
8. 后续需要由 agent/human 做冲突检查、版本记录和 rollback。

## 3. 允许入口

以下入口可以生成 proposal draft：

| entry_surface | 中文名 | 允许目标 | 说明 |
|---|---|---|---|
| `memory_overview` | 记忆总览 | overview signal / suggested action / tier asset / topic | 从首页摘要进入调整 |
| `suggested_action_detail` | 建议动作明细 | action | 调整动作状态、优先级、due window 或解释备注 |
| `tier_asset_detail` | 层级资产明细 | asset | 调整 importance、priority、staleness 或 confidence note |
| `topic_classification_detail` | 主题分类明细 | topic | 调整 topic_category、importance、priority 或 stale override |
| `inspector` | Inspector | action / asset / topic / overview signal | 从解释层补充证据与理由 |

本 phase 不新增编辑器页面。后续实现可以使用按钮、菜单或 Inspector action，但必须遵守本合同。

## 4. 允许目标类型

| target_type | 中文名 | 说明 |
|---|---|---|
| `overview_signal` | 总览信号 | 今日状态、Memory Weather、低价值循环、新生机会等总览信号 |
| `suggested_action` | 建议动作 | 可执行建议、复盘建议或降噪建议 |
| `tier_asset` | 层级资产 | 核心画像、项目、决策、工作流、知识、机会、stale 资产 |
| `topic_classification` | 主题分类 | dominant、rising、declining、emerging、conflict、black_hole、stale 主题 |

## 5. 允许调整字段

proposal draft 只能覆盖以下字段：

| field | 中文名 | 适用目标 | 说明 |
|---|---|---|---|
| `importance` | 重要性 | overview_signal / suggested_action / tier_asset / topic_classification | 调整重要性判断 |
| `priority` | 优先级 | suggested_action / tier_asset / topic_classification | 调整行动或资产优先级 |
| `topic_category` | 主题分类 | tier_asset / topic_classification | 建议归类变更或主题合并 |
| `action_status` | 动作状态 | suggested_action | 调整为 continue / review / done / defer / watch |
| `due_window` | 时间窗口 | suggested_action | 建议 now / this_week / later / watch |
| `hidden_until` | 延后显示 | overview_signal / suggested_action / tier_asset / topic_classification | 暂时隐藏或降低干扰 |
| `stale_override` | 过期覆盖 | tier_asset / topic_classification | 建议复活、过期或待复核 |
| `confidence_note` | 置信说明 | overview_signal / suggested_action / tier_asset / topic_classification | 补充人工判断和不确定性 |

本 phase 不允许调整 raw text、secret、cookie/session、本地路径、active memory row、GitHub 数据或用户私有原文。

## 6. Proposal draft 最小 schema

每个 proposal draft 必须包含：

```json
{
  "proposal_id": "string",
  "proposal_schema_version": "memory_atlas_proposal_entry.v1",
  "parent_snapshot_id": "string",
  "entry_surface": "memory_overview",
  "target_type": "suggested_action",
  "target_id": "string",
  "field": "importance",
  "old_value_ref": "string",
  "proposed_value": "high",
  "reason": "string",
  "evidence_refs": ["redacted-evidence-id"],
  "confidence": "medium",
  "created_at": "ISO-8601",
  "created_by": "human_or_agent",
  "requires_conflict_check": true,
  "requires_agent_or_human_apply": true,
  "rollback_hint": "string"
}
```

`old_value_ref` 必须引用可复查的 snapshot、Inspector 字段或 redacted evidence，不能直接复制 raw/private 内容。

## 7. 用户可读说明

入口附近必须明确表达：

- 这是 proposal draft，不是直接修改。
- draft 不会写入 active memory。
- 后续需要冲突检查。
- apply 必须由 agent/human 在前端之外执行。
- 每个 apply 都需要 history、版本链和 rollback。

不允许使用“已应用”“已保存到长期记忆”“直接更新”等会造成误解的文案。

## 8. Inspector 交接

从任何入口生成 proposal draft 前，Inspector 或等价解释层必须能展示：

- target_type 和 target_id。
- 当前字段来源。
- old_value_ref。
- proposed_value。
- reason。
- evidence_refs。
- confidence。
- rollback_hint。
- proposal-only 安全说明。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 9. 与完整 proposal 编辑工作区的边界

本 phase 不覆盖：

- 多 proposal 队列。
- proposal diff editor。
- 冲突合并 UI。
- agent apply CLI。
- history 写入。
- rollback proposal 生成。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0。
- 运行时 UI 实现或 Playwright 截图。

这些内容必须在后续 phase 或 stage 单独交付和验收。

## 10. 验收

Stage 1 Phase 5 通过条件：

1. 合同明确 proposal-only 调整入口不是直接写回。
2. 合同覆盖 memory_overview、suggested_action_detail、tier_asset_detail、topic_classification_detail 和 Inspector 五类入口。
3. 合同覆盖 overview_signal、suggested_action、tier_asset、topic_classification 四类目标。
4. 合同覆盖 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 和 confidence_note 八类字段。
5. 合同定义 proposal draft 最小 schema，包含 proposal_id、parent_snapshot_id、target_id、field、old_value_ref、proposed_value、reason、evidence_refs、created_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
6. 合同明确 raw/private 安全边界和 no direct active memory write。
7. 验收文件提供字段检查、失败条件和后续截图入口。
8. 记录文件登记目标、范围、风险、验收和回滚。

## 11. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
