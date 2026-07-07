# 同步与备份

用于放置 ChatGPT、Codex、后续其他 agent 的 source registry、同步模式、公开备份策略、
raw append-only 规则和 credential boundary。

当前 S02 P1 只定义数据源模型。模型位于
`../数据契约/source_data_model.v1_2_s02_p1.json`，覆盖 ChatGPT、Codex、后续其他 agent。

source registry 属于 S02 P2；本阶段不创建 `sync_source_registry.json`，不实现 connector，
不写 raw archive。
