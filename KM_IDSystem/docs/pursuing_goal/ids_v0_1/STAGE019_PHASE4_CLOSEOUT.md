# IDS v0.1 STAGE-019 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE019-P4`
- Acceptance ID: `ACC-STAGE-019`
- Stage: `STAGE-019`
- Phase: `Phase 4`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Marker: `STAGE019_PHASE4_CLOSEOUT_NO_STAGE020`

## Delivery Evidence

Phase 4 closes out the metadata-only import risk estimator. The delivered
owner-facing helper is:

`KM_IDSystem/scripts/check_import_risk_estimator.py build_owner_feedback_summary`

It produces an in-memory
`ids.stage019.import_risk_estimator.owner_feedback.v1` object with:

- 预检报告样例
- 风险清单
- 用户确认流程日志
- 估算不确定性
- 失败解释文案
- 回滚方式

The helper does not choose an output path, does not persist the report, and does
not create screenshots, PDFs, JSON output files, runtime reports, manifests,
databases, evidence ledgers, audit logs, document rows, chunk rows, job rows,
index rows, or import rows.

## Preflight Report Sample

The report sample is intentionally a compact summary, not a raw data dump. It
includes:

- `overall_state`
- `confirmation_status`
- `risk_score_band`
- `file_count_estimate`
- `total_size_bytes_estimate`
- `format_counts`
- `high_risk_file_count`
- `oversized_file_count`
- `suspicious_archive_count`
- `unknown_format_count`
- `insufficient_space_risk`
- `risk_items`
- `cost_items`
- `priority_hint`
- `human_product_entrance_payload`

No body text, raw payload, raw database row, source file content, or extracted
business value is included.

## Risk Checklist

The closeout feedback can explain these owner-visible risk states:

- `RISK_SOURCE_NOT_CONFIGURED`
- `RISK_SOURCE_BLOCKED`
- `RISK_DRIVE_OFFLINE`
- `RISK_SUSPICIOUS_ARCHIVE_PRESENT`
- `RISK_HIGH_RISK_FILE_PRESENT`
- `RISK_LARGE_BATCH_PRESENT`
- `RISK_OVERSIZED_FILE_PRESENT`
- `RISK_UNKNOWN_FORMAT_PRESENT`
- `RISK_INSUFFICIENT_SPACE`
- `RISK_OWNER_REVIEW_REQUIRED`

## User Confirmation Flow Log

1. 系统展示预检报告样例，owner 先查看数量、体积、格式、风险、成本和优先级。
2. owner 可以选择保存风险估算结果；当前 helper 只提供可序列化内容，不自动落盘。
3. owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database 写入均保持 `0`。
4. owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引或导入。
5. owner 可以选择跳过高风险文件；可疑压缩包、扫描件、未知格式和超大文件会进入跳过候选清单。
6. owner 确认后才进入批量处理；本 Stage 只交付确认前的风险反馈，不授权实际导入。

## Estimation Uncertainty

- 风险估算只基于显式 `file://` 输入的文件系统 metadata；目录不递归扫描。
- 风险等级不代表正文质量、页数、解析耗时、压缩包内部结构或未来模型成本。
- OCR 和 Embedding 工作量是候选数量估算，不代表已经解析正文或启动处理任务。
- 空间不足判断只比较传入 `available_space_bytes` 与估算输入体积，不替代系统级容量审计。

## Failure Explanations

- `RISK_SOURCE_NOT_CONFIGURED`: 未配置导入来源；请先选择 owner 批准的本地 `file://` 输入。
- `RISK_SOURCE_BLOCKED`: 来源不可用或越过安全边界；系统不会继续读取或推断该来源。
- `RISK_DRIVE_OFFLINE`: 移动硬盘或来源盘处于离线状态；请重新接入后再做风险估算。
- `RISK_SUSPICIOUS_ARCHIVE_PRESENT`: 发现可疑压缩包；需要 owner 复核后再决定是否单独处理。
- `RISK_OVERSIZED_FILE_PRESENT`: 发现超大文件；建议拆分批次或先跳过后复核。
- `RISK_UNKNOWN_FORMAT_PRESENT`: 发现未知格式；建议跳过或转交人工处理。
- `RISK_INSUFFICIENT_SPACE`: 目标空间不足；请释放空间或缩小批次后再继续。

## Processing Guard

- 不解析正文
- 不启动 OCR
- 不启动 Embedding
- 不建立索引
- 不启动实际导入
- 不修改原始文件
- 不写 runtime output
- 不写 manifest/database/document/chunk/job/index/import row

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

This closeout only records the path as a read-only real-data boundary already
tracked by:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake business documents, placeholder
corpora, fake IDS business data, and fabricated evidence are forbidden.

Focused tests may use temporary process-owned structural directories and scalar
boundary values only as test harness state. Those files are not IDS corpus, not
database rows, not business evidence, and are not committed as user data.

## Rollback

回滚方式:

1. Revert the Stage 019 Phase 4 helper additions, focused tests, closeout
   evidence, batch lock, roadmap/event updates, Stage005 validator/test changes,
   and rendered owner-file changes.
2. Do not move, delete, overwrite, rewrite, compact, clean, or normalize
   original materials.
3. Do not clean `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases,
   reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes,
   delivered reports, app entries, or GitHub state.
4. After rollback, STAGE-019 should return to Phase 3 complete and Phase 4
   pending.

## Stop Line

`NO_STAGE020`

This run closes STAGE-019 locally only. It does not enter STAGE-020, does not
perform the STAGE-011..020 batch review/upload gate, does not push to GitHub,
does not open or merge a PR, and does not reinstall app entries.
