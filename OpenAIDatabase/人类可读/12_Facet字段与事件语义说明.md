# 12 Facet 字段与事件语义说明

## 结论

S05 P1 已定义 Memory Atlas v1.2 的 facet schema。它只定义事件语义字段，
不抽取真实事件、不生成 `events.json`、不修改 raw，也不把机器字段堆到首屏。

任务 ID 为 `MA-V12-S05P1`，验收 ID 为 `ACC-MA-V12-S05P1`，状态为
`phase_s05_p1_facet_schema_completed_pending_s05_p2`。

机器契约文件是 `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`。
下一步是 S05 P2：实现 extractor。

## 字段解释

| 字段 | 中文含义 | 用途 |
|---|---|---|
| `source` | 事件来自哪个 agent 或同步来源。 | 区分 ChatGPT、Codex、future agent 或其他 agent。 |
| `topic` | 这条事件讨论的主题。 | 后续用于主题簇和趋势。 |
| `intent` | 用户或 agent 的主要意图。 | 区分计划、构建、调试、复审、研究、写作、运维、决策和交接。 |
| `task_type` | 任务所属类型。 | 后续用于行为簇、ROI 和低价值循环识别。 |
| `project` | 事件所属项目；无法判断时允许为空。 | 支持按项目聚合和过滤。 |
| `output_type` | 这次工作主要产出了什么。 | 支持按代码、文档、配置、数据、报告、测试等产物分析。 |
| `language` | 事件主要使用的语言。 | 支持中文、英文、混合和其他语言区分。 |
| `tool` | 事件最关键的工具或运行表面。 | 帮助分析 Codex、ChatGPT、terminal、browser、GitHub 等工具使用。 |
| `turn_count` | 围绕这件事发生了多少轮交互。 | 作为复杂度、摩擦和协作成本的轻量 proxy。 |
| `friction` | 阻力、卡点、返工或不确定性信号。 | 后续用于低价值循环和风险识别。 |
| `value_signal` | 价值信号，例如节省时间、复用、降低风险、形成决策。 | 后续用于信息 ROI 和机会发现。 |
| `future_agent_source` | 后续其他 agent 的来源描述；ChatGPT/Codex 可为空。 | 保留 future agent 接入能力。 |

## 人类阅读边界

这些字段是机器抽取和分析的底层语义，不是首屏展示文案。后续界面应该显示中文结论、
变化、证据和行动，而不是直接展示 schema 字段堆。

## 停止条件

- extractor 为缺失数据生成假记录时停止。
- 人类 UI 直接展示 schema 字段堆时停止。
- event 完全缺少 evidence ref 或缺失原因时停止。

## 下一步

下一步只允许进入 S05 P2：实现或扩展 facet extractor。S05 P2 之前不得生成真实
`data/derived/behavior_intelligence/events.json`。
