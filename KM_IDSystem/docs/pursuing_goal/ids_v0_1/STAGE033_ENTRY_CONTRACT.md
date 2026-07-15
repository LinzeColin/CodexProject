# IDS v0.1 STAGE-033 Entry Contract

## Taskpack Identity
- Stage: `STAGE-033 · 数据库体积护栏`
- Task: `IDS-V0_1-STAGE033-P1`
- Acceptance: `ACC-STAGE-033`
- Version: `v0.1`
- Local code: `D06-S004`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `防止 PostgreSQL 无边界存 raw/OCR/大文件派生产物，保护 800GB 内置盘。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md`
- P0 stage file SHA-256:
  `454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777`

## Preconditions
- `STAGE-032` is locally reviewed and passed as `completed_reviewed_local`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains the active ten-stage upload lock.
- `STAGE-030` defined the PostgreSQL control-plane schema contract.
- `STAGE-031` defined the schema migration safety contract.
- `STAGE-032` defined the database connection and connection-pool baseline.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE033-P1` defines the database size-guard boundary for later
implementation. It records the required PostgreSQL storage scope, blocked raw
content classes, blocked OCR/full-text payload classes, large-file and derived
artifact boundaries, size budget fields, table/index/payload guardrails,
retention/cleanup boundaries, audit evidence, and rollback verification
requirements.

Phase 1 is a contract-only phase:
- It defines the database volume guard without creating schema, migration
  scripts, size-query runtime, cleanup jobs, connection configs, DSNs, data
  directories, reports, or runnable services.
- It confirms PostgreSQL stores control-plane metadata, state, refs, audit,
  evidence, migration state, job state, and bounded hot-index metadata only.
- It confirms PostgreSQL must not store 500GB raw files, raw metadata database
  content, raw rows from protected roots, OCR full text, document bodies, report
  binaries, vector payloads, unbounded derived artifacts, credentials, or fake
  data.
- It requires every later runnable size guard to be rollback-safe, bounded,
  explainable, and non-destructive by default.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement schema, migration scripts, size statistics,
  database cleanup, retention jobs, database clients, connection loading,
  healthcheck execution, worker integration, report-task integration,
  retrieval-task integration, hot-index writes, UI controls, or runnable
  database behavior.
- `NO_POSTGRES_CONNECTION`: do not connect to local or remote PostgreSQL and do
  not create a PostgreSQL database, schema, migration file, connection config,
  volume-statistics runtime, cleanup task, DSN, data directory, or service
  process.
- `NO_SIZE_GUARD_RUNTIME`: do not instantiate size checks, table scans,
  pg_total_relation_size queries, VACUUM, cleanup jobs, retention deletion jobs,
  or database storage monitors in this phase.
- `NO_LIVE_MIGRATION`: do not execute migration dry-run, apply, rollback,
  backup, restore, schema diff, checksum verification, recovery smoke, VACUUM,
  cleanup, retention, or volume-statistics commands.
- `NO_RAW_DB_CONTENT`: do not read, list, hash, open, copy, move, delete,
  modify, dump, scan, normalize, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- Do not start backend, frontend, worker, Docker, dependency install, external
  API calls, GitHub upload, PR, merge, app reinstall, batch review, upload gate,
  or Phase 2 work.
- Do not write runtime output, database, manifest, evidence ledger, audit log,
  index, report, PDF, screenshot, JSON output, document/chunk/job/import row,
  parser output, production data artifact, PostgreSQL statistics output, or
  cleanup output.
- Do not submit secrets, API key, database password, credential-bearing DSN, or
  cloud credentials.
- Do not use fake IDS business data, fake database rows, fake source documents,
  placeholder corpus, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
