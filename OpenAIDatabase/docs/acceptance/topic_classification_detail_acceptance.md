# Memory Atlas 主题分类明细验收

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 4

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 1 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定主题分类明细的可见性和可解释性底线。通过本验收只表示 Stage 1 Phase 4 的合同完整，不表示运行时 UI 已完成主题分类工作台或截图验收。

## 2. 主题状态检查

必须覆盖七类主题状态：

1. `dominant` / 主导主题。
2. `rising` / 增强主题。
3. `declining` / 衰退主题。
4. `emerging` / 新生主题。
5. `conflict` / 冲突主题。
6. `black_hole` / 低价值循环。
7. `stale` / 过期或待复核主题。

任一主题状态缺失即失败。

## 3. 字段检查

| 检查项 | 通过标准 | 失败示例 |
|---|---|---|
| topic_id | 每个主题有稳定 ID | 只有 tag 名称 |
| topic_label | 中文短标签 | 长句塞进标签 |
| topic_state | 使用七类主题状态枚举 | 任意自由文本 |
| topic_strength | 显示主题强度 | 没有强弱判断 |
| trend | up/down/flat/new/volatile | 没有趋势 |
| confidence | high/medium/low | 无置信度 |
| record_count | 显示关联记录数 | 只说“很多记录” |
| evidence_count | 显示脱敏证据数量 | 只说“有证据” |
| evidence_refs | 指向 redacted evidence 或 Inspector | 直接贴 raw text |
| source_scope | 显示 总数据源 / ChatGPT / Codex | 来源不明 |
| linked_asset_ids | 能关联层级资产 | 主题与资产断开 |
| linked_action_ids | 能关联建议动作 | 主题与行动断开 |
| linked_starfield_cluster_id | 可指向记忆星系 cluster | 星系入口缺失 |
| linked_river_range | 可指向时间河窗口 | 时间来源不明 |
| related_topic_ids | 可显示关联主题 | 关系不可追踪 |
| matched_reason | 解释为什么归入该主题 | 只有模型字段 |
| recommended_topic_action | continue/review/consolidate/validate/defer/watch | 没有下一步 |
| proposal_hint | 说明是否建议生成 proposal | 暗示直接应用 |
| rollback_hint | 说明后续应用后如何撤回或复核 | 没有撤回路径 |

## 4. 展开与 Inspector 检查

主题分类摘要可以短，但展开层或 Inspector 必须能承载完整解释。后续实现 phase 需要验证：

- 首页摘要不超过两行。
- 展开层显示七类主题状态分组。
- 每个主题显示 topic_strength、trend、confidence、record_count 和 evidence_count。
- 点击主题后 Inspector focus 同步。
- linked_asset_ids 能回到层级资产明细。
- linked_action_ids 能回到建议动作明细。
- linked_starfield_cluster_id 能进入记忆星系。
- linked_river_range 能进入记忆时间河。

## 5. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 七类主题状态和至少一条展开明细可读 |
| Tablet 768x1024 | 展开明细不遮挡 Inspector 或导航 |
| Mobile 390x844 | 主题标签、强度、趋势、置信度和动作按钮不溢出 |

## 6. 安全失败条件

任一情况出现即失败：

1. 合同要求显示 raw/private/cookie/session/secret 数据。
2. 合同允许主题分类直接修改 active memory 或长期记忆。
3. 合同缺少七类主题状态之一。
4. 合同没有 topic_strength、trend、confidence、record_count、evidence_count、linked_asset_ids、linked_action_ids 或 recommended_topic_action。
5. 合同没有 proposal_hint 或 rollback_hint。
6. 合同把 proposal 编辑工作区、搜索复盘或 Data Map 冒充为本 phase 已完成。
7. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 7. 通过条件

Stage 1 Phase 4 通过时必须有：

1. `docs/product/topic_classification_detail_contract.md`。
2. `docs/acceptance/topic_classification_detail_acceptance.md`。
3. `validate:v1.1.6-stage1-phase4`。
4. 三文件和模型参数记录中登记 `MA-V116-S1P04`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 8. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
