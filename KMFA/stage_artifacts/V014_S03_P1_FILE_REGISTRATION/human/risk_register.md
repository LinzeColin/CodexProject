# KMFA v0.1.4 S03-P1 Risk Register

| Risk | Status | Control |
|---|---|---|
| raw root 只读扫描被误实现成写入或缓存生成 | controlled | 工具只写 `KMFA/.codex_private_runtime/`、`KMFA/metadata/` 和 `KMFA/stage_artifacts/`；validator 要求 raw root write/delete/move/rename/overwrite 均为 false。 |
| raw 文件明细或内容 hash 被提交到公开仓库 | controlled | private manifest 保存在 `.codex_private_runtime/`；公开 manifest 只保留 private ref、类型、大小和聚合计数；validator 扫描公开证据。 |
| zip 支持被误解为已解包真实 raw 包 | controlled | 本 phase 仅证明安全解包能力和策略，manifest 要求 `safe_zip_extract_performed=false`。 |
| S03-P1 被扩展为字段映射或 raw value matching | controlled | phase scope 明确 `field_mapping_performed=false`、`raw_value_matching_performed=false`，下一步限定 S03-P2。 |
| 提前触发 Stage 3 review 或 GitHub upload | controlled | manifest、completion record 和 validator 均要求 `stage3_review_performed=false`、`github_upload_performed=false`；v1.4 upload 延后到 Stage 1-18 全部完成后统一执行。 |
