# 数据契约

用于放置 source、raw、derived、reports、visualization、proposal 和 apply 相关数据契约。

当前 S02 P1 定义 source data model：

- `source_data_model.v1_2_s02_p1.json`
- 必填字段：`source_id`、`source_type`、`agent_name`、`raw_root`、
  `sync_mode`、`public_backup_mode`、`connector_capability`
- 支持 source_type：`chatgpt`、`codex`、`other_agent`
- 每个 source 必须区分 transcript 与 credential

source registry 属于 S02 P2；本阶段不创建 registry 文件，不修改 raw archive。

当前 S06 P1 已完成。S05 Review 已通过，并新增：

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
保留中文摘要、代表事件和 `evidence_refs`。下一步是 S06 P2。
