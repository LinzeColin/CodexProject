# Memory Atlas 层级资产明细合同

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 3

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑或长期记忆。

## 1. 目标

Stage 1 Phase 3 解决“层级资产只能看到摘要，看不到具体明细”的问题。记忆总览里的层级资产摘要必须能展开为用户可判断、可追溯、可调整的资产明细。

本 phase 只定义层级资产明细模型合同，不实现主题分类完整模型、proposal 编辑工作区、搜索复盘、Data Map 或浏览器截图。

## 2. 层级资产定义

层级资产是长期记忆中可被系统用于判断、行动和复盘的结构化资产。它不是原始记录列表，也不是内部数据库字段直出。每个资产都必须能说明：

1. 它属于哪个资产层级。
2. 它为什么重要。
3. 它当前是否仍有效。
4. 它来自哪些脱敏证据。
5. 它与哪些建议动作、主题、时间河事件或 proposal 相关。
6. 用户下一步应该保留、复盘、整合、降权、重新验证还是暂缓。

## 3. 资产层级

| tier | 中文名 | 说明 | 默认用户动作 |
|---|---|---|---|
| `core_profile` | 核心画像 | 长期稳定的偏好、身份、工作方式、边界和高价值规则 | 保留高权重，必要时通过 proposal 修正 |
| `project` | 项目 | 正在推进或历史上仍有参考价值的项目、阶段和目标 | 关联时间河和建议动作 |
| `decision` | 决策 | 已做出的选择、取舍、授权、停止条件或边界 | 检查是否仍有效 |
| `workflow` | 工作流 | 可复用流程、检查清单、执行规范或验收方式 | 整合为可执行 SOP |
| `knowledge` | 知识 | 可复用概念、事实、技术、研究或经验 | 连接主题和证据 |
| `opportunity` | 机会 | proto-star、新方向、潜在项目、可验证兴趣或能力增长点 | 建立验证窗口 |
| `stale` | 过期/待复核 | 过期、低置信、冲突、长期未维护或可能应降权的资产 | 复盘、降权、隐藏或重新验证 |

## 4. 必备字段

每个层级资产明细必须包含以下字段：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `asset_id` | required | 稳定 ID，供 Inspector、搜索、时间河、星系和 proposal 引用 |
| `asset_tier` | required | `core_profile` / `project` / `decision` / `workflow` / `knowledge` / `opportunity` / `stale` |
| `title` | required | 中文短标题，建议不超过 18 个中文字符 |
| `summary` | required | 两行内人类可读摘要 |
| `importance` | required | `high` / `medium` / `low` |
| `priority` | required | `p0` / `p1` / `p2` / `p3` / `watch` |
| `confidence` | required | `high` / `medium` / `low` |
| `staleness_status` | required | `current` / `needs_review` / `stale` / `unknown` |
| `evidence_count` | required | 脱敏证据数量 |
| `evidence_refs` | required | redacted evidence 或 Inspector 引用 |
| `source_scope` | required | 总数据源 / ChatGPT / Codex |
| `linked_action_ids` | required | 关联建议动作 |
| `linked_theme_ids` | optional | 关联主题，完整主题分类模型进入后续 phase |
| `linked_time_range` | optional | 关联时间河窗口 |
| `recommended_asset_action` | required | `keep` / `review` / `consolidate` / `lower_priority` / `validate` / `defer` |
| `proposal_hint` | required | 是否建议生成 proposal-only 调整 |
| `rollback_hint` | required | 如果后续调整被应用，如何撤回或复核 |

## 5. 展开顺序

层级资产明细默认按以下顺序展示：

1. 核心画像。
2. 当前项目。
3. 决策。
4. 工作流。
5. 知识。
6. 机会。
7. stale / 待复核。

在每个 tier 内，默认排序优先考虑：

1. importance 高。
2. priority 高。
3. staleness_status 需要复核。
4. evidence_count 足够。
5. 与当前 source scope、time range、selection focus 相关。

## 6. Inspector 交接

点击层级资产必须同步 Inspector，并至少显示：

- asset_id、asset_tier 和标题。
- summary。
- importance、priority、confidence、staleness_status。
- evidence_count 和 redacted evidence_refs。
- linked_action_ids。
- linked_theme_ids 或后续主题分类入口。
- linked_time_range。
- recommended_asset_action。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 7. Proposal-only 边界

层级资产明细可以建议用户调整 importance、priority、action_status、hidden_until、stale_override 或 confidence_note，但前端只能生成 proposal draft，不能直接修改：

- active memory。
- memory_tier。
- importance。
- priority。
- topic_category。
- GitHub 数据。

真正 apply 必须由 agent/human 在前端之外重新读库、冲突检查、写 history 并保留 rollback。

## 8. 与其他 phase 的边界

本 phase 不覆盖：

- 主题分类完整模型。
- Proposal-only 编辑 schema。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- 运行时 UI 实现或 Playwright 截图。

这些内容必须在后续 phase 或 stage 单独交付和验收。

## 9. 验收

Stage 1 Phase 3 通过条件：

1. 合同明确层级资产不是原始记录列表，而是可解释、可追溯、可调整的结构化资产。
2. 合同覆盖 core_profile、project、decision、workflow、knowledge、opportunity、stale 七类资产。
3. 合同覆盖 asset_id、asset_tier、summary、importance、priority、confidence、staleness_status、evidence、linked actions、recommended asset action、proposal hint 和 rollback hint。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 10. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
