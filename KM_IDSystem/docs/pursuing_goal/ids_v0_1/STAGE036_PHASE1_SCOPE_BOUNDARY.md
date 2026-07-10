# STAGE-036 Phase 1 - Database Quality Constraint Scope Boundary

## Identity And Goal
- Stage: `STAGE-036 · 数据库质量约束`
- Task: `IDS-V0_1-STAGE036-P1`
- Acceptance: `ACC-STAGE-036`
- Local code: `D06-S007`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Goal: `增加关键唯一性、非空、外键、状态枚举和一致性约束。`
- Contract id field: `database_quality_constraint_contract_id`
- P0 source:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md`
- P0 SHA-256:
  `13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b`

This phase defines the engineering contract only. It does not create a
PostgreSQL schema, migration, connection, state registry, row fixture, checker,
runtime output, or live validation result.

## Authoritative Inputs
- `control_plane_schema_ref`:
  `postgresql_control_plane/001_control_plane_schema.sql`
- `control_plane_schema_index_ref`:
  `postgresql_control_plane/control_plane_schema_index.json`
- `schema_migration_safety_ref`:
  `schema_migration_safety/stage031_migration_safety_index.json`
- `connection_pool_contract_ref`:
  `database_connection_pool/stage032_connection_pool_index.json`
- `database_size_guard_ref`:
  `database_size_guard/stage033_database_size_guard_index.json`
- `data_retention_table_ref`:
  `data_retention_table/stage034_data_retention_table_index.json`
- `database_recovery_smoke_ref`:
  `database_recovery_smoke/stage035_database_recovery_smoke_index.json`
- `raw_data_boundary_ref`: `IDS_METADATA_RAW_DATA_BOUNDARY.md`
- `constraint_inventory`: the future machine-readable inventory of current
  schema facts, candidates, dependencies, validation, migration, and rollback.
- `owner_authorized_real_data_profile_ref`: future bounded preflight evidence
  for duplicate/null/orphan/invalid-state/conflict checks. It is absent and is
  not generated in Phase 1.
- `rollback_plan_ref`: future STAGE-031-compatible down migration and
  post-rollback validation evidence.
- `recovery_validation_ref`: future STAGE-035 isolated-target constraint and
  source-non-interference evidence.

No input may contain plaintext credentials, credential-bearing DSNs, raw row
values, raw filenames from protected roots, document/OCR bodies, report
binaries, vectors, raw logs, fake IDS data, placeholder corpus, or fabricated
evidence.

## Tracked Schema Facts
The STAGE-030 schema currently defines eight control-plane tables:
`ids_schema_migrations`, `ids_metadata_sources`, `ids_jobs`, `ids_documents`,
`ids_chunks`, `ids_evidence_records`, `ids_audit_events`, and
`ids_index_versions`.

The following are current tracked facts, not new Phase 1 claims:
- Primary-key uniqueness exists for `migration_id`, `source_id`, `job_id`,
  `document_id`, `chunk_id`, `evidence_id`, and `audit_id`.
- Composite primary-key uniqueness exists for
  `ids_index_versions(index_id, index_version)`.
- Existing foreign keys are
  `ids_documents.source_id -> ids_metadata_sources.source_id`,
  `ids_chunks.document_id -> ids_documents.document_id`, and
  `ids_jobs.parent_job_id -> ids_jobs.job_id`.
- Existing stable value checks cover metadata source storage class,
  evidence `fact_level`, and `ids_index_versions.index_state`.
- Existing consistency checks cover nonnegative source size, bounded payloads,
  raw-content prohibition, retry bounds, connection pool size, nonnegative
  chunk ordinal, and ordered chunk offsets when both offsets are present.

Text references such as `evidence_ref`, `audit_ref`, `coverage_ref`,
`rollback_ref`, and external source refs are not automatically converted into
foreign keys. They may legitimately reference evidence outside one table or
database and require an explicit ownership contract before any future FK.

## Constraint Classification
Every future inventory item must record table, columns, class, existing or
candidate state, dependency, preflight query reference, migration reference,
validation reference, rollback reference, owner-facing Chinese failure reason,
and whether real-row evidence is required.

Required classes are:
- `PRIMARY_KEY_UNIQUENESS`: preserve the seven single-column primary keys.
- `COMPOSITE_UNIQUENESS`: preserve
  `ids_index_versions(index_id, index_version)` and evaluate the schema-backed
  candidate `ids_chunks(document_id, chunk_ordinal)`. The candidate requires
  duplicate preflight against owner-authorized real control-plane data before
  any migration.
- `NOT_NULL_REQUIRED`: preserve current `NOT NULL` columns; evaluate nonblank
  IDs, state names, source URIs, and required refs without converting optional
  fields into required fields without evidence.
- `FOREIGN_KEY_INTEGRITY`: preserve the three tracked relationships above.
  Deletion/update actions remain restrictive by default; no cascade is added
  without explicit source-preservation and retention evidence.
- `STATUS_VALUESET_INTEGRITY`: preserve stable existing checks for
  `storage_class`, `fact_level`, and `index_state`; define an extensible
  registry interface for mutable workflow states.
- `CROSS_FIELD_CONSISTENCY`: evaluate retry/max-retry, paired chunk offsets,
  nonnegative offsets/sizes, raw-content/payload, migration safety, and state
  lifecycle consistency without inventing row results.

Candidate does not mean approved. Candidate states are:
- `EXISTING_SCHEMA_VERIFIED`: directly present in tracked STAGE-030 SQL.
- `PHASE2_STATIC_CONTRACT_CANDIDATE`: eligible for machine-contract work only.
- `OWNER_AUTHORIZED_REAL_DATA_PROFILE_REQUIRED`: blocked until real bounded
  duplicate/null/orphan/invalid-state/conflict evidence exists.
- `DEFERRED_PENDING_STATE_MODEL`: values or transitions belong to STAGE-037.
- `REJECTED_UNOWNED_RELATIONSHIP`: no FK or uniqueness rule may be inferred
  from a similarly named text reference alone.

## Long-Term State Compatibility
Hard-coding `job_state`, `parser_state`, `validation_state`, or
`decision_state` into PostgreSQL native enums now would block STAGE-037 and
future workflow versions. The future interface therefore uses a
`versioned_state_registry` keyed by `state_namespace`, state value, introduced
version, optional retired version, active flag, and owner-readable label.

- `job_state` and `job_type` values are owned by the STAGE-037 unified job
  state machine.
- `parser_state` remains compatible with later parser routing and fallback
  stages.
- `validation_state` remains compatible with evidence and human-review flows.
- `decision_state` remains compatible with audit, owner stop-gate, and approval
  flows.
- Allowed transitions are not defined by STAGE-036. Referential membership and
  transition legality are separate contracts.
- Stable small vocabularies may retain explicit checks when they are already
  authoritative; mutable workflow vocabularies must not require DDL merely to
  add a future state.

Current state: `DB_QUALITY_STATE_REGISTRY_DEFERRED_TO_STAGE037`.

## Outputs
Phase 1 defines these future owner/system outputs:
- `database_quality_constraint_summary`: compact Chinese status by constraint
  class, blocked reason, next gate, and residual risk.
- `constraint_inventory_payload`: machine-readable existing/candidate/rejected
  items with exact schema refs and ownership.
- `constraint_migration_plan_payload`: ordered preflight, DDL, validation,
  backup, rollback, and recovery references without executed output.
- `constraint_validation_payload`: future PASS/FAIL/BLOCKED checks for duplicate,
  null, orphan, state-membership, cross-field, index, and source preservation.
- `constraint_violation_payload`: constraint id, safe field identifiers,
  violation class, bounded count, Chinese explanation, evidence ref, and owner
  action. It must not expose row values or secrets.
- `rollback_verification_payload`: future down-migration, restored constraint
  state, source non-interference, and post-rollback evidence.
- `phase2_ready_contract`: handoff allowing only the approved static machine
  index/checker slice after this Phase 1 contract passes.

## Owner And System States
- `DB_QUALITY_CONSTRAINT_DRAFT`: the Phase 1 boundary is being defined.
- `DB_QUALITY_SCHEMA_BASELINE_BOUND`: the eight tracked STAGE-030 tables and
  current constraints are the baseline.
- `DB_QUALITY_CONSTRAINT_INVENTORY_DEFINED`: classes, ownership, candidate
  states, outputs, and evidence requirements are explicit.
- `DB_QUALITY_STATE_REGISTRY_DEFERRED_TO_STAGE037`: mutable state values and
  transitions remain open for the downstream state-model contract.
- `DB_QUALITY_DATA_PROFILE_REQUIRED`: any row-dependent constraint remains
  blocked without owner-authorized real bounded preflight evidence.
- `DB_QUALITY_MIGRATION_SAFETY_REQUIRED`: dry-run, backup, validation, rollback,
  recovery, and destructive owner confirmation are mandatory.
- `DB_QUALITY_VALIDATION_REQUIRED`: a future constraint is not accepted until
  its schema and real-data checks pass with bounded evidence.
- `DB_QUALITY_ROLLBACK_REQUIRED`: failed migration or validation must stop,
  roll back, preserve source data, and produce post-rollback evidence.
- `DB_QUALITY_RAW_CONTENT_BLOCKED`: raw files, raw rows, bodies, vectors,
  binaries, raw logs, secrets, fake data, and unbounded artifacts remain barred.
- `DB_QUALITY_READY_FOR_PHASE2_SLICE`: contract-only evidence permits a later
  static implementation slice; it is not live migration authorization.

## Migration, Validation, Recovery, And Rollback
- Every candidate must bind to a stable constraint id and exact table/column
  identifiers from the tracked schema.
- A future preflight must detect duplicates, null/nonblank violations, orphans,
  invalid state membership, and cross-field conflicts before DDL. Row values
  must not be written to logs or committed evidence.
- Migration must comply with STAGE-031: deterministic up/down definitions,
  `ON_ERROR_STOP`, single-transaction safety where applicable, backup
  checkpoint, validation, rollback, and recovery-smoke refs.
- Uniqueness changes that cannot be safely applied transactionally must stop
  for a separate reviewed migration plan; Phase 1 does not choose an unsafe
  concurrent-index shortcut.
- A future failure must stop further writes, preserve the source database,
  quarantine an isolated target when relevant, record a bounded Chinese reason,
  execute only the approved rollback, and validate post-rollback state.
- Destructive migration, cascade behavior, data repair, row deletion, default
  backfill, state coercion, or target cleanup requires a separate owner gate and
  is blocked by default.
- No fake rows or placeholder corpus may be used to make a candidate appear
  clean. Current contract tests validate tracked engineering metadata only.

## Storage, Connection, And Raw-Data Boundary
- PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件.
- Quality constraints cannot authorize raw files, raw database rows, source
  document bodies, OCR full text, archive bodies, report binaries, vector
  payloads, raw log bodies, secrets, or unbounded derived artifacts.
- The aggregate connection pool remains at most 10 with zero overflow and
  existing timeout/backpressure requirements. Phase 1 creates no connection.
- `/Users/linzezhang/Downloads/IDS_MetaData` is recorded as path-only. Codex
  must not read, list, hash, open, copy, move, delete, modify, dump, scan,
  normalize, restore, or commit its content.
- All future row-dependent evidence must use owner-authorized real bounded data.
  不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据.

## Boundary And Stop Conditions
- `NO_PHASE2`: no machine index, checker, schema, migration, connection loader,
  state registry, constraint DDL, UI, service, or runtime implementation.
- `NO_POSTGRES_CONNECTION`: no PostgreSQL connection, pool, database, schema,
  table, index, constraint, transaction, healthcheck, or row query.
- `NO_SCHEMA_CHANGE`: no edits to STAGE-030 SQL and no new migration file.
- `NO_LIVE_MIGRATION`: no dry-run/apply/validate/rollback/backup/restore/schema
  diff or PostgreSQL command.
- `NO_LIVE_CONSTRAINT_VALIDATION`: no duplicate/null/orphan/state/consistency/
  count/index query and no claim about real row quality.
- `NO_RAW_DB_CONTENT`: no access to raw roots, dumps, backups, database files,
  row bodies, document/OCR content, vectors, reports, or logs.
- `NO_FAKE_DATA`: no fake business data, fake rows, fake documents, fabricated
  dumps, placeholder corpus, or fabricated evidence.
- `NO_STAGE037`: no unified job states, transitions, worker queue, retry/dead
  letter, backpressure, lock, or automatic lifecycle implementation.
- Do not move, delete, or overwrite `00_ORIGINAL_RAW_DATA`, source/runtime
  databases, reports, outputs, manifests, evidence ledgers, audit logs, indexes,
  or delivered reports.
- Do not write runtime output, database, dump, backup, report, PDF, screenshot,
  JSON output file, fixture row, validation result, or production artifact.
- Do not install dependencies, start services, call external APIs, upload to
  GitHub, create/merge a PR, reinstall app entries, run stage/batch review, run
  an upload gate, or enter Phase 2.
- Stop if a candidate needs real rows but owner-authorized bounded evidence is
  unavailable, if a migration cannot be rolled back, if a shared contract
  conflicts, or if a test fails for an unexplained reason.

## Rollback
Revert only `IDS-V0_1-STAGE036-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test changes, roadmap/event
updates, narrow compatibility-test updates, and rendered owner-file changes.
Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
`00_ORIGINAL_RAW_DATA`, source/runtime databases, dumps, backups, PostgreSQL
data directories, reports, outputs, manifests, evidence ledgers, audit logs,
indexes, app entries, GitHub state, STAGE-030 SQL, STAGE-037 files, or Phase 2
artifacts.
