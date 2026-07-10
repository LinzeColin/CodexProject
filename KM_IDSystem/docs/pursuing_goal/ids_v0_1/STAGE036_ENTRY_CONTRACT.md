# IDS v0.1 STAGE-036 Entry Contract

## Taskpack Identity
- Stage: `STAGE-036 · 数据库质量约束`
- Task: `IDS-V0_1-STAGE036-P1`
- Acceptance: `ACC-STAGE-036`
- Version: `v0.1`
- Local code: `D06-S007`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `增加关键唯一性、非空、外键、状态枚举和一致性约束。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md`
- P0 stage file SHA-256:
  `13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b`

## Preconditions
- `STAGE-035` is locally reviewed and passed as `completed_reviewed_local`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains the active ten-stage upload lock with
  `push_allowed=false`.
- `STAGE-030` is the authoritative tracked PostgreSQL control-plane schema and
  machine index for eight tables.
- `STAGE-031` owns migration dry-run, backup checkpoint, validation, rollback,
  recovery-smoke evidence, and destructive-change owner gates.
- `STAGE-032` owns connection pools, timeouts, transaction boundaries, retry,
  backpressure, and credential references.
- `STAGE-033` prevents raw, OCR, report-binary, vector, large-file, and
  unbounded derived payloads from entering PostgreSQL.
- `STAGE-034` owns retention metadata, owner holds, cleanup dry-run, deletion
  stop gates, and rollback/restore requirements.
- `STAGE-035` owns isolated recovery preflight and source non-interference.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only boundary. This
  phase must not read, list, hash, open, copy, move, delete, modify, dump, scan,
  normalize, restore, or commit its content.

## Phase 1 Contract
`IDS-V0_1-STAGE036-P1` defines a contract-only database-quality boundary over
the tracked STAGE-030 schema. It classifies current and candidate constraints,
their dependencies, future validation evidence, migration safety, rollback,
owner stop gates, and Chinese violation feedback. It does not change SQL.

The contract covers:
- `PRIMARY_KEY_UNIQUENESS` and `COMPOSITE_UNIQUENESS`;
- `NOT_NULL_REQUIRED` and nonblank identity/reference requirements;
- `FOREIGN_KEY_INTEGRITY` only for real relationships already present in the
  tracked schema;
- `STATUS_VALUESET_INTEGRITY` without freezing downstream job-state values;
- `CROSS_FIELD_CONSISTENCY` for retry counts, offsets, raw-content flags,
  payload bounds, migration safety, and lifecycle relationships.

Phase 1 distinguishes existing schema facts from future candidates. A new
unique, non-null, foreign-key, status, or consistency constraint is not treated
as safe merely because it appears desirable. It must have deterministic schema
evidence, an owner-authorized real-data preflight for duplicate/null/orphan/
invalid-state/conflict detection when row data is required, a reversible
migration plan, validation evidence, and rollback evidence.

Mutable states are not implemented as PostgreSQL native enums in this phase.
`job_state`, `parser_state`, `validation_state`, and `decision_state` must later
resolve through a `versioned_state_registry` and `state_namespace`. STAGE-036
defines the integrity interface only; `STAGE-037` remains authoritative for the
unified job state machine and allowed transitions.

PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件. The quality
contract cannot relax STAGE-030..035 storage, connection, retention, recovery,
source-preservation, real-data-only, or no-secret boundaries.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement the machine index, checker, schema diff,
  migration SQL, constraint DDL, state registry, connection loader, UI,
  database client, service, or runtime behavior.
- `NO_POSTGRES_CONNECTION`: do not connect to PostgreSQL, instantiate a pool,
  create a database/schema/table/index/constraint, or query any rows.
- `NO_SCHEMA_CHANGE`: do not create or edit schema or migration files and do
  not claim any new constraint is installed.
- `NO_LIVE_MIGRATION`: do not run migration dry-run, apply, validate, rollback,
  backup, restore, schema diff, `psql`, `pg_dump`, or `pg_restore`.
- `NO_LIVE_CONSTRAINT_VALIDATION`: do not execute duplicate, null, orphan,
  state-value, consistency, count, index, transaction, or readiness queries.
- `NO_RAW_DB_CONTENT`: do not access or commit raw database content, metadata
  dump bytes, raw rows, source bodies, OCR text, vectors, reports, or logs.
- `NO_FAKE_DATA`: do not use fake IDS business data, fake database rows, fake
  source documents, fabricated dumps, placeholder corpus, or fabricated
  evidence in place of owner-authorized real evidence.
- `NO_STAGE037`: do not define the unified job state machine, transitions,
  retry/dead-letter workflow, worker queue, lock behavior, or lifecycle owned
  by STAGE-037 and later stages.
- Do not start backend, frontend, worker, Docker, dependency installation,
  external APIs, GitHub upload, PR, merge, app reinstall, stage review, batch
  review, upload gate, or Phase 2 work.
- Do not write runtime output, database, manifest, evidence ledger, audit log,
  index, report, PDF, screenshot, JSON output, row fixture, migration output,
  validation output, recovery output, or production artifact.
- Do not submit secrets, API keys, database passwords, credential-bearing DSNs,
  private keys, cloud credentials, or access tokens.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE036_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage036_database_quality_constraints.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
