# IDS v0.1 STAGE-034 Entry Contract

## Taskpack Identity
- Stage: `STAGE-034 · 数据保留表`
- Task: `IDS-V0_1-STAGE034-P1`
- Acceptance: `ACC-STAGE-034`
- Version: `v0.1`
- Local code: `D06-S005`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `定义临时文件、缓存、旧索引、日志、报告快照的保留策略字段。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md`
- P0 stage file SHA-256:
  `af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d`

## Preconditions
- `STAGE-033` is locally reviewed and passed as `completed_reviewed_local`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains the active ten-stage upload lock.
- `STAGE-030` defined the PostgreSQL control-plane schema contract.
- `STAGE-031` defined the schema migration safety contract.
- `STAGE-032` defined the database connection and connection-pool baseline.
- `STAGE-033` defined the database size guard and blocked raw/OCR/large-file
  payloads from PostgreSQL.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only
  real-data source boundary. This phase must not read, list, hash, open, copy,
  move, delete, modify, dump, scan, normalize, or commit raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE034-P1` defines the data retention table boundary for later
implementation. It records the retention-policy fields for temporary files,
caches, old indexes, logs, and report snapshots, plus owner holds, cleanup
dry-run requirements, deletion stop gates, audit evidence, rollback/restore
references, and raw-data boundaries.

Phase 1 is a contract-only phase:
- It defines the future PostgreSQL control-plane retention fields without
  creating schema, migration scripts, database clients, cleanup jobs, deletion
  jobs, retention schedulers, connection configs, DSNs, data directories,
  reports, or runnable services.
- It confirms PostgreSQL may store bounded retention metadata and artifact refs
  only; raw payloads, report binaries, OCR text, raw database rows, and large
  file bodies remain outside PostgreSQL.
- It confirms deletion and cleanup are never automatic in Phase 1. Future
  cleanup behavior must be dry-run first, owner stop-gated, auditable, and
  rollback/restore-aware.
- It requires every later retention state transition to be explainable in
  Chinese, reversible where possible, and backed by audit evidence.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement schema, migration scripts, retention tables,
  cleanup logic, deletion logic, retention schedulers, database clients,
  connection loading, dry-run execution, rollback execution, backup/restore
  smoke tests, hot-index writes, UI controls, or runnable retention behavior.
- `NO_POSTGRES_CONNECTION`: do not connect to local or remote PostgreSQL and do
  not create a PostgreSQL database, schema, migration file, connection config,
  data retention runtime, cleanup task, DSN, data directory, or service process.
- `NO_RETENTION_CLEANUP_RUNTIME`: do not instantiate cleanup jobs, deletion
  jobs, retention scans, old-index rebuilds, report-snapshot pruning, log
  compaction, cache eviction, or database storage monitors in this phase.
- `NO_LIVE_MIGRATION`: do not execute migration dry-run, apply, rollback,
  backup, restore, schema diff, checksum verification, recovery smoke,
  cleanup, deletion, retention, log compaction, cache eviction, old-index
  rebuild, report snapshot pruning, or PostgreSQL commands.
- `NO_RAW_DB_CONTENT`: do not read, list, hash, open, copy, move, delete,
  modify, dump, scan, normalize, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- Do not start backend, frontend, worker, Docker, dependency install, external
  API calls, GitHub upload, PR, merge, app reinstall, batch review, upload gate,
  or Phase 2 work.
- Do not write runtime output, database, manifest, evidence ledger, audit log,
  index, report, PDF, screenshot, JSON output, document/chunk/job/import row,
  parser output, production data artifact, PostgreSQL statistics output,
  retention output, cleanup output, deletion output, or report snapshot output.
- Do not submit secrets, API key, database password, credential-bearing DSN, or
  cloud credentials.
- Do not use fake IDS business data, fake database rows, fake source documents,
  placeholder corpus, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_data_retention_table.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
