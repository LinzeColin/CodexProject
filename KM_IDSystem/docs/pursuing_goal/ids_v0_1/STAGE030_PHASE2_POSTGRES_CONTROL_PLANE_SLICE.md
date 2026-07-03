# IDS v0.1 STAGE-030 Phase 2 PostgreSQL Control Plane Slice

## Scope
- Schema: `ids.stage030.postgresql_control_plane.phase2.v1`
- Stage: `STAGE-030 · PostgreSQL 控制面启动`
- Task: `IDS-V0_1-STAGE030-P2`
- Acceptance: `ACC-STAGE-030`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-03T07:26:00Z`

This phase implements a static, tracked PostgreSQL control-plane slice. It
defines schema DDL, migration rollback text, connection-pool guards, database
size guards, and quality constraints without connecting to PostgreSQL or writing
runtime database state.

## Delivered Slice
- `KM_IDSystem/scripts/check_postgresql_control_plane.py`
  - validates the tracked SQL and machine-readable index in memory;
  - returns schema `ids.stage030.postgresql_control_plane.phase2.v1`;
  - does not connect to PostgreSQL;
  - does not read raw metadata;
  - does not write runtime outputs.
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql`
  - records `-- migrate:up` and `-- migrate:down`;
  - defines metadata、job、document、chunk、evidence、audit、index version and
    schema migration control-plane tables;
  - includes migration dry-run and rollback markers;
  - blocks raw content storage with `chk_no_raw_content_stored` and
    `NO_RAW_DB_CONTENT`;
  - records `ENV:IDS_POSTGRES_DSN` as a connection reference only.
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json`
  - records the schema change to a machine-readable index;
  - records database size, connection pool and quality constraint guards;
  - records `/Users/linzezhang/Downloads/IDS_MetaData` as path-only read-only
    real database source boundary.

## Tables
- `ids_metadata_sources`: path-only metadata source refs and source-boundary flags.
- `ids_jobs`: job state, retry, dependency, stop reason, and connection pool guard.
- `ids_documents`: document identity, source ref, parser state, evidence/report refs.
- `ids_chunks`: chunk identity, document ref, scalar offsets, parser state.
- `ids_evidence_records`: evidence kind, fact level, validation state, audit ref.
- `ids_audit_events`: actor role, action, object ref, decision state, stop reason.
- `ids_index_versions`: hot index version, coverage ref, rollback ref, pointer ref.
- `ids_schema_migrations`: migration id, checksum, dry-run, rollback, destructive flag.

## Guards
- 数据库大小: `payload_size_bytes <= 1048576` for control-plane payload columns.
- 连接池: `connection_pool_size <= 10`; index records statement, lock, and idle
  timeout ceilings.
- 质量约束: `fact_level` is limited to `VERIFIED`、`INFERRED`、`UNKNOWN`; index
  state is limited to `DRAFT`、`READY`、`BLOCKED`、`ROLLBACK_READY`.
- Migration: `dry_run_required=true`, `rollback_required=true`,
  `destructive_allowed=false`.
- Storage: PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件、原始数据库内容、
  生产文档正文、压缩包正文、OCR 全文、向量 payload、报告二进制或 secrets.

## Raw Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容。
- This phase does not read, list, hash, open, copy, move, delete, modify, dump,
  normalize, compact, or scan `/Users/linzezhang/Downloads/IDS_MetaData`.
- This phase does not inspect raw filenames, table contents, row values, schema
  details, credentials, private business values, or derived dumps from that root.
- Future runtime corpus, database-backed content, analytics inputs, reports,
  indexes, manifests, and committed examples must use real user-approved data.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Non-Goals
- 不连接 PostgreSQL.
- 不创建 database、schema、runtime data directory 或 local service.
- 不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不安装依赖、不启动 Docker、backend、frontend 或 worker.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact.
- 不提交 secrets、API key、数据库密码、DSN with credentials 或云端凭证.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE3`: this run must not validate live migration execution, repeat apply,
  failure rollback, recovery smoke, transaction behavior, or live constraint errors.

## Verification Targets
- Stage030 focused tests validate the script, SQL migration, schema index,
  batch lock, roadmap, event, and raw-data boundary.
- Stage005 governance regression accepts `IDS-STAGE030-P2` as current local
  no-upload state.
- Full v0.1 test discovery, Stage005 validator, render drift, and event
  uniqueness remain required before commit.

## Rollback
Revert `check_postgresql_control_plane.py`, the SQL/index contract files, this
Phase 2 evidence, Stage030/Stage005 tests, BATCH021_030 lock, roadmap/events,
compatibility-test updates, validator updates, and rendered owner-file changes.
Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs, indexes,
PostgreSQL data directories, app entries, GitHub state, or Phase 3 artifacts.
