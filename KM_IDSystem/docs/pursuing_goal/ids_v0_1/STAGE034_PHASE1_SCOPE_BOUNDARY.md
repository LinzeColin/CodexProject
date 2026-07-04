# IDS v0.1 STAGE-034 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage034.data_retention_table.phase1.v1`
- Stage: `STAGE-034 · 数据保留表`
- Task: `IDS-V0_1-STAGE034-P1`
- Acceptance: `ACC-STAGE-034`
- Local code: `D06-S005`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-04T00:17:08Z`

This phase defines a data retention table contract only. It does not create
PostgreSQL schema, migration scripts, retention queries, cleanup jobs, deletion
jobs, connection configuration, database clients, runtime logs, reports, or any
executable retention slice.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md` |
| Stage file SHA-256 | `af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d` |
| Stage execution index | STAGE-034 maps to `D06-S005`, `ACC-STAGE-034`, and `stages/STAGE-034_数据保留表.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future data-retention table inputs:
- `data_retention_table_contract_id`: stable id for one retention table contract.
- `control_plane_schema_ref`: dependency on the STAGE-030 control-plane schema contract.
- `schema_migration_safety_ref`: dependency on the STAGE-031 migration rollback and validation contract.
- `connection_pool_contract_ref`: dependency on the STAGE-032 connection and pool baseline.
- `database_size_guard_ref`: dependency on the STAGE-033 database size guard and raw/OCR/large-file block.
- `retention_subject_class`: controlled enum for `temporary_file`, `cache`, `old_index`, `log`, and `report_snapshot`.
- `temp_file_retention_policy`: future TTL, owner reason, and cleanup mode for 临时文件.
- `cache_retention_policy`: future TTL, rebuildability, and cleanup mode for 缓存.
- `old_index_retention_policy`: future retention and rebuild policy for 旧索引.
- `log_retention_policy`: future log retention, redaction, compaction, and audit policy for 日志.
- `report_snapshot_retention_policy`: future snapshot retention, owner hold, and regeneration policy for 报告快照.
- `retention_ttl_policy`: future TTL field, warning window, expiration reason, and owner-readable stop reason.
- `owner_hold_policy`: future manual hold, compliance hold, or owner hold flag before cleanup.
- `cleanup_dry_run_requirement`: future cleanup must dry-run and report impact before any destructive action.
- `deletion_stop_gate`: future deletion/pruning/compaction requires explicit owner stop-gate approval.
- `audit_evidence_ref`: event/evidence reference required for every future retention transition.
- `rollback_restore_ref`: future restore, rebuild, or rollback evidence ref required after cleanup.

The input contract is metadata-only. It must not include plaintext credentials,
raw filenames from protected roots, raw database rows, production document text,
report binaries, archive bodies, OCR full text, vector payloads, raw logs,
unbounded derived artifacts, or fabricated IDS business data.

## Outputs
Phase 1 defines these future owner/system outputs:
- `data_retention_summary`: compact Chinese owner-facing summary of what is retained, why, and for how long.
- `retention_subject_payload`: structured subject class for 临时文件, 缓存, 旧索引, 日志, and 报告快照.
- `retention_policy_payload`: TTL, keep-until, owner hold, expiration reason, and cleanup mode.
- `cleanup_dry_run_payload`: future dry-run impact summary, no-delete proof, and owner stop reason.
- `deletion_stop_gate_payload`: future explicit approval state before deletion, compaction, pruning, or cache eviction.
- `rollback_restore_payload`: future restore, rebuild, rollback, and post-cleanup verification requirements.
- `phase2_ready_contract`: limited handoff saying Phase 2 may implement a minimal static data-retention table slice only after this contract passes.

## Owner And System States
- `DATA_RETENTION_TABLE_DRAFT`: retention table boundary exists, but no runnable table or cleanup behavior is implemented.
- `DATA_RETENTION_TEMP_FILES_POLICY_DEFINED`: temporary-file retention fields are defined.
- `DATA_RETENTION_CACHES_POLICY_DEFINED`: cache retention and rebuildability fields are defined.
- `DATA_RETENTION_OLD_INDEXES_POLICY_DEFINED`: old-index retention and rebuild policy fields are defined.
- `DATA_RETENTION_LOGS_POLICY_DEFINED`: log retention, redaction, compaction, and audit fields are defined.
- `DATA_RETENTION_REPORT_SNAPSHOTS_POLICY_DEFINED`: report snapshot retention, owner hold, and regeneration fields are defined.
- `DATA_RETENTION_CLEANUP_OWNER_CONFIRMATION_REQUIRED`: cleanup, deletion, compaction, pruning, or cache eviction requires a later owner stop gate.
- `DATA_RETENTION_ROLLBACK_REQUIRED`: future cleanup or deletion behavior requires rollback/restore and post-cleanup verification evidence.
- `DATA_RETENTION_READY_FOR_PHASE2_SLICE`: Phase 1 contract is sufficient for a later minimal static implementation slice.

## Data Retention Boundary
- PostgreSQL may store bounded control-plane retention metadata and artifact refs only.
- PostgreSQL must not store raw file bodies, OCR full text, report binaries, raw logs, protected-root raw database rows, or unbounded derived artifacts.
- Data-retention policy covers 临时文件, 缓存, 旧索引, 日志, and 报告快照.
- Phase 1 does not delete files, prune report snapshots, compact logs, evict caches, rebuild indexes, or clean temporary directories.
- 中文 owner boundary: 本阶段只定义保留策略字段，不执行删除.
- Future retention logs must not contain passwords, API keys, credential-bearing DSNs, raw database rows, raw filenames from `/Users/linzezhang/Downloads/IDS_MetaData`, production document content, OCR full text, report binaries, vector payloads, raw log bodies, or fake business data.
- Future cleanup behavior must be dry-run first, owner stop-gated for deletion, and backed by rollback/restore evidence.

## Boundary
- 不创建 PostgreSQL database、schema、migration 文件、连接配置、数据保留 runtime 或清理任务.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore、schema diff、清理、删除、retention 或恢复冒烟.
- 不执行删除、清理、log compaction、cache eviction、old-index rebuild 或 report snapshot pruning.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output、
  PostgreSQL statistics output、retention output、cleanup output、deletion output 或
  production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不执行 GitHub upload、PR、merge、app reinstall、batch review 或 upload gate.
- `NO_PHASE2`: this run must not implement schema, migration scripts, retention
  tables, cleanup jobs, deletion jobs, retention schedulers, connection
  loading, dry-run execution, rollback execution, backup/restore smoke tests,
  hot-index writes, or UI controls.
- `NO_POSTGRES_CONNECTION`: this run must not connect to PostgreSQL.
- `NO_RETENTION_CLEANUP_RUNTIME`: this run must not instantiate cleanup jobs,
  deletion jobs, retention scans, log compaction, cache eviction, old-index
  rebuilds, report snapshot pruning, storage monitors, or retention schedulers.
- `NO_LIVE_MIGRATION`: this run must not execute any live or dry-run migration,
  cleanup, deletion, backup, restore, schema diff, retention action, or recovery
  smoke command.
- `NO_RAW_DB_CONTENT`: future retention tables may reference approved source IDs
  later, but must never store raw database content or raw 500GB corpus content.

## Rollback
Revert only `IDS-V0_1-STAGE034-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event
updates, compatibility-test updates, and rendered owner-file changes. Do not
touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs,
indexes, app entries, GitHub state, PostgreSQL data directories, retention
outputs, cleanup outputs, deletion outputs, or Phase 2 artifacts.
