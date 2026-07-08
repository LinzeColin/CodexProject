# 数据契约

用于放置 source、raw、derived、reports、visualization、proposal 和 apply 相关数据契约。

当前 S02 P1 定义 source data model：

- `source_data_model.v1_2_s02_p1.json`
- 必填字段：`source_id`、`source_type`、`agent_name`、`raw_root`、
  `sync_mode`、`public_backup_mode`、`connector_capability`
- 支持 source_type：`chatgpt`、`codex`、`other_agent`
- 每个 source 必须区分 transcript 与 credential

source registry 属于 S02 P2；本阶段不创建 registry 文件，不修改 raw archive。

当前 S07 P3 已完成。S05 Review 已通过，并新增：

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`
- `人类可读/12_Facet字段与事件语义说明.md`
- `docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `scripts/extract_memory_atlas_facets.py`
- `data/derived/behavior_intelligence/events.json`
- `docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md`
- `docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md`
- `docs/reviews/memory_atlas_v1_2_s05_review.md`
- `scripts/build_memory_atlas_clusters.py`
- `data/derived/behavior_intelligence/clusters.json`
- `人类可读/13_行为簇与层级簇说明.md`
- `docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md`
- `scripts/build_memory_atlas_low_value_loops.py`
- `data/derived/behavior_intelligence/low_value_loops.json`
- `人类可读/14_低价值循环与DecisionDebt说明.md`
- `docs/reviews/memory_atlas_v1_2_s06_p2_low_value_loops.md`
- `scripts/build_memory_atlas_opportunities.py`
- `data/derived/behavior_intelligence/opportunities.json`
- `人类可读/15_机会发现与为什么不是现在卡片.md`
- `docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md`
- `data/derived/visualization/memory_atlas.json`
- `docs/reviews/memory_atlas_v1_2_s06_review.md`
- `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `scripts/build_memory_atlas_economic_proxy.py`
- `data/derived/economic_proxy/personal_economic_proxy.json`
- `人类可读/16_PersonalEconomicProxy公式说明.md`
- `docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md`
- `机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- `机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- `scripts/build_memory_atlas_information_roi.py`
- `data/derived/information_roi/information_roi_gate.json`
- `人类可读/17_InformationROI与VisualROIGate说明.md`
- `docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md`
- `机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- `scripts/build_memory_atlas_formula_what_if.py`
- `data/derived/economic_proxy/formula_what_if_preview.json`
- `人类可读/18_FormulaWhatIf配置预览说明.md`
- `docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`

S05 P1 定义 facet/canonical event schema：`source`、`topic`、`intent`、
`task_type`、`project`、`output_type`、`language`、`tool`、`turn_count`、
`friction`、`value_signal` 和 `future_agent_source`。字段名保持英文，中文解释在
人类文件中说明。

下一步是 S05 P2：实现 extractor。S05 P1 不生成 fake events，不写
`data/derived/behavior_intelligence/events.json`，不修改 raw。

S05 P2 实现 extractor 后，`events.json` 当前覆盖 ChatGPT、Codex 和
future_agent source_status。ChatGPT 与 Codex 从 processed manifest 抽取；future_agent
当前无 public raw，因此 `source_status.future_agent.missing_reason` 记录缺失原因而不生成
fake events。

S05 P3 在 `events.json` 内补齐轻量 `evidence_refs`。每条 event 必须保留
`source_id`，并通过 `raw_ref`、`manifest_ref`、`derived_ref` 或
`evidence_missing_reason` 形成可追溯证据引用。当前 ChatGPT/Codex 事件主要使用
`manifest_ref` 和 missing reason；future_agent 当前仍只记录 source_status missing reason，
不生成 fake events。

S05 Review 复审确认 canonical event 可覆盖 ChatGPT/Codex/future agent，且
`evidence_refs`、`source_id`、`manifest_ref` 和 missing reason 足以支撑后续
cluster、ROI、latent、visualization 复用。

S06 P1 生成 `data/derived/behavior_intelligence/clusters.json`。该输出包含主题簇和
层级簇，固定 `source/time/project/task/language` 过滤合同，并要求每个 cluster
保留中文摘要、代表事件和 `evidence_refs`。

S06 P2 生成 `data/derived/behavior_intelligence/low_value_loops.json`。该输出包含
低价值循环候选、Decision Debt Ledger 和 Action Half-Life，覆盖重复返工、反复讨论未落地、
过度优化和 scope creep 四类候选。每条候选、Decision Debt 和 Action Half-Life 都必须有
`evidence_refs`，并保持候选语气。

S06 P3 生成 `data/derived/behavior_intelligence/opportunities.json`。该输出包含
候选机会和 为什么不是现在 卡片，覆盖 automation、productization、template、
compounding 和 defer 五类机会线索。每条机会都必须有 `evidence_refs`、`next_step_zh`、
半衰期或暂缓理由，并保持 candidate only，不形成无穷压力清单。

S06 Review 将 S06 P1/P2/P3 的派生结果汇总进
`data/derived/visualization/memory_atlas.json` 的 `behavior_intelligence`。该展示合同只保留
计数、中文摘要、有限证据引用、代表事件、下一步和 why-not-now 摘要，不修改 raw，也不把完整
行为智能输出复制到前端。下一步是 S07 P1。

S07 P1 生成 `data/derived/economic_proxy/personal_economic_proxy.json`。该输出包含
`score_cards`、`formula_registry`、`parameters` 和 `external_economic_database`
占位字段。每个 score card 必须包含中文解释、公式来源、参数引用和证据引用。
本阶段不接入外部经济数据库，不做精确收入预测，不实现 S07 P2 信息 ROI gate，也不实现
S07 P3 what-if UI。下一步是 S07 P2。

S07 P2 生成 `data/derived/information_roi/information_roi_gate.json`。该输出包含
`roi_items`、`roi_summary`、`visual_roi_gate`、`formula_registry`、`parameters`
和 `phase_boundary`。`roi_items` 覆盖 insight、card、chart 三类内容；P0 chart 必须
通过 `visual_roi_gate`，并绑定 human question、action 和 evidence refs。没有决策价值的图表
不进 P0。本阶段不接入外部经济数据库，不做精确收入预测，不实现 S07 P3 what-if UI，
不修改运行时 UI，也不修改 raw。下一步是 S07 P3。

S07 P3 生成 `data/derived/economic_proxy/formula_what_if_preview.json`。该输出包含
`scenarios`、`adjustable_weights`、`parameter_change_proposal`、`formulas`、
`parameters` 和 `phase_boundary`。Formula What-if 只做配置预览，支持查看时间节省、
复用价值、机会价值、长期复利、自动化增强、返工成本和低价值循环惩罚等权重假设。
所有 scenario 都必须保留公式来源、参数引用和中文说明，且
`active_config_write=false`、`proposal_required_before_apply=true`。本阶段不接入外部
经济数据库，不做精确收入预测，不提供财务建议，不修改 raw，不修改运行时 UI。
下一步是 S07 Review。
