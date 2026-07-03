# KMFA Immutability Policy

product_version: `0.1.4-s02p2-immutability-policy`
stage_phase: `S02-P2`
status: `active`

## Purpose

S02-P2 建立不可污染原则。当前只实现协议、schema、空事件流和检查器，不导入原始文件，不读取或保存原始经营明细，不生成业务报告。

## v0.1.4 Raw Inbox Guard

本机 raw/private inbox 固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`。v0.1.4 S02-P2 只锁定不可污染协议，不读取、列出、盘点、修改、删除、移动、重命名、覆盖或写入该目录。公开仓库只保存协议、状态、聚合计数、validator 结果和证据索引；不得提交 raw 文件、raw 文件名、raw hash、字段/表头明文、sheet 名、ZIP member 名、row/cell values、业务金额或业务值。

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
- 不上传 GitHub；v1.4 GitHub main upload 延期到 Stage 1-18 全部完成、整体复审通过并修复 findings 后一次性执行。
