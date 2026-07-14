# IDS v0.1 STAGE-033 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage033.database_size_guard.phase1.v1`
- Stage: `STAGE-033 · 数据库体积护栏`
- Task: `IDS-V0_1-STAGE033-P1`
- Acceptance: `ACC-STAGE-033`
- Local code: `D06-S004`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T11:23:27Z`

This phase defines a database volume guard contract only. It does not create
PostgreSQL schema, migration scripts, size-statistics queries, cleanup jobs,
connection configuration, database clients, runtime logs, reports, or any
executable database-size guard slice.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md` |
| Stage file SHA-256 | `454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777` |
| Stage execution index | STAGE-033 maps to `D06-S004`, `ACC-STAGE-033`, and `stages/STAGE-033_数据库体积护栏.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future database-size guard inputs:
- `database_size_guard_contract_id`: stable id for one database-size guard contract.
- `control_plane_schema_ref`: dependency on the STAGE-030 control-plane schema contract.
- `schema_migration_safety_ref`: dependency on the STAGE-031 migration rollback and validation contract.
- `connection_pool_contract_ref`: dependency on the STAGE-032 connection and pool baseline.
- `postgres_storage_scope`: explicit list of PostgreSQL-allowed storage classes.
- `raw_content_storage_block`: blocked classes for raw files, raw database dumps, raw rows, protected-root payloads, and source bodies.
- `ocr_full_text_storage_block`: blocked classes for OCR full text, full document bodies, and extracted text payloads.
- `large_file_storage_block`: blocked classes for 500GB raw file storage, report binaries, archives, media, and unbounded blobs.
- `derived_artifact_limit`: bounded policy for manifests, evidence refs, hot-index metadata, report refs, and re-creatable derived state.
- `database_size_budget`: future max database size, warning threshold, stop threshold, and owner-facing reason fields.
- `table_size_guard`: future per-table size threshold, row-count threshold, and allowed exception policy.
- `index_bloat_guard`: future index bloat warning threshold, rebuild/cleanup decision ref, and no-auto-destructive-change policy.
- `row_payload_guard`: future maximum row payload shape and prohibition on raw/OCR/vector/report bodies.
- `retention_and_cleanup_boundary`: future retention policy reference, cleanup dry-run requirement, and owner stop gate for deletion.
- `audit_evidence_ref`: event/evidence reference required for every future size-guard state transition.
- `rollback_verification_requirement`: future rollback, backup/restore, and post-cleanup verification requirement.

The input contract is metadata-only. It must not include plaintext credentials,
raw filenames from protected roots, raw database rows, production document text,
report binaries, archive bodies, OCR full text, vector payloads, unbounded
derived artifacts, or fabricated IDS business data.

## Outputs
Phase 1 defines these future owner/system outputs:
- `database_size_guard_summary`: compact Chinese owner-facing summary of storage scope, blocked payloads, and 800GB disk protection.
- `storage_scope_payload`: explicit statement that PostgreSQL 只存控制面、状态和热索引.
- `blocked_payload_policy`: explicit statement that PostgreSQL 不存 500GB 原始文件, 不存 OCR 全文, 不存无限制派生产物.
- `size_budget_payload`: future size budget, warning threshold, stop threshold, and owner-readable stop reason.
- `cleanup_stop_gate_payload`: future cleanup/deletion must be dry-run, reversible where possible, and owner stop-gated.
- `rollback_verification_payload`: future backup/restore, rollback, and post-cleanup verification evidence requirements.
- `phase2_ready_contract`: limited handoff saying Phase 2 may implement a minimal static size-guard slice only after this contract passes.

## Owner And System States
- `DATABASE_SIZE_GUARD_DRAFT`: size-guard boundary exists, but no runnable guard is implemented.
- `DATABASE_SIZE_GUARD_BUDGET_REQUIRED`: future runnable guard must define warning and stop thresholds before it can write state.
- `DATABASE_SIZE_GUARD_RAW_CONTENT_BLOCKED`: raw files, raw database rows, raw payloads, protected-root bodies, and fake data must be blocked.
- `DATABASE_SIZE_GUARD_OCR_FULL_TEXT_BLOCKED`: OCR full text and full document bodies must not be stored in PostgreSQL.
- `DATABASE_SIZE_GUARD_DERIVED_ARTIFACT_BLOCKED`: unbounded derived artifacts, report binaries, vector payloads, and archive bodies must be blocked.
- `DATABASE_SIZE_GUARD_CLEANUP_OWNER_CONFIRMATION_REQUIRED`: cleanup or deletion behavior requires a later owner stop gate.
- `DATABASE_SIZE_GUARD_ROLLBACK_REQUIRED`: future size-related schema or cleanup changes require rollback and backup/restore evidence.
- `DATABASE_SIZE_GUARD_READY_FOR_PHASE2_SLICE`: Phase 1 contract is sufficient for a later minimal static implementation slice.

## Database Size Boundary
- PostgreSQL remains a control-plane store for metadata, refs, state, audit, evidence, migration state, job state, and bounded hot-index metadata only.
- PostgreSQL 只存控制面、状态和热索引.
- PostgreSQL 不存 500GB 原始文件.
- PostgreSQL 不存 OCR 全文.
- PostgreSQL 不存无限制派生产物.
- The size guard protects the 800GB internal disk by blocking raw/OCR/large-file and unbounded derived payloads from PostgreSQL.
- 中文 owner boundary: 保护 800GB 内置盘.
- Future size guard logs must not contain passwords, API keys, credential-bearing DSNs, raw database rows, raw filenames from `/Users/linzezhang/Downloads/IDS_MetaData`, production document content, OCR full text, report binaries, vector payloads, or fake business data.
- Future cleanup behavior must be dry-run first, owner stop-gated for deletion, and backed by rollback/restore evidence.

## Boundary
- 不创建 PostgreSQL database、schema、migration 文件、连接配置、体积统计 runtime 或清理任务.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore、schema diff、VACUUM、清理或体积统计查询.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output、
  PostgreSQL statistics output、cleanup output 或 production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不执行 GitHub upload、PR、merge、app reinstall、batch review 或 upload gate.
- `NO_PHASE2`: this run must not implement schema, migration scripts, size
  statistics, cleanup jobs, retention deletion jobs, connection loading,
  dry-run execution, rollback execution, backup/restore smoke tests,
  hot-index writes, or UI controls.
- `NO_POSTGRES_CONNECTION`: this run must not connect to PostgreSQL.
- `NO_SIZE_GUARD_RUNTIME`: this run must not instantiate table scans,
  size-statistics queries, cleanup jobs, storage monitors, or deletion tasks.
- `NO_LIVE_MIGRATION`: this run must not execute any live or dry-run migration,
  VACUUM, cleanup, backup, restore, schema diff, or size-statistics command.
- `NO_RAW_DB_CONTENT`: future size guards may reference approved source IDs
  later, but must never store raw database content or raw 500GB corpus content.

## Rollback
Revert only `IDS-V0_1-STAGE033-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event
updates, compatibility-test updates, and rendered owner-file changes. Do not
touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs,
indexes, app entries, GitHub state, PostgreSQL data directories, size-statistics
outputs, cleanup outputs, or Phase 2 artifacts.
