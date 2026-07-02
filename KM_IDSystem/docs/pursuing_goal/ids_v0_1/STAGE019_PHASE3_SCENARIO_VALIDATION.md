# IDS v0.1 STAGE-019 Phase 3 Scenario Validation

- Task ID: `IDS-V0_1-STAGE019-P3`
- Acceptance ID: `ACC-STAGE-019`
- Stage: `STAGE-019`
- Phase: `Phase 3`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Marker: `STAGE019_PHASE3_SCENARIO_VALIDATION_NO_PHASE4`

## Scope

Phase 3 validates the metadata-only import risk estimator across the required
pre-import scenarios:

- `empty_directory`
- `small_directory`
- `large_directory`
- `offline_drive`
- `archive_present`
- `insufficient_space`

The scenario helper builds an in-memory
`ids.stage019.import_risk_estimator.scenario_validation.v1` report. It calls the
Stage 019 risk estimator for each explicit test-harness source, attaches an
operator decision plan, and verifies the required scenario set is covered.

## Owner Decision Validation

The operator decision plan supports:

- `save_for_owner_review`
- `cancel_without_side_effects`
- `split_into_batches`
- `skip_high_risk_files`

Save means JSON-serializable in-memory content only. The helper does not select
an output path, does not persist a report, and does not write manifests,
databases, evidence ledgers, audit logs, document rows, chunk rows, job rows,
index rows, or import rows.

Cancel leaves all persistence deltas at `0`. Split produces batch metadata only.
Skip-high-risk separates candidate file summaries by metadata risk tags only.

## Processing Guard

- 不解析正文
- 不启动 OCR
- 不启动 Embedding
- 不建立索引
- 不启动实际导入
- 不修改原始文件
- 不写 runtime output
- 不写 manifest/database/document/chunk/job/index/import row

The report records:

- `actual_parse_jobs_started = 0`
- `actual_ocr_jobs_started = 0`
- `actual_embedding_jobs_started = 0`
- `actual_index_jobs_started = 0`
- `actual_import_jobs_started = 0`

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit any content from that root. This phase does not access that directory.
中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。
It only records the path as a read-only boundary already tracked by:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake business documents, placeholder
corpora, fake IDS business data, and fabricated evidence are forbidden.

Phase 3 tests may use temporary process-owned structural directories and scalar
boundary values only as test harness state. Those files are not IDS corpus, not
database rows, not business evidence, and are not committed as user data.

## Validation Notes

- Large-directory validation must expose `RISK_LARGE_BATCH_PRESENT` and a
  multi-batch owner decision plan.
- Offline-drive validation must fail closed with `RISK_BLOCKED`.
- Archive-present validation must expose `RISK_SUSPICIOUS_ARCHIVE_PRESENT`.
- Insufficient-space validation must expose `RISK_INSUFFICIENT_SPACE` and
  `RISK_BLOCKED`.
- The helper must not start actual parse, OCR, Embedding, index, or import work.

## Stop Line

`NO_PHASE4`

This run does not close STAGE-019, does not create owner feedback, does not
perform whole-stage closeout, does not push to GitHub, does not open or merge a
PR, and does not reinstall app entries.
