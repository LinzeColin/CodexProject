# Memory Atlas 主题分类明细合同

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 4

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑或长期记忆。

## 1. 目标

Stage 1 Phase 4 解决“主题分类只能看到摘要，看不到具体明细”的问题。记忆总览里的主题分类摘要必须能展开为用户可判断、可追溯、可调整的主题明细。

本 phase 只定义主题分类明细模型合同，不实现 proposal 编辑工作区、Search 2.0、复盘、总结迭代、Data Map 或浏览器截图。

## 2. 主题分类定义

主题分类是对长期记忆、层级资产、建议动作和时间河事件的语义聚合。它不是 tag 列表，也不是数据库字段直出。每个主题都必须说明：

1. 主题是什么。
2. 主题当前强度是多少。
3. 主题是在增强、衰退、新生、冲突还是稳定。
4. 判断置信度是多少。
5. 关联记录、证据、资产和建议动作有哪些。
6. 用户下一步应该继续投入、复盘、整合、验证、降噪还是观察。

## 3. 主题状态类型

| topic_state | 中文名 | 说明 | 默认用户动作 |
|---|---|---|---|
| `dominant` | 主导主题 | 当前最强、最影响系统判断的主题 | 查看证据并确认是否继续投入 |
| `rising` | 增强主题 | 近期强度或活动正在上升 | 继续投入或设置复盘窗口 |
| `declining` | 衰退主题 | 近期关注下降、资产冷却或证据减少 | 判断是否归档、复活或降权 |
| `emerging` | 新生主题 | proto-star、早期机会或潜在新方向 | 建立验证任务 |
| `conflict` | 冲突主题 | 证据、决策或行动建议之间存在冲突 | 打开 Inspector 做复盘 |
| `black_hole` | 低价值循环 | 重复消耗、低 ROI 或高摩擦主题 | 降噪、设约束或生成 proposal |
| `stale` | 过期主题 | 长期未维护、低置信或需复核主题 | 复核、隐藏、降权或重新验证 |

## 4. 必备字段

每个主题分类明细必须包含以下字段：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `topic_id` | required | 稳定 ID，供 Inspector、星系、时间河、搜索和 proposal 引用 |
| `topic_label` | required | 中文短标签，建议不超过 18 个中文字符 |
| `topic_state` | required | `dominant` / `rising` / `declining` / `emerging` / `conflict` / `black_hole` / `stale` |
| `topic_strength` | required | 主题强度，建议 0-1 或 low/medium/high |
| `trend` | required | `up` / `down` / `flat` / `new` / `volatile` |
| `confidence` | required | `high` / `medium` / `low` |
| `record_count` | required | 关联脱敏记录数量 |
| `evidence_count` | required | 脱敏证据数量 |
| `evidence_refs` | required | redacted evidence 或 Inspector 引用 |
| `source_scope` | required | 总数据源 / ChatGPT / Codex |
| `linked_asset_ids` | required | 关联层级资产 |
| `linked_action_ids` | required | 关联建议动作 |
| `linked_starfield_cluster_id` | optional | 关联记忆星系 cluster |
| `linked_river_range` | optional | 关联记忆时间河窗口 |
| `related_topic_ids` | optional | 相关主题 |
| `matched_reason` | required | 为什么归入该主题，必须人类可读 |
| `recommended_topic_action` | required | `continue` / `review` / `consolidate` / `validate` / `defer` / `watch` |
| `proposal_hint` | required | 是否建议生成 proposal-only 调整 |
| `rollback_hint` | required | 如果后续调整被应用，如何撤回或复核 |

## 5. 展开顺序

主题分类明细默认按以下顺序展示：

1. dominant。
2. rising。
3. emerging。
4. conflict。
5. black_hole。
6. declining。
7. stale。

在每个 topic_state 内，默认排序优先考虑：

1. topic_strength 高。
2. trend 为 up/new/volatile。
3. confidence 不低于 medium。
4. record_count 和 evidence_count 足够。
5. 与当前 source scope、time range、selection focus 相关。

## 6. Inspector 交接

点击主题分类必须同步 Inspector，并至少显示：

- topic_id、topic_label 和 topic_state。
- topic_strength、trend、confidence。
- record_count、evidence_count 和 redacted evidence_refs。
- linked_asset_ids。
- linked_action_ids。
- linked_starfield_cluster_id。
- linked_river_range。
- related_topic_ids。
- matched_reason。
- recommended_topic_action。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 7. Proposal-only 边界

主题分类明细可以建议用户调整 topic_category、importance、priority、hidden_until、stale_override 或 confidence_note，但前端只能生成 proposal draft，不能直接修改：

- active memory。
- topic_category。
- importance。
- priority。
- memory_tier。
- GitHub 数据。

真正 apply 必须由 agent/human 在前端之外重新读库、冲突检查、写 history 并保留 rollback。

## 8. 与其他 phase 的边界

本 phase 不覆盖：

- Proposal-only 编辑 schema。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- 运行时 UI 实现或 Playwright 截图。

这些内容必须在后续 phase 或 stage 单独交付和验收。

## 9. 验收

Stage 1 Phase 4 通过条件：

1. 合同明确主题分类不是 tag 列表，而是可解释、可追溯、可调整的语义聚合。
2. 合同覆盖 dominant、rising、declining、emerging、conflict、black_hole、stale 七类主题状态。
3. 合同覆盖 topic_strength、trend、confidence、record_count、evidence_count、linked assets、linked actions、matched reason、recommended topic action、proposal hint 和 rollback hint。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 10. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
