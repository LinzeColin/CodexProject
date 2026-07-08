# 行为智能模型

用于放置 facets、semantic clusters、latent signals、collaboration quality、自我迭代和
低价值循环识别的模型配置。

当前 S06 Review 已完成。facet/canonical events 的数据契约已定义在
`机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`，中文解释位于
`人类可读/12_Facet字段与事件语义说明.md`，facet extractor 已实现为
`scripts/extract_memory_atlas_facets.py`，并为 events 输出补齐
`lightweight_evidence_refs`。

S05 P1 只定义 facets 和 canonical events schema，不实现 extractor，不生成
`data/derived/behavior_intelligence/events.json`，不生成 fake events，不修改 raw。

S05 P2 已生成 `data/derived/behavior_intelligence/events.json`。当前 extractor 从
public raw、processed manifest 和 derived snapshot 中抽取事件；缺失来源只写
source_status missing reason，不生成 fake events，不修改 raw，不改变首屏 UI。

S05 P3 在每条 event 中保留 `source_id`、`record_id` 和 `evidence_refs`，证据引用
只指向 raw、manifest、derived 或 missing reason，不实现 Raw-to-Insight Replay UI。
S05 P3 仍不生成 fake events，不修改 raw，不改变首屏 UI。

S05 Review 已通过，确认行为事件与 facets 可被后续 cluster、ROI、latent、visualization
复用。

S06 P1 已完成：`scripts/build_memory_atlas_clusters.py` 从
`data/derived/behavior_intelligence/events.json` 生成
`data/derived/behavior_intelligence/clusters.json`。输出包含主题簇和层级簇，每个
cluster 均保留中文摘要、代表事件、`source/time/project/task/language` 过滤维度和
`evidence_refs`。S06 P1 不识别低价值循环，不生成机会卡片。

当前 S06 P2 已完成：`scripts/build_memory_atlas_low_value_loops.py` 从 events 和
clusters 生成 `data/derived/behavior_intelligence/low_value_loops.json`。输出包含
低价值循环候选、Decision Debt Ledger 和 Action Half-Life，覆盖重复返工、反复讨论未落地、
过度优化和 scope creep。S06 P2 不做心理诊断，不生成 opportunity cards。

当前 S06 P3 已完成：`scripts/build_memory_atlas_opportunities.py` 从 events、clusters
和 low-value loops 生成 `data/derived/behavior_intelligence/opportunities.json`。输出包含
机会发现候选和 why-not-now 卡片，覆盖 automation、productization、template、
compounding 和 defer。S06 P3 不接外部经济数据库，不做心理诊断，不生成无穷压力清单。

当前 S06 Review 已完成：`scripts/build_memory_atlas_data.py` 将主题簇、低价值循环和
机会线索汇总为 `data/derived/visualization/memory_atlas.json` 的
`behavior_intelligence`。Memory Atlas 首页可显示有证据的主题簇、低价值循环和机会线索。
下一步是 S07 P1。
