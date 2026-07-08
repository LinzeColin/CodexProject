# 行为智能模型

用于放置 facets、semantic clusters、latent signals、collaboration quality、自我迭代和
低价值循环识别的模型配置。

当前 S05 P3 已完成：facet/canonical events 的数据契约已定义在
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

下一步是 S05 Review。
