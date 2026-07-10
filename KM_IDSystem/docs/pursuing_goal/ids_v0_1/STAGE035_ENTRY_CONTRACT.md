# IDS v0.1 STAGE-035 Entry Contract

## Taskpack Identity
- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Task: `IDS-V0_1-STAGE035-P1`
- Acceptance: `ACC-STAGE-035`
- Version: `v0.1`
- Local code: `D06-S006`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `验证 metadata dump 能恢复到可运行状态。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md`
- P0 stage file SHA-256:
  `2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62`

## Preconditions
- `STAGE-034` is locally reviewed and passed as `completed_reviewed_local`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains the active ten-stage upload lock.
- `STAGE-030` defines the PostgreSQL control-plane schema and storage contract.
- `STAGE-031` defines migration dry-run, rollback, backup checkpoint, and
  recovery evidence requirements.
- `STAGE-032` defines the connection and connection-pool boundary.
- `STAGE-033` blocks raw, OCR, large-file, and unbounded derived payloads from
  PostgreSQL.
- `STAGE-034` defines bounded retention metadata, owner holds, cleanup dry-run,
  deletion stop gates, and rollback/restore requirements.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real
  database source boundary. This phase must not read, list, hash, open, copy,
  move, delete, modify, dump, scan, normalize, or commit its content.
- No owner-authorized real metadata dump is inspected or claimed available in
  Phase 1. 无 owner 授权真实 metadata dump 时必须停止; do not replace it with
  fake rows, a fabricated dump, or placeholder corpus.

## Phase 1 Contract
`IDS-V0_1-STAGE035-P1` defines the database recovery smoke boundary for later
implementation. It records future metadata dump identity, source schema and
migration compatibility, an isolated restore target, connection and storage
boundaries, restore preflight, validation, audit evidence, owner confirmation,
and rollback requirements.

Phase 1 is contract-only:
- It defines how a future owner-authorized real metadata dump may be referenced
  and validated without creating, opening, copying, hashing, or restoring a
  dump in this run.
- It confirms PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件.
  A future metadata dump must contain bounded control-plane metadata, states,
  refs, audit/evidence records, migration state, and hot-index metadata only.
- It requires a future restore to use an explicitly authorized isolated target,
  never production or the source database, with credential references supplied
  outside Git.
- It requires deterministic schema/migration compatibility, constraint/index
  checks, source-versus-restored real metadata counts, health/readiness checks,
  audit evidence, rollback, and owner-readable Chinese failure reasons.
- It does not claim database recovery is runnable or production-ready. Phase 2
  may implement only the next approved minimal slice after this boundary passes.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement a machine index, checker, schema, migration,
  connection loader, dump command, restore command, recovery smoke runner,
  database client, UI, service, or runtime behavior.
- `NO_POSTGRES_CONNECTION`: do not connect to local or remote PostgreSQL and do
  not create a PostgreSQL database, schema, migration file, connection config,
  DSN, data directory, restore target, or service process.
- `NO_DUMP_ACCESS`: do not create, read, list, hash, open, copy, move, delete,
  modify, inspect, extract, normalize, or restore any metadata dump, backup,
  database file, or raw source content.
- `NO_LIVE_MIGRATION`: do not execute migration dry-run, apply, rollback,
  backup, restore, schema diff, checksum verification, or PostgreSQL commands.
- `NO_LIVE_RESTORE`: do not run `pg_dump`, `pg_restore`, `psql`, backup,
  restore, recovery smoke, healthcheck, transaction, constraint, or cleanup
  commands against any database.
- `NO_RAW_DB_CONTENT`: do not read, list, hash, open, copy, move, delete,
  modify, dump, scan, normalize, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- `NO_FAKE_DATA`: do not use fake IDS business data, fake database rows,
  fabricated metadata dumps, fake source documents, placeholder corpus, or
  fabricated evidence to simulate recovery.
- Do not start backend, frontend, worker, Docker, dependency installation,
  external APIs, GitHub upload, PR, merge, app reinstall, stage review, batch
  review, upload gate, or Phase 2 work.
- Do not write runtime output, database, dump, backup, manifest, evidence
  ledger, audit log, index, report, PDF, screenshot, JSON output,
  document/chunk/job/import row, parser output, restore output, recovery log,
  production data artifact, or cleanup output.
- Do not submit secrets, API key, database password, credential-bearing DSN,
  private key, cloud credential, or access token.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage035_database_recovery_smoke.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
