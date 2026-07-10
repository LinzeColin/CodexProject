# IDS v0.1 STAGE-035 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage035.database_recovery_smoke.phase1.v1`
- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Task: `IDS-V0_1-STAGE035-P1`
- Acceptance: `ACC-STAGE-035`
- Local code: `D06-S006`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-10T14:13:42Z`

This phase defines a database recovery smoke contract only. It does not access
a metadata dump, connect to PostgreSQL, create a restore target, execute schema
or migration commands, restore data, start services, or write runtime evidence.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md` |
| Stage file SHA-256 | `2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62` |
| Matching stage entries | `1` |
| Stage execution index | STAGE-035 maps to `D06-S006`, `ACC-STAGE-035`, and `stages/STAGE-035_数据库恢复冒烟测试.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extraction or copying into the worktree. No metadata database or dump
content was read to produce this contract.

## Inputs
Phase 1 defines these future recovery-smoke inputs:
- `database_recovery_smoke_contract_id`: stable id for one metadata-dump
  recovery contract.
- `metadata_dump_ref`: owner-approved path/object/evidence reference to a future
  real metadata dump; the dump itself is not opened or committed in Phase 1.
- `metadata_dump_identity`: future dump id, format, source database ref, source
  schema version, migration head, PostgreSQL tool version, creation timestamp,
  bounded content scope, checksum evidence ref, and owner approval ref.
- `control_plane_schema_ref`: dependency on the STAGE-030 control-plane schema
  contract.
- `schema_migration_safety_ref`: dependency on STAGE-031 dry-run, rollback,
  backup checkpoint, and recovery requirements.
- `connection_pool_contract_ref`: dependency on STAGE-032 connection budget,
  timeout, transaction, and secret-loading boundaries.
- `database_size_guard_ref`: dependency on STAGE-033 raw/OCR/large-file and
  unbounded-derived-payload blocking.
- `data_retention_table_ref`: dependency on STAGE-034 retention, owner hold,
  cleanup dry-run, deletion stop gate, and rollback/restore requirements.
- `restore_target_contract`: future isolated, owner-authorized, non-production
  target identity, lifecycle, credential-ref policy, and cleanup stop gate.
- `restore_preflight_checklist`: future dump identity, checksum evidence, format
  compatibility, tool-version compatibility, storage scope, secret boundary,
  migration head, free-space guard, and owner approval checks.
- `restore_execution_plan`: future ordered restore plan with command refs,
  transaction/error-stop behavior, expected result classes, timeout, and stop
  reasons; it contains no credential-bearing command in Git.
- `restore_validation_checklist`: future deterministic checks for schema,
  migration ledger, required control-plane tables, constraints, indexes,
  bounded real metadata counts, audit/evidence refs, readiness, and no raw
  payloads.
- `backup_checkpoint_ref`: future source checkpoint and restore evidence ref;
  no backup is created in Phase 1.
- `rollback_plan_ref`: future failure rollback, target quarantine, source
  non-interference, and post-rollback verification evidence ref.
- `recovery_audit_ref`: future fact-level event/evidence reference for preflight,
  execution, validation, failure, owner decision, and rollback.
- `owner_authorized_real_metadata_dump_required`: mandatory true gate. If no
  owner-authorized real metadata dump exists, execution must stop rather than
  generating fake rows or a fabricated dump.

The input contract is metadata-only. It must not contain plaintext credentials,
credential-bearing DSNs, dump bytes, raw filenames from protected roots, raw
database rows, source document text, OCR full text, report binaries, archive
bodies, vector payloads, raw logs, unbounded derived artifacts, fake IDS
business data, or fabricated evidence.

## Outputs
Phase 1 defines these future owner/system outputs:
- `database_recovery_smoke_summary`: compact Chinese owner-facing result for
  dump identity, restore target, compatibility, validation, rollback, and
  residual limits.
- `metadata_dump_identity_payload`: bounded dump metadata and owner approval
  refs only; never dump bytes or raw row content.
- `restore_preflight_payload`: per-check PASS/FAIL/BLOCKED state with Chinese
  owner reason and evidence refs.
- `restore_execution_plan_payload`: future ordered action refs and stop reasons,
  without credentials or executed command output.
- `restore_validation_payload`: future schema/migration/table/constraint/index,
  bounded real metadata count, readiness, and no-raw-payload results.
- `rollback_verification_payload`: future quarantine/rollback/source
  non-interference/post-rollback checks and owner decision evidence.
- `recovery_audit_payload`: future fact level, actor role, state transition,
  evidence refs, failure class, and owner-readable stop reason.
- `phase2_ready_contract`: limited handoff saying Phase 2 may implement the
  approved minimal static recovery-smoke slice only after this contract passes.

## Owner And System States
- `DATABASE_RECOVERY_SMOKE_DRAFT`: recovery boundary exists; no dump is opened
  and no restore is executed.
- `DATABASE_RECOVERY_REAL_DUMP_REQUIRED`: execution is blocked until an
  owner-authorized real metadata dump reference exists.
- `DATABASE_RECOVERY_DUMP_IDENTITY_VERIFIED`: future dump identity, scope,
  compatibility, and checksum evidence have passed without exposing dump data.
- `DATABASE_RECOVERY_ISOLATED_TARGET_REQUIRED`: a future restore must target an
  explicitly authorized isolated non-production database.
- `DATABASE_RECOVERY_SCHEMA_COMPATIBILITY_REQUIRED`: source schema, migration
  head, PostgreSQL tool version, and target compatibility must pass first.
- `DATABASE_RECOVERY_VALIDATION_REQUIRED`: future restored schema, migration
  ledger, control-plane tables, constraints, indexes, bounded real metadata
  counts, readiness, and no-raw-payload checks are mandatory.
- `DATABASE_RECOVERY_OWNER_CONFIRMATION_REQUIRED`: unknown, destructive,
  production-targeting, cleanup, or source-affecting behavior requires an owner
  stop gate and remains blocked by default.
- `DATABASE_RECOVERY_RAW_CONTENT_BLOCKED`: raw files, raw dump bodies, raw rows,
  OCR/document/report bodies, vector payloads, or fabricated data must block the
  restore path.
- `DATABASE_RECOVERY_READY_FOR_PHASE2_SLICE`: Phase 1 is sufficient for a later
  minimal static implementation slice; it is not live restore authorization.

## PostgreSQL Storage And Dump Boundary
- PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件.
- A future eligible metadata dump may contain bounded control-plane schema,
  metadata, jobs, document/chunk identity refs without bodies, evidence, audit,
  index-version state, migration state, retention state, and hot-index pointer
  metadata only.
- Blocked content includes raw files, raw database source payloads, original
  document bodies, OCR full text, archive bodies, report binaries, vector
  payload blobs, raw log bodies, secrets, fake rows, and unbounded artifacts.
- Source, target, and dump identities must remain distinct. A future restore
  must not overwrite, mutate, truncate, delete, or migrate the source database.
- Future source-versus-restored counts and identities must be derived from the
  same owner-approved real metadata dump evidence. They must not be fabricated.
- No dump existence, checksum, row count, schema compatibility, restore success,
  or production readiness is claimed in Phase 1.

## Restore And Rollback Requirements
- Future restore preflight must fail closed on missing owner approval, unknown
  dump identity, checksum mismatch, unsupported dump/tool format, incompatible
  schema or migration head, prohibited payload scope, missing secret reference,
  insufficient isolated-target capacity, or production/source target identity.
- Future execution must use a separate authorized target and environment-managed
  credentials; logs and evidence must redact credentials and raw values.
- Future validation must distinguish dump identity evidence, restore execution
  evidence, schema/migration evidence, constraint/index evidence, bounded real
  metadata count evidence, readiness evidence, no-raw-payload evidence, and
  owner acceptance.
- Failure must stop further writes, quarantine the isolated target, preserve the
  source, record a Chinese owner reason, and follow the approved rollback plan.
- Target cleanup or deletion is not automatic and requires a later explicit
  owner stop gate under the STAGE-034 retention/deletion contract.

## Boundary And Stop Conditions
- 不创建 PostgreSQL database、schema、migration 文件、连接配置、metadata dump、恢复目标或恢复任务.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore、schema diff 或恢复冒烟.
- 不运行 `pg_dump`、`pg_restore`、`psql`、healthcheck、transaction、constraint、
  index、row-count、cleanup 或 target-deletion 命令.
- 不创建、读取、列出、hash、打开、复制、移动、删除、修改、inspect、extract、
  normalize 或恢复 metadata dump、backup 或 database file.
- 不写 runtime output、database、dump、backup、manifest、evidence ledger、
  audit log、index、report、PDF、screenshot、JSON output、document/chunk/job/
  import row、parser output、restore output、recovery log、cleanup output 或
  production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`、source database、runtime data、
  reports、outputs、manifest、evidence ledger、audit log 或已交付报告.
- 不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据.
- 无 owner 授权真实 metadata dump 时必须停止.
- 不执行 GitHub upload、PR、merge、app reinstall、stage review、batch review
  或 upload gate.
- `NO_PHASE2`: this run must not implement the machine index, checker, schema,
  migration, connection loader, dump/restore command, recovery runner, UI, or
  service.
- `NO_POSTGRES_CONNECTION`: this run must not connect to PostgreSQL.
- `NO_DUMP_ACCESS`: this run must not create, read, inspect, hash, copy, or
  restore any metadata dump or backup.
- `NO_LIVE_MIGRATION`: this run must not execute any migration command.
- `NO_LIVE_RESTORE`: this run must not execute dump, backup, restore, recovery
  smoke, healthcheck, transaction, validation, or target cleanup commands.
- `NO_RAW_DB_CONTENT`: future recovery may reference approved metadata dump IDs
  only and must never store or expose raw database/500GB corpus content.
- `NO_FAKE_DATA`: future recovery evidence must use owner-approved real metadata
  and must stop rather than substitute fake rows, fake dumps, or fake evidence.

## Rollback
Revert only `IDS-V0_1-STAGE035-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event
updates, compatibility-test updates, and rendered owner-file changes. Do not
touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, source
or runtime databases, dumps, backups, reports, outputs, manifests, evidence
ledgers, audit logs, indexes, app entries, GitHub state, PostgreSQL data
directories, restore targets, recovery outputs, or Phase 2 artifacts.
