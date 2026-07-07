# 数据契约

用于放置 source、raw、derived、reports、visualization、proposal 和 apply 相关数据契约。

当前 S02 P1 定义 source data model：

- `source_data_model.v1_2_s02_p1.json`
- 必填字段：`source_id`、`source_type`、`agent_name`、`raw_root`、
  `sync_mode`、`public_backup_mode`、`connector_capability`
- 支持 source_type：`chatgpt`、`codex`、`other_agent`
- 每个 source 必须区分 transcript 与 credential

source registry 属于 S02 P2；本阶段不创建 registry 文件，不修改 raw archive。
