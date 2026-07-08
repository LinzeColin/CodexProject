# 行为智能模型

用于放置 facets、semantic clusters、latent signals、collaboration quality、自我迭代和
低价值循环识别的模型配置。

当前 S05 P1 已完成：facet/canonical events 的数据契约已定义在
`机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`，中文解释位于
`人类可读/12_Facet字段与事件语义说明.md`。

S05 P1 只定义 facets 和 canonical events schema，不实现 extractor，不生成
`data/derived/behavior_intelligence/events.json`，不生成 fake events，不修改 raw。

下一步是 S05 P2：实现或扩展 facet extractor。
