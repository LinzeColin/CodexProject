# IDS v0.1 STAGE-031 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage031.schema_migration_safety.phase1.v1`
- Stage: `STAGE-031 · Schema 迁移安全`
- Task: `IDS-V0_1-STAGE031-P1`
- Acceptance: `ACC-STAGE-031`
- Local code: `D06-S002`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T08:32:56Z`

This phase defines a migration safety contract only. It does not create schema
files, migration scripts, connection config, database objects, backup files,
restore output, runtime logs, or any executable migration slice.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-031_Schema迁移安全.md` |
| Stage file SHA-256 | `17a91f01a284d4046a0a17f17f02a5be60b2c351b82a91c87c9c75106800be88` |
| Stage execution index | STAGE-031 maps to `D06-S002`, `ACC-STAGE-031`, and `stages/STAGE-031_Schema迁移安全.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future migration-safety inputs:
- `schema_migration_safety_contract_id`: stable id for one schema-migration safety review.
- `schema_change_set_ref`: path-only or Git ref to a future migration change set; Phase 1 does not create the change set.
- `migration_dry_run_plan`: command, expected output class, failure criteria, and artifact policy for future dry-run evidence.
- `backup_checkpoint_ref`: required backup or restore checkpoint reference before any future migration apply.
- `validation_checklist`: deterministic checks for schema compatibility, table/column constraints, index state, migration checksum, and no-raw-content storage.
- `rollback_plan_ref`: explicit rollback command, down migration reference, and recovery owner note for future use.
- `recovery_smoke_plan_ref`: future smoke test proving control-plane recovery after rollback or backup restore.
- `migration_audit_ref`: audit/evidence reference required for migration review and owner-facing state.
- `destructive_migration_review_state`: owner stop-gate state for any destructive or irreversible migration candidate.

The input contract is metadata-only. It must not include plaintext credentials,
raw filenames from protected roots, raw database rows, production document text,
report binaries, archive bodies, OCR full text, vector payloads, or fabricated
IDS business data.

## Outputs
Phase 1 defines these future owner/system outputs:
- `migration_safety_summary`: compact Chinese owner-facing summary of dry-run, backup, validation, rollback, and recovery readiness.
- `rollback_verification_requirements`: required evidence for rollback command, rollback idempotency, and post-rollback validation.
- `owner_stop_gate_payload`: human-readable stop-gate payload for destructive migration or unknown recovery risk.
- `migration_audit_payload`: fact-level, evidence refs, actor role, state transition, and stop reason for governance audit.
- `blocked_storage_policy`: explicit statement that raw files, raw database dumps, raw rows, secrets, and fake data are blocked.
- `phase2_ready_contract`: limited handoff saying Phase 2 may implement a minimal migration-safety slice only after this contract passes.

## Owner And System States
- `SCHEMA_MIGRATION_DRAFT`: migration safety contract exists, but no runnable migration is implemented.
- `SCHEMA_MIGRATION_DRY_RUN_REQUIRED`: future migration cannot proceed without dry-run evidence.
- `SCHEMA_MIGRATION_BACKUP_REQUIRED`: future migration cannot proceed without backup checkpoint evidence.
- `SCHEMA_MIGRATION_VALIDATION_REQUIRED`: future migration cannot proceed without deterministic validation checks.
- `SCHEMA_MIGRATION_ROLLBACK_REQUIRED`: future migration cannot proceed without rollback and recovery evidence.
- `SCHEMA_MIGRATION_DESTRUCTIVE_OWNER_CONFIRMATION_REQUIRED`: destructive migration requires explicit owner stop-gate confirmation.
- `SCHEMA_MIGRATION_BLOCKED_RAW_CONTENT`: migration attempts to store raw files, raw database rows, raw payloads, or fake data and must be blocked.
- `SCHEMA_MIGRATION_READY_FOR_PHASE2_SLICE`: Phase 1 contract is sufficient for a later minimal implementation slice.

## Migration Safety Boundary
- Every future migration must define dry-run, apply, rollback, backup checkpoint, validation checklist, and recovery smoke requirements before any apply path.
- Destructive migration is blocked until a later owner gate explicitly accepts the risk and rollback plan.
- Migration logs must not contain passwords, API keys, credential-bearing DSNs, raw database rows, raw filenames from `/Users/linzezhang/Downloads/IDS_MetaData`, production document content, or report binaries.
- Schema migration evidence must distinguish dry-run evidence, backup evidence, validation evidence, rollback evidence, recovery evidence, and owner stop-gate evidence.
- PostgreSQL remains a control-plane store for metadata, status, refs, audit, evidence, migration state, and hot index metadata only.

## Boundary
- 不创建 PostgreSQL database、schema、migration 文件或连接配置.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不提交 secrets、API key、数据库密码或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE2`: this run must not implement schema, migration scripts,
  connection loading, dry-run execution, rollback execution, backup/restore
  smoke tests, hot-index writes, or UI controls.
- `NO_LIVE_MIGRATION`: this run must not execute any live or dry-run migration command.
- `NO_POSTGRES_CONNECTION`: this run must not connect to PostgreSQL.
- `NO_RAW_DB_CONTENT`: future migrations may reference approved source IDs later, but must never store raw database content or raw 500GB corpus content.

## Rollback
Revert only `IDS-V0_1-STAGE031-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event
updates, and rendered owner-file changes. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, runtime data,
reports, outputs, manifests, evidence ledgers, audit logs, indexes, app entries,
GitHub state, PostgreSQL data directories, or Phase 2 artifacts.
