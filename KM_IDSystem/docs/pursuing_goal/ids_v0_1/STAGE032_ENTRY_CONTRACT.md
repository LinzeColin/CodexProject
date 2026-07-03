# IDS v0.1 STAGE-032 Entry Contract

## Taskpack Identity
- Stage: `STAGE-032 · 数据库连接与连接池基线`
- Task: `IDS-V0_1-STAGE032-P1`
- Acceptance: `ACC-STAGE-032`
- Version: `v0.1`
- Local code: `D06-S003`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `建立后端、worker、报告任务、检索任务的数据库连接策略。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-032_数据库连接与连接池基线.md`
- P0 stage file SHA-256:
  `a780cbf5eaf4b565dc0f0e7da1c503275bfa4e066d3409f8a258f13f09a0035a`

## Preconditions
- `STAGE-031` is locally reviewed and passed as `completed_reviewed_local`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains the active ten-stage upload lock.
- `STAGE-030` defined the PostgreSQL control-plane schema contract.
- `STAGE-031` defined the schema migration safety contract.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE032-P1` defines the database connection and connection-pool
baseline for later backend, worker, report-task, and retrieval-task slices.
It records the required connection profiles, credential policy, pool-size
limits, timeout limits, transaction boundaries, retry/backoff rules, healthcheck
expectations, migration dependency, storage boundary, hot-index boundary, and
backup/restore requirements.

Phase 1 is a contract-only phase:
- It defines the connection strategy without creating connection configs,
  DSNs, database clients, pools, runtime services, migration scripts, or SQL.
- It confirms PostgreSQL is a control-plane store for metadata, state,
  references, audit/evidence, migration state, and hot-index metadata only.
- It confirms PostgreSQL must not store 500GB raw files, raw database dumps,
  raw IDS business data, raw rows from protected roots, report binaries,
  OCR full text, vector payloads, credentials, or fake data.
- It requires every later runnable connection slice to be rollback-safe,
  healthcheckable, bounded by timeouts, and explainable to the owner.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement database clients, pool factories, connection
  loading, schema, migration scripts, healthcheck execution, worker integration,
  report-task integration, retrieval-task integration, hot-index writes, UI
  controls, or runnable database behavior.
- `NO_POSTGRES_CONNECTION`: do not connect to local or remote PostgreSQL and do
  not create a PostgreSQL database, schema, migration file, connection config,
  pool runtime, DSN, data directory, or service process.
- `NO_CONNECTION_POOL_RUNTIME`: do not instantiate backend, worker, report, or
  retrieval connection pools in this phase.
- `NO_LIVE_MIGRATION`: do not execute migration dry-run, apply, rollback,
  backup, restore, schema diff, checksum verification, or recovery smoke
  commands.
- `NO_RAW_DB_CONTENT`: do not read, list, hash, open, copy, move, delete,
  modify, dump, scan, normalize, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- Do not start backend, frontend, worker, Docker, dependency install, external
  API calls, GitHub upload, PR, merge, app reinstall, or Phase 2 work.
- Do not write runtime output, database, manifest, evidence ledger, audit log,
  index, report, PDF, screenshot, JSON output, document/chunk/job/import row,
  parser output, or production data artifact.
- Do not submit secrets, API key, database password, credential-bearing DSN, or
  cloud credentials.
- Do not use fake IDS business data, fake database rows, fake source documents,
  placeholder corpus, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_database_connection_pool.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
