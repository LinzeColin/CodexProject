# 同步与备份

用于放置 ChatGPT、Codex、后续其他 agent 的 source registry、同步模式、公开备份策略、
raw append-only 规则和 credential boundary。

当前 S02 P2 已建立 source registry：

- `sync_source_registry.json`
- 依赖的 source data model：`../数据契约/source_data_model.v1_2_s02_p1.json`
- ChatGPT browser connector + official export fallback
- Codex local sync
- future_agent_template / other_agent / future_agent_adapter

S02 P3 才能创建人类同步说明页。当前阶段不实现 connector，不写 raw archive。
