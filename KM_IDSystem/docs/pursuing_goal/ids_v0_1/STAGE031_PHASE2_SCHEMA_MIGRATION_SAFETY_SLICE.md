# IDS v0.1 STAGE-031 Phase 2 Schema Migration Safety Slice

## Scope
- Schema: `ids.stage031.schema_migration_safety.phase2.v1`
- Stage: `STAGE-031 · Schema 迁移安全`
- Task: `IDS-V0_1-STAGE031-P2`
- Acceptance: `ACC-STAGE-031`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-03T08:51:49Z`

This phase implements a static, tracked schema migration safety slice. It uses
the real committed STAGE-030 PostgreSQL control-plane schema contract as the
source schema change and validates its dry-run, backup checkpoint, validation
checklist, rollback guard, recovery smoke, audit, owner stop-gate, connection
pool, database size, and storage quality requirements in memory.

## Delivered Slice
- `KM_IDSystem/scripts/check_schema_migration_safety.py`
  - builds `ids.stage031.schema_migration_safety.phase2.v1` reports;
  - reads only tracked Git files under `KM_IDSystem/`;
  - validates safety gates against the committed STAGE-030 schema/index;
  - does not connect to PostgreSQL;
  - does not execute migration dry-run、apply、rollback、backup、restore 或 schema diff;
  - does not read raw metadata or write runtime outputs.
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json`
  - records the machine-readable safety index for `ids_stage030_001_control_plane`;
  - records dry-run, backup checkpoint, validation, rollback, recovery smoke,
    audit, and owner stop-gate requirements;
  - records database size, connection pool and storage quality guardrails;
  - records `/Users/linzezhang/Downloads/IDS_MetaData` as path-only read-only
    real database source boundary.

## Safety Gates
- dry-run: future migration execution must require `ON_ERROR_STOP=1`,
  `--single-transaction`, and dry-run evidence before any apply path.
- backup checkpoint: any future apply path must reference a pre-apply control
  plane backup checkpoint and restore evidence.
- validation checklist: schema markers, payload size, no-raw-content, connection
  pool, fact level, and index state constraints must be present.
- rollback guard: rollback SQL must exist, run fail-fast, and stay transactional.
- recovery smoke: recovery checkpoint and rollback SQL refs must exist before
  runtime restore smoke tests are allowed.
- audit: migration and audit tables must record fact-level evidence refs.
- owner stop-gate: destructive migration is blocked unless a later explicit
  owner gate approves risk and recovery evidence.

## Guardrails
- database size: `max_control_plane_payload_bytes <= 1048576`.
- connection pool: `max_pool_size <= 10`, `statement_timeout_ms <= 30000`,
  `lock_timeout_ms <= 5000`, and `idle_timeout_ms <= 60000`.
- quality: PostgreSQL remains a control-plane store for metadata, state, refs,
  audit, evidence, migration state, and hot index metadata only.
- storage: raw files, raw database rows, production document bodies, archive
  bodies, OCR full text, large vector payloads, report binaries, secrets, fake
  IDS business data, fake database rows, fake source documents, placeholder
  corpus, and fabricated evidence are blocked.

## Raw Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容。
- This phase does not inspect raw filenames, table contents, row values, schema
  details, credentials, private business values, or derived dumps from that root.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据。

## Non-Goals
- 不连接 PostgreSQL。
- 不创建 database、schema、runtime data directory、local service 或 live connection config。
- 不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff。
- 不安装依赖、不启动 Docker、backend、frontend 或 worker。
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact。
- 不提交 secrets、API key、数据库密码、DSN with credentials 或云端凭证。
- 不执行 GitHub upload、PR、merge 或 app reinstall。
- `NO_PHASE3`: this run must not validate live migration execution, repeat apply,
  failure rollback, recovery smoke, transaction behavior, or live constraint errors.

## Verification Targets
- Stage031 focused tests validate the Phase 2 script, safety index, evidence
  document, batch lock, roadmap, event, and raw-data boundary.
- Stage005 governance regression accepts `IDS-STAGE031-P2` as the current local
  no-upload state.
- Full v0.1 discovery, Stage005 validator, render drift, event uniqueness,
  py_compile, diff checks, and sparse semantic diagnostic remain required before
  commit.

## Rollback
Revert `check_schema_migration_safety.py`, `schema_migration_safety/`,
`STAGE031_PHASE2_SCHEMA_MIGRATION_SAFETY_SLICE.md`, Stage031/Stage005 tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, roadmap/events, validator updates, and rendered
owner-file changes. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
`00_ORIGINAL_RAW_DATA`, runtime data, reports, outputs, manifests, evidence
ledgers, audit logs, indexes, PostgreSQL data directories, app entries, GitHub
state, or Phase 3 artifacts.
