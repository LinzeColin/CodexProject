# KMFA v0.1.4 S02-P2 Risk Register

| Risk | Control |
|---|---|
| 误读或误写 raw/private inbox | 本 phase 不读取、不列出、不盘点 `/Users/linzezhang/Downloads/KMFA_MetaData`；validator 只检查 public-safe 协议文件和证据。 |
| raw manifest 被当作业务导入服务 | S02-P2 只锁定登记规范和不可变字段，不实现 raw manifest 写入服务，不登记真实业务文件。 |
| 派生重跑覆盖旧版本 | `derived_data_policy` 和 validator 强制 `append_only=true`、`overwrite_old_version_allowed=false`。 |
| 前端或人工工作台绕过事件模型直接写 raw 层 | `control_event_policy` 和 validator 强制 `raw_layer_write_allowed=false`，禁止 target raw、raw manifest immutable fields 和 original extracted values。 |
| S02-P2 被误认为 Stage 2 完成或可上传 | manifest 和证据明确 `s02_p3_started=false`、`stage2_review_performed=false`、`github_upload_performed=false`。 |
