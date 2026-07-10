# STAGE-036 Phase 2 - Static Database Quality Constraint Slice

## Identity
- Stage: `STAGE-036 · 数据库质量约束`
- Task: `IDS-V0_1-STAGE036-P2`
- Acceptance: `ACC-STAGE-036`
- Contract id: `ids_stage036_database_quality_constraints_static_slice`
- Index schema: `ids.stage036.database_quality_constraints.index.v1`
- Report schema: `ids.stage036.database_quality_constraints.phase2.v1`
- Migration id: `ids_stage036_002_database_quality_constraints`
- Contract state: `STATIC_QUALITY_CONSTRAINT_CONTRACT_VALID`
- Next gate: `IDS-STAGE036-P3-GATE`

## Implemented Static Slice
Phase 2 adds four tracked engineering artifacts:

1. `database_quality_constraints/002_database_quality_constraints.sql`
   defines a guarded, reversible, not-executed migration contract.
2. `database_quality_constraints/stage036_database_quality_constraints_index.json`
   records dependency identities, current constraints, candidate constraints,
   the future `versioned_state_registry`, guardrails, and runtime blocks.
3. `scripts/check_database_quality_constraints.py` reads tracked SQL/JSON and
   prints one deterministic JSON report to stdout.
4. This document records the implementation boundary, truthful result,
   rollback, and Chinese owner feedback.

No PostgreSQL connection, DDL execution, row query, data profile, migration,
constraint validation, backup, restore, or recovery smoke occurred.

## Migration Contract
The migration has ordered `-- migrate:up` and `-- migrate:down` sections. A
future apply fails closed unless all three session refs are present:

- `ids.owner_authorized_real_profile_ref`
- `ids.migration_backup_checkpoint_ref`
- `ids.migration_rollback_plan_ref`

The tracked migration creates the empty structural table
`ids_state_value_registry` with primary key
`(state_namespace, state_value)`. It does not insert or fabricate state values.
STAGE-037 remains authoritative for `job_type`, `job_state`, transitions, and
the unified job state machine. Parser, validation, and decision state values
also remain unpopulated until their owning contracts exist.

The migration records nine candidates:

- `uq_ids_chunks_document_ordinal`
- `chk_ids_metadata_sources_quality_v2`
- `chk_ids_jobs_quality_v2`
- `chk_ids_documents_quality_v2`
- `chk_ids_chunks_quality_v2`
- `chk_ids_evidence_records_quality_v2`
- `chk_ids_audit_events_quality_v2`
- `chk_ids_index_versions_quality_v2`
- `chk_ids_schema_migrations_quality_v2`

The unique candidate is not safe to apply until owner-authorized real
control-plane data proves duplicate count zero. Every `CHECK` candidate is
added `NOT VALID` and then explicitly validated in a future authorized apply;
existing violating rows therefore block the transaction instead of being
silently accepted. No repair, coercion, default backfill, row deletion, or
state-value seed statement exists in the migration.

The down section drops only these STAGE-036 candidates and the registry
structure. It fails closed instead of dropping the registry when any later
owner has populated it. It does not drop STAGE-030 tables or existing
constraints.

## Constraint Coverage
The machine index keeps these categories separate:

- Existing primary keys and the existing composite index-version primary key.
- Existing foreign keys:
  `ids_documents.source_id -> ids_metadata_sources.source_id`,
  `ids_chunks.document_id -> ids_documents.document_id`, and
  `ids_jobs.parent_job_id -> ids_jobs.job_id`.
- Existing stable checks for storage class, `fact_level`, and `index_state`.
- Candidate uniqueness, nonblank, nonnegative, bounded-payload, retry,
  connection-pool, offset, migration-safety, and reference constraints.
- Deferred mutable status values and transitions owned by STAGE-037 or their
  later domain contracts.

The checker strips SQL comments before testing forbidden data-changing
statements, validates exact constraint ids and source refs, verifies the eight
baseline tables and three tracked foreign-key relationships, checks migration
up/down and rollback coverage, validates the empty registry contract and its
nonempty rollback guard, and requires every runtime action to remain false.

## Truthful Result
The expected tracked result is:

- `contract_valid=true`
- `execution_ready=false`
- `execution_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE`
- `migration_execution_performed=false`
- `real_data_profile_executed=false`
- `github_upload_allowed=false`
- `app_reinstall_allowed=false`

`contract_valid=true` means the static migration/index/checker agree and fail
closed. It does not mean the migration was applied, existing rows are clean,
PostgreSQL is reachable, or the database is production-ready.

If the index allows a runtime action, removes the real-data gate, populates
state values, changes dependency identities, or the SQL loses any required
candidate/rollback/guard, the checker returns
`contract_valid=false` and
`BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT`.

## Storage, Connection, And Real-Data Boundaries
- PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件.
- Aggregate pool size stays at most 10 with zero overflow and backpressure.
- The migration and checker contain no plaintext DSN, password, API key, cloud
  credential, raw row, document/OCR body, vector payload, report binary, or raw
  log body.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only in the machine
  index. Its content is not read, listed, hashed, opened, copied, moved,
  deleted, modified, dumped, scanned, normalized, restored, or committed.
- All future duplicate/null/orphan/state/consistency evidence must come from an
  owner-authorized bounded real-data profile. Fake IDS business data, fake
  database rows, fake source documents, fabricated profiles, placeholder
  corpus, and fabricated evidence are forbidden.

## Validation Command
Run from the repository root:

```bash
python3 -B KM_IDSystem/scripts/check_database_quality_constraints.py
```

The command reads only tracked engineering contracts and writes JSON to stdout.
It does not write a report file or runtime artifact.

## Stop Conditions
- Do not execute `002_database_quality_constraints.sql` in this run.
- Do not connect PostgreSQL, instantiate a pool, query rows, or run a profile.
- Do not provide fake rows or fabricated results to satisfy the profile gate.
- Do not seed `ids_state_value_registry` or define STAGE-037 transitions.
- Do not edit STAGE-030 SQL or claim baseline data was migrated.
- Do not execute dry-run/apply/validate/rollback/backup/restore/recovery smoke.
- Do not start services, install dependencies, write runtime output, enter
  Phase 3, upload GitHub, create/merge a PR, reinstall app entries, run stage or
  batch review, or run an upload gate.

## Rollback
Revert only this Phase 2 document, the Stage036 migration/index/checker,
Stage036/Stage005 tests, validator changes, batch lock, roadmap/event, narrow
compatibility updates, and rendered owner files. Do not execute the migration
down section because the migration was not applied. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, source or
runtime databases, dumps, backups, STAGE-030 SQL, reports, outputs, manifests,
evidence ledgers, audit logs, app entries, GitHub state, STAGE-037 files, or
Phase 3 artifacts.

## 中文 Owner 反馈
STAGE-036 Phase 2 已形成静态、可检查、可回滚的数据库质量约束工程切片。
当前没有连接或修改数据库，也没有使用虚构数据证明约束可应用。唯一性和所有
存量行相关约束仍等待 owner 授权真实数据 profile；状态 registry 只创建结构合同，
没有填入状态值。下一步只能进入独立的 Phase 3 场景验证。
