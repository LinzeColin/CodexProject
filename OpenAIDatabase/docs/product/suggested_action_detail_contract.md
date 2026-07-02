# Memory Atlas 建议动作明细合同

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 2

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑或长期记忆。

## 1. 目标

Stage 1 Phase 2 解决“建议动作看不到明细”的问题。记忆总览里的建议动作不能只是短句列表，必须能展开为用户可判断、可追溯、可调整的行动解释。

本 phase 只定义建议动作明细合同，不实现层级资产明细、主题分类明细、proposal 编辑工作区、搜索复盘、Data Map 或浏览器截图。

## 2. 建议动作定义

建议动作是从 Universe State、Memory Weather、低价值循环、新生机会、ROI leverage、staleness 和用户当前 source scope 派生的 action candidate。它是 proposal-ready 的行动建议，不是直接写长期记忆的命令。

每条建议动作必须回答：

1. 为什么现在建议做这件事。
2. 预期 ROI 是什么。
3. 努力成本是多少。
4. 紧急度是多少。
5. 有哪些脱敏证据。
6. 下一步具体怎么做。
7. 不做或延后有什么风险。
8. 是否需要生成 proposal。

## 3. 必备字段

每条建议动作明细必须包含以下字段：

| 字段 | 必须性 | 说明 |
|---|---|---|
| `action_id` | required | 稳定 ID，便于 Inspector、搜索、复盘和 proposal 引用 |
| `title` | required | 中文短标题，建议不超过 18 个中文字符 |
| `action_type` | required | `continue` / `review` / `consolidate` / `explore` / `defer` |
| `reason` | required | 为什么建议做，必须是人类可读解释 |
| `roi_score` | required | ROI 或 leverage 的相对值，可来自现有模型或后续参数 |
| `effort_cost` | required | `low` / `medium` / `high`，解释执行成本 |
| `urgency` | required | `now` / `this_week` / `later` / `watch` |
| `confidence` | required | `high` / `medium` / `low`，说明判断可靠性 |
| `evidence_count` | required | 脱敏证据数量，不显示 raw text |
| `evidence_refs` | required | 指向 redacted evidence 或 Inspector 引用 |
| `source_scope` | required | 总数据源 / ChatGPT / Codex |
| `linked_theme_ids` | required | 关联主题或 cluster |
| `linked_asset_ids` | optional | 关联层级资产，具体资产模型进入后续 phase |
| `next_step` | required | 用户可执行的下一步 |
| `proposal_hint` | required | 是否建议进入 proposal-only 调整 |
| `rollback_hint` | required | 如果 proposal 后续被应用，如何撤回或复核 |

## 4. 动作类型

| action_type | 使用场景 | 默认下一步 |
|---|---|---|
| `continue` | 高 ROI、低阻力、趋势增强 | 继续投入并设置复盘窗口 |
| `review` | 低价值循环、冲突、过期或置信度下降 | 打开 Inspector 证据并做复盘 |
| `consolidate` | 分散记忆、重复主题、可沉淀工作流 | 合并为项目、规则或能力记录 |
| `explore` | 新生机会、proto-star 或潜在方向 | 建立验证任务或观察窗口 |
| `defer` | 噪音、低 ROI、暂不值得投入 | 暂缓、隐藏或降低优先级 proposal |

## 5. 排序与显示原则

建议动作默认排序应优先考虑：

1. ROI / leverage 高。
2. effort_cost 低。
3. urgency 高。
4. confidence 不低于 medium。
5. 与当前 source scope、time range 和 focus 相关。

首页只显示精简摘要；展开层或 Inspector 显示完整 reason、ROI、努力成本、紧急度、证据和下一步。任何长解释不得塞进表格或卡片正文。

## 6. Inspector 交接

点击建议动作必须同步 Inspector，并至少显示：

- action_id 和标题。
- reason。
- ROI / leverage 解释。
- effort_cost 与 urgency。
- confidence。
- evidence_count 和 redacted evidence_refs。
- linked themes。
- next_step。
- proposal_hint。
- rollback_hint。

Inspector 不得显示 raw transcript、plaintext secret、cookie/session、本地绝对私有路径或未脱敏证据全文。

## 7. Proposal-only 边界

建议动作可以建议进入 proposal-only 调整，但不能直接修改：

- active memory。
- importance。
- priority。
- topic_category。
- action_status。
- due_window。
- hidden_until。
- GitHub 数据。

如果用户要调整，前端只能生成 proposal draft。真正 apply 必须由 agent/human 重新读库、冲突检查、写 history 并保留 rollback。

## 8. 与其他 phase 的边界

本 phase 不覆盖：

- 层级资产完整模型。
- 主题分类完整模型。
- Proposal-only 编辑 schema。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- 运行时 UI 实现或 Playwright 截图。

这些内容必须在后续 phase 或 stage 单独交付和验收。

## 9. 验收

Stage 1 Phase 2 通过条件：

1. 合同明确建议动作不是短句列表，而是可展开、可追溯、proposal-ready 的行动解释。
2. 合同覆盖 reason、ROI、effort cost、urgency、evidence、next step、proposal hint 和 rollback hint。
3. 合同定义 `continue`、`review`、`consolidate`、`explore`、`defer` 五类动作。
4. 合同定义 Inspector 交接内容和 raw/private 安全边界。
5. 合同明确 proposal-only，不直接写长期记忆。
6. 验收文件提供字段检查、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 10. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
