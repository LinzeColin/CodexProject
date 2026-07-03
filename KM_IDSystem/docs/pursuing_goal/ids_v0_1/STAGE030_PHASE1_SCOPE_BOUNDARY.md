# IDS v0.1 STAGE-030 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage030.postgresql_control_plane.phase1.v1`
- Stage: `STAGE-030 · PostgreSQL 控制面启动`
- Task: `IDS-V0_1-STAGE030-P1`
- Acceptance: `ACC-STAGE-030`
- Local code: `D06-S001`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T06:44:19Z`

This phase defines the PostgreSQL control-plane contract. It does not create a
database, connect to PostgreSQL, execute migrations, inspect raw databases, read
raw files, generate fixtures, or write runtime outputs.

## Contract Fields
- `postgres_control_plane_schema_id`: stable id for the future PostgreSQL
  control-plane schema contract.
- `metadata_table_contract`: source metadata and path-only source boundary refs.
- `job_table_contract`: job state, retry state, dependency state, and stop-gate
  state.
- `document_table_contract`: document identity, source ref, ingestion state,
  ownership state, and report/evidence ref; no raw document body.
- `chunk_table_contract`: chunk identity, source-document ref, parser status,
  and small scalar offsets; no raw chunk text or large payload.
- `evidence_table_contract`: evidence id, evidence kind, source ref, fact level,
  validation state, and audit linkage.
- `audit_table_contract`: actor role, action type, object ref, decision state,
  and error/stop reason.
- `index_version_table_contract`: hot index version, rebuild status, source
  coverage ref, and rollback candidate ref.
- `migration_id`: future migration identity; Phase 1 does not create migration
  files.
- `migration_dry_run_required`: every future migration requires dry-run evidence.
- `migration_rollback_required`: every future migration requires rollback
  evidence and a restore-safe stop gate.
- `connection_url_ref`: reference to a local or environment-managed DSN, never a
  credential-bearing DSN in Git.
- `connection_pool_boundary`: future pool limits, timeout policy, transaction
  boundary, and owner-visible failure reason.
- `storage_boundary`: PostgreSQL stores control plane, state, refs, and hot
  index metadata only.
- `hot_index_boundary`: hot index pointers and version state are allowed; vector
  payloads or large raw index blobs are not allowed in this phase.
- `backup_restore_smoke_ref`: future backup/restore smoke evidence ref; Phase 1
  only defines the requirement.

## Owner And System States
- `POSTGRES_CONTROL_PLANE_DRAFT`: schema, migration, connection, storage, and
  recovery contract exists, but runtime implementation is not started.
- `POSTGRES_MIGRATION_ROLLBACK_REQUIRED`: future migration cannot pass without
  dry-run, idempotency, rollback, and restore evidence.
- `POSTGRES_CONNECTION_SECRET_BLOCKED`: connection config contains plaintext
  credentials or unapproved cloud secrets and must be rejected.
- `POSTGRES_RAW_CONTENT_BLOCKED`: attempted storage of raw files, raw database
  rows, raw document bodies, archive contents, OCR full text, report binaries,
  or fabricated data is blocked.
- `POSTGRES_READY_FOR_PHASE2_SCHEMA_SLICE`: Phase 1 contract is sufficient for a
  later minimal schema/migration slice, still without raw data access.

## Table Boundary
- `metadata`: path-only source refs, owner-approved source ids, size counters,
  status, and source-boundary flags.
- `jobs`: job id, job type, status, retry policy, stop reason, parent job,
  dependency refs, timestamps, and owner-visible failure details.
- `documents`: document id, source ref, parser state, report/evidence refs, and
  lineage refs; no raw file body.
- `chunks`: chunk id, document id, ordinal, parser status, scalar offsets, and
  evidence refs; no raw chunk text or embedding payload.
- `evidence`: evidence id, evidence type, fact level, validation state, source
  refs, and audit refs.
- `audit`: actor role, action, object ref, state transition, stop reason, and
  policy outcome.
- `index_versions`: index id, version, coverage ref, build state, rollback ref,
  and hot index pointer metadata.
- `migrations`: migration id, checksum, dry-run result, apply result, rollback
  result, destructive flag, and recovery checkpoint ref.

## Storage Boundary
- PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件.
- Allowed: small scalar metadata, ids, path-only refs, status values, evidence
  refs, audit refs, migration refs, hot index version refs, and recovery refs.
- Blocked: raw file bodies, raw database dumps, raw database rows, source
  document full text, OCR full text, archive bodies, report binaries, vector
  payload blobs, secrets, fake business rows, and fabricated evidence.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real
  database source boundary and must not be opened, scanned, dumped, hashed,
  copied, normalized, moved, deleted, or modified.

## Migration And Recovery Requirements
- Future migrations must include an explicit `up` path, `down` path, dry-run
  command, idempotency check, rollback command, destructive-migration flag, and
  restore checkpoint reference.
- Destructive migrations require a later explicit owner stop gate; Phase 1 does
  not authorize destructive migration.
- Future restore smoke tests must prove metadata/control-plane recovery without
  touching original raw data or generating fake corpus content.
- Migration logs must not include passwords, API keys, DSNs with credentials,
  raw filenames from protected roots, raw row values, or production document
  content.

## Boundary
- 不创建 PostgreSQL database、schema、migration、runtime data directory 或连接配置.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不提交 secrets、API key、数据库密码或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_RAW_DB_CONTENT`: the future PostgreSQL control plane must never store raw
  database content or raw 500GB corpus content.
- `NO_PHASE2`: do not implement schema, migrations, connection loading,
  migration verification, backup/restore smoke tests, hot-index writes, or UI
  controls in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests,
BATCH021_030 lock update, Stage005 validator/test updates, compatibility test
updates, roadmap/event updates, and rendered owner-file changes only. Do not
touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs,
indexes, app entries, GitHub state, PostgreSQL data directories, or Phase 2
artifacts.
