# KMFA Metadata Protocol

product_version: `0.1.4-s02p1-metadata-protocol`
stage_phase: `S02-P1`
status: `active`

## Purpose

S02-P1 建立 metadata 目录协议。当前只定义目录、标识符、文件形态、raw/private 根目录协议和隐私边界，不导入任何原始经营数据，不解析业务金额，不生成正式报告。

## Required Directories

| Directory | Purpose | Public repo rule |
|---|---|---|
| `KMFA/metadata/sources/` | 来源系统和来源别名登记 | 只保存 `source_id`、类别、状态、证据引用 |
| `KMFA/metadata/imports/` | 导入批次和原始文件 manifest 协议 | 只保存 `import_run_id`、hash、大小、状态、证据引用 |
| `KMFA/metadata/schema_maps/` | 字段映射版本协议 | 只保存 `mapping_version`、字段路径、版本和状态 |
| `KMFA/metadata/quality/` | 数据质量和 zero-delta 结果协议 | 只保存质量状态、差异索引、证据引用 |
| `KMFA/metadata/lineage/` | 字段、指标、报告 lineage 协议 | 只保存引用链和版本，不保存原始值 |
| `KMFA/metadata/reports/` | 报告 manifest 协议 | 只保存报告版本、质量等级、输入版本 |
| `KMFA/metadata/approvals/` | 人工处理和签核事件协议 | 只追加事件，不改写原始事实 |

## v1.4 Raw Root Boundary

- local raw/private inbox: `/Users/linzezhang/Downloads/KMFA_MetaData`
- public-safe protocol file: `KMFA/metadata/protocol/raw_data_roots_v1_4.json`
- current S02-P1 access: no read, no list, no inventory, no mutation
- private runtime target: `KMFA/.codex_private_runtime/`
- public repo rule: metadata may record only protocol, status, evidence refs, and authorized aggregate/hash refs; it must not record raw filenames, unapproved raw hashes, field/header plaintext, row values, business amount values, ZIP/Excel/PDF/private CSV/SQLite/db files, credentials, bank statements, contracts, payroll, or tax filings.

## Identifier Contract

| Identifier | Required shape | Example | Notes |
|---|---|---|---|
| `import_run_id` | `IMP-YYYYMMDD-HHMMSS-<slug>-<8hex>` | `IMP-20260629-181500-finance-a1b2c3d4` | 一个导入批次一个 ID |
| `source_id` | `SRC-<domain>-<slug>-<8hex>` | `SRC-finance-ledger-a1b2c3d4` | 只表示来源别名，不保存敏感原文 |
| `file_hash` | `sha256:<64 lowercase hex>` | `sha256:0000000000000000000000000000000000000000000000000000000000000000` | 后续文件登记必须使用 SHA-256 |
| `formula_version` | `FORM-<formula_id>-v<semver>` | `FORM-KMFA-AMOUNT-001-v0.1.0` | 绑定公式定义版本 |
| `mapping_version` | `MAP-<source_id>-v<semver>` | `MAP-SRC-finance-ledger-a1b2c3d4-v0.1.0` | 绑定来源字段映射版本 |

## Privacy Boundary

允许进入公开仓库的 metadata 类别：

- hash
- manifest index
- status
- evidence reference
- schema or mapping version
- quality grade
- lineage reference
- approval event metadata

禁止进入公开仓库的内容：

- 原始银行流水、合同、工资、税务申报、身份证、账户、密码、token、密钥。
- 原始文件全文、PDF 文本全文、Excel 明细行全文。
- 可直接还原敏感经营事实的明文字段值。
- 未脱敏客户、员工、银行账户、纳税主体敏感明细。

## S02-P1 Non-goals

- 不实现 raw manifest 登记器；这是 S02-P2。
- 不实现 Q0-Q5 或 A/B/C/D 报告门禁；这是 S02-P3。
- 不实现文件导入、金额工具、zero-delta、lineage 完整检查或 UI。
- 不上传 GitHub；v1.4 GitHub main upload 延期到 Stage 1-18 全部完成整体复审并修复 findings 后一次性执行。
