# Memory Atlas 建议动作明细验收

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 2

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 1 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定建议动作的明细可见性底线。通过本验收只表示 Stage 1 Phase 2 的合同完整，不表示运行时 UI 已完成明细工作台或截图验收。

## 2. 字段检查

| 检查项 | 通过标准 | 失败示例 |
|---|---|---|
| action_id | 每条动作有稳定 ID | 只有中文标题 |
| action_type | 使用 continue/review/consolidate/explore/defer | 任意自由文本类型 |
| reason | 明确为什么建议做 | 只有“建议处理” |
| roi_score | 显示相对 ROI 或 leverage | 无收益判断 |
| effort_cost | 显示 low/medium/high 并可解释 | 用户无法估计成本 |
| urgency | 显示 now/this_week/later/watch | 没有时间窗口 |
| confidence | 显示 high/medium/low | 没有可信度 |
| evidence_count | 显示脱敏证据数量 | 只说“有证据” |
| evidence_refs | 指向 redacted evidence 或 Inspector | 直接贴 raw text |
| source_scope | 显示 总数据源 / ChatGPT / Codex | 来源不明 |
| linked_theme_ids | 关联主题或 cluster | 动作无法回到星系/时间河 |
| next_step | 给出用户下一步 | 只有概念性建议 |
| proposal_hint | 说明是否建议生成 proposal | 暗示直接应用 |
| rollback_hint | 说明后续应用后如何撤回或复核 | 没有撤回路径 |

## 3. 动作类型检查

必须覆盖五类动作语义：

1. `continue`：继续投入高 ROI 主题。
2. `review`：复盘冲突、低价值循环、过期或低置信内容。
3. `consolidate`：整合分散记忆、重复主题、工作流或能力记录。
4. `explore`：验证 proto-star 机会。
5. `defer`：暂缓低 ROI 或噪音输入。

## 4. 展开与 Inspector 检查

建议动作摘要可以短，但展开层或 Inspector 必须能承载完整解释。后续实现 phase 需要验证：

- 首页摘要不超过两行。
- 展开层包含 reason、ROI、努力成本、紧急度、证据、下一步和 proposal hint。
- 点击动作后 Inspector focus 同步。
- 跳转记忆星系和记忆时间河时保留 linked theme 或 time range。

## 5. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 建议动作摘要和至少一条展开明细可读 |
| Tablet 768x1024 | 展开明细不遮挡 Inspector 或导航 |
| Mobile 390x844 | 标题、按钮、ROI、effort、urgency 不溢出 |

## 6. 安全失败条件

任一情况出现即失败：

1. 合同要求显示 raw/private/cookie/session/secret 数据。
2. 合同允许建议动作直接修改 active memory 或长期记忆。
3. 合同没有 reason、ROI、effort cost、urgency、evidence 或 next step。
4. 合同没有 proposal_hint 或 rollback_hint。
5. 合同把层级资产模型、主题分类模型、proposal 编辑工作区、搜索复盘或 Data Map 冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 7. 通过条件

Stage 1 Phase 2 通过时必须有：

1. `docs/product/suggested_action_detail_contract.md`。
2. `docs/acceptance/suggested_action_detail_acceptance.md`。
3. `validate:v1.1.6-stage1-phase2`。
4. 三文件和模型参数记录中登记 `MA-V116-S1P02`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 8. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
