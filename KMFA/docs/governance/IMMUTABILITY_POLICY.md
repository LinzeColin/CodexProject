# KMFA Immutability Policy

product_version: `0.1.0-s02p2`
stage_phase: `S02-P2`
status: `active`

## Purpose

S02-P2 建立不可污染原则。当前只实现协议、schema、空事件流和检查器，不导入原始文件，不读取或保存原始经营明细，不生成业务报告。

## Raw Manifest Rule

`raw_file_manifest` 只能登记外部原始文件的索引信息：

- `import_run_id`
- `source_id`
- `file_hash`
- `file_size_bytes`
- `storage_ref`
- `original_filename_hash`
- `received_at`
- `manifest_status`
- `evidence_ref`

禁止登记：

- 原始文件 bytes
- 原始文件全文
- PDF/Excel 明细行全文
- 原始抽取值
- 银行账号、身份证号、工资、合同正文、税务申报明文

一旦写入 manifest，`file_hash`、`source_id`、`import_run_id`、`storage_ref`、`original_filename_hash` 不可原地修改。后续纠错必须追加新 manifest 记录或 resolution event。

## Derived Data Version Rule

派生数据必须以版本记录保存：

- `derived_dataset_id`
- `derived_version`
- `source_refs`
- `formula_version`
- `mapping_version`
- `lineage_ref`
- `status`
- `invalidated_by_event_id`
- `rerun_of_version`
- `evidence_ref`

派生数据可以失效、重跑、对比，但不能覆盖旧版本；任何重跑必须保留旧版本和新的 lineage。

## Frontend Write Boundary

前端和人工工作台不得直接写 raw 层。允许写入：

- `control_event`
- `mapping_rule`
- `resolution_event`
- `approval_event`
- `comment`

禁止写入：

- `raw_file_manifest` 的不可变字段
- 原始文件 bytes
- 原始抽取值
- 业务金额事实层
- 任何敏感明文字段

前端操作必须追加事件，不得静默改写历史事件。

## S02-P2 Non-goals

- 不实现真实文件导入。
- 不实现 raw manifest 写入服务。
- 不实现派生数据计算。
- 不实现 Q0-Q5 或 A/B/C/D 报告等级；这是 S02-P3。
- 不上传 GitHub；Stage 2 完成并复审修复后再整体上传。
