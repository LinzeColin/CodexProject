# Memory Atlas 层级资产明细验收

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 3

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 1 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定层级资产明细的可见性和可解释性底线。通过本验收只表示 Stage 1 Phase 3 的合同完整，不表示运行时 UI 已完成层级资产工作台或截图验收。

## 2. 层级检查

必须覆盖七类资产：

1. `core_profile` / 核心画像。
2. `project` / 项目。
3. `decision` / 决策。
4. `workflow` / 工作流。
5. `knowledge` / 知识。
6. `opportunity` / 机会。
7. `stale` / 过期或待复核。

任一资产层级缺失即失败。

## 3. 字段检查

| 检查项 | 通过标准 | 失败示例 |
|---|---|---|
| asset_id | 每个资产有稳定 ID | 只有标题 |
| asset_tier | 使用七类资产枚举 | 任意自由文本 |
| title | 中文短标题 | 长句塞进标题 |
| summary | 两行内人类可读摘要 | 只有数据库字段 |
| importance | high/medium/low | 无重要性 |
| priority | p0/p1/p2/p3/watch | 无优先级 |
| confidence | high/medium/low | 无置信度 |
| staleness_status | current/needs_review/stale/unknown | 无有效性判断 |
| evidence_count | 显示脱敏证据数量 | 只说“有证据” |
| evidence_refs | 指向 redacted evidence 或 Inspector | 直接贴 raw text |
| source_scope | 显示 总数据源 / ChatGPT / Codex | 来源不明 |
| linked_action_ids | 能关联建议动作 | 资产与行动断开 |
| linked_theme_ids | 可指向后续主题分类入口 | 伪造主题分类已完成 |
| linked_time_range | 可指向时间河窗口 | 时间来源不明 |
| recommended_asset_action | keep/review/consolidate/lower_priority/validate/defer | 没有下一步 |
| proposal_hint | 说明是否建议生成 proposal | 暗示直接应用 |
| rollback_hint | 说明后续应用后如何撤回或复核 | 没有撤回路径 |

## 4. 展开与 Inspector 检查

层级资产摘要可以短，但展开层或 Inspector 必须能承载完整解释。后续实现 phase 需要验证：

- 首页摘要不超过两行。
- 展开层显示七类资产分组。
- 每个资产显示 importance、priority、confidence 和 staleness_status。
- 点击资产后 Inspector focus 同步。
- linked_action_ids 能回到建议动作明细。
- linked_time_range 能进入记忆时间河。

## 5. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类资产分组和至少一条展开明细可读 |
| Tablet 768x1024 | 展开明细不遮挡 Inspector 或导航 |
| Mobile 390x844 | 标题、重要性、优先级、置信度和动作按钮不溢出 |

## 6. 安全失败条件

任一情况出现即失败：

1. 合同要求显示 raw/private/cookie/session/secret 数据。
2. 合同允许层级资产直接修改 active memory 或长期记忆。
3. 合同缺少七类资产之一。
4. 合同没有 importance、priority、confidence、staleness_status、evidence、linked_action_ids 或 recommended_asset_action。
5. 合同没有 proposal_hint 或 rollback_hint。
6. 合同把主题分类模型、proposal 编辑工作区、搜索复盘或 Data Map 冒充为本 phase 已完成。
7. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 7. 通过条件

Stage 1 Phase 3 通过时必须有：

1. `docs/product/tier_asset_detail_contract.md`。
2. `docs/acceptance/tier_asset_detail_acceptance.md`。
3. `validate:v1.1.6-stage1-phase3`。
4. 三文件和模型参数记录中登记 `MA-V116-S1P03`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 8. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
