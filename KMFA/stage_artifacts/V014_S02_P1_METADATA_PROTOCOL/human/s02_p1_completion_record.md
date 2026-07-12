# KMFA v0.1.4 S02-P1 metadata目录协议

## 结论

- task_id: `KMFA-V014-S02-P1-METADATA-PROTOCOL-20260703`
- status: `completed_validated_local_only_no_go_upload_deferred`
- scope: 只锁定 metadata 目录协议、五类核心标识符、公开仓库可保存类别、raw/private 边界和本 phase validator。
- evidence_dir: `KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/`

## 已完成

- 复用并验证既有七类 metadata 目录：`sources`, `imports`, `schema_maps`, `quality`, `lineage`, `reports`, `approvals`。
- 复用并验证五类核心标识符协议：`import_run_id`, `source_id`, `file_hash`, `formula_version`, `mapping_version`。
- 新增 `KMFA/metadata/protocol/raw_data_roots_v1_4.json`，把 `/Users/linzezhang/Downloads/KMFA_MetaData` 锁为 raw/private inbox，只允许在后续明确授权 phase 中只读使用；本 phase 未读取、未列出、未盘点、未修改。
- 新增 v1.4 S02-P1 validator 与 focused unit test，绑定 Stage 1 review dependency、metadata protocol check、raw boundary、no-upload/no-go 和证据完整性。

## 未执行

- 未读取、列出、修改、删除、移动、重命名、覆盖或写入 `/Users/linzezhang/Downloads/KMFA_MetaData`。
- 未执行 raw inventory、raw value matching、字段或表头抽取、row value 抽取、S02-P2、S02-P3、Stage 2 review、GitHub upload、正式报告、live connector、OpMe 深度耦合或业务执行。
- 未提交 raw business data、ZIP、Excel、PDF、私有 CSV、SQLite/db、raw 文件名、raw hash、字段/表头明文、row values、真实金额、credentials、银行流水、合同、薪资或税务材料。

## 下一步

下一轮只能执行 `v0.1.4 S02-P2｜不可污染原则 / immutability policy`，不得跳到 S02-P3、Stage 2 review、raw inventory、GitHub upload、正式报告或业务执行。
