# IDS v0.1 STAGE-032 Phase 1 Scope Boundary

## Scope
- Schema version: `ids.stage032.database_connection_pool.phase1.v1`
- Stage: `STAGE-032 · 数据库连接与连接池基线`
- Task: `IDS-V0_1-STAGE032-P1`
- Acceptance: `ACC-STAGE-032`
- Local code: `D06-S003`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T09:44:26Z`

This phase defines a database connection and connection-pool baseline contract
only. It does not create PostgreSQL schema, migration scripts, connection
configuration, database clients, worker jobs, runtime services, healthcheck
outputs, logs, reports, or any executable connection-pool slice.

## P0 Source Evidence

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-032_数据库连接与连接池基线.md` |
| Stage file SHA-256 | `a780cbf5eaf4b565dc0f0e7da1c503275bfa4e066d3409f8a258f13f09a0035a` |
| Stage execution index | STAGE-032 maps to `D06-S003`, `ACC-STAGE-032`, and `stages/STAGE-032_数据库连接与连接池基线.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying the taskpack into the worktree.

## Inputs
Phase 1 defines these future connection-baseline inputs:
- `database_connection_pool_contract_id`: stable id for one connection-pool baseline.
- `backend_connection_profile`: future backend API connection role, timeout, pool, transaction, and healthcheck requirements.
- `worker_connection_profile`: future background worker connection role, queue visibility, retry, backoff, and shutdown requirements.
- `report_task_connection_profile`: future report-generation connection role, read/write boundary, timeout, and idempotency requirements.
- `retrieval_task_connection_profile`: future retrieval/indexing connection role, hot-index access boundary, batch-size guard, and timeout requirements.
- `connection_url_ref`: reference name for future DSN loading; the DSN value must not be committed.
- `credential_source_policy`: environment or local secret-store reference policy; plaintext credentials are forbidden.
- `pool_size_boundary`: upper/lower pool size, overflow, idle timeout, and backpressure expectations for later implementation.
- `statement_timeout_boundary`: maximum statement timeout, lock timeout, idle transaction timeout, and owner-facing timeout reason.
- `transaction_boundary`: explicit transaction scope, commit/rollback behavior, and fail-fast requirements.
- `retry_backoff_boundary`: bounded retry count, backoff class, non-retryable errors, and stop reason.
- `healthcheck_boundary`: future liveness/readiness checks that prove connection availability without touching raw data.
- `schema_migration_dependency_ref`: dependency on STAGE-030 control-plane schema and STAGE-031 migration-safety contracts before any live connection slice.
- `control_plane_storage_boundary`: PostgreSQL stores control-plane metadata, refs, status, audit, evidence, migration state, and job state only.
- `hot_index_storage_boundary`: PostgreSQL may store bounded hot-index metadata and state refs, not raw source bodies.
- `backup_restore_requirement`: future connection changes must preserve backup/restore and rollback evidence paths.

The input contract is metadata-only. It must not include plaintext credentials,
raw filenames from protected roots, raw database rows, production document text,
report binaries, archive bodies, OCR full text, vector payloads, or fabricated
IDS business data.

## Outputs
Phase 1 defines these future owner/system outputs:
- `connection_strategy_summary`: compact Chinese owner-facing summary of backend, worker, report-task, and retrieval-task connection responsibilities.
- `pool_limit_summary`: pool-size, timeout, backpressure, and retry limits, including owner-facing stop reasons.
- `credential_policy_summary`: statement that credentials must come from environment or approved local secret storage and never from committed files.
- `healthcheck_readiness_contract`: future healthcheck shape and failure modes without live execution in this phase.
- `storage_boundary_payload`: explicit statement that PostgreSQL 只存控制面、状态和热索引 and 不存 500GB 原始文件.
- `recovery_requirement_payload`: backup/restore, rollback, transaction, and fail-fast requirements for later runnable slices.
- `phase2_ready_contract`: limited handoff saying Phase 2 may implement a minimal connection-pool slice only after this contract passes.

## Owner And System States
- `CONNECTION_POOL_DRAFT`: connection-pool baseline exists, but no runnable pool is implemented.
- `CONNECTION_POOL_CREDENTIALS_REQUIRED`: future runnable slice requires approved credential loading and must not commit secret values.
- `CONNECTION_POOL_SECRETS_BLOCKED`: plaintext DSN, database password, API key, cloud credential, or credential-bearing config is blocked.
- `CONNECTION_POOL_RAW_CONTENT_BLOCKED`: any attempt to store raw files, raw database rows, raw payloads, report binaries, OCR full text, vector payloads, or fake data is blocked.
- `CONNECTION_POOL_TIMEOUTS_REQUIRED`: future connection behavior must define statement, lock, idle transaction, and shutdown timeouts.
- `CONNECTION_POOL_TRANSACTION_GUARD_REQUIRED`: future write behavior must define transaction boundary, rollback, and idempotency expectations.
- `CONNECTION_POOL_HEALTHCHECK_REQUIRED`: future runnable slice must expose safe healthcheck/readiness evidence without inspecting raw data.
- `CONNECTION_POOL_READY_FOR_PHASE2_SLICE`: Phase 1 contract is sufficient for a later minimal implementation slice.

## Connection Pool Boundary
- Backend API, worker, report task, and retrieval task must use explicit role profiles; shared global mutable connection state is not allowed without a later contract.
- Every future connection pool must have bounded max pool size, overflow, idle timeout, statement timeout, lock timeout, and shutdown behavior.
- Every future transaction path must have fail-fast behavior, rollback expectations, and owner-readable error categories.
- Connection logs must not contain passwords, API keys, credential-bearing DSNs, raw database rows, raw filenames from `/Users/linzezhang/Downloads/IDS_MetaData`, production document content, or report binaries.
- PostgreSQL remains a control-plane store for metadata, status, refs, audit, evidence, migration state, and hot index metadata only.
- PostgreSQL 只存控制面、状态和热索引.
- PostgreSQL 不存 500GB 原始文件.

## Boundary
- 不创建 PostgreSQL database、schema、migration 文件、连接配置或连接池 runtime.
- 不连接 PostgreSQL，不启动 Docker，不安装依赖，不启动 backend/frontend/worker.
- 不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE2`: this run must not implement database clients, pool factories,
  connection loading, schema, migration scripts, healthcheck execution, worker
  integration, report-task integration, retrieval-task integration, hot-index
  writes, or UI controls.
- `NO_POSTGRES_CONNECTION`: this run must not connect to PostgreSQL.
- `NO_CONNECTION_POOL_RUNTIME`: this run must not instantiate backend, worker,
  report, or retrieval connection pools.
- `NO_LIVE_MIGRATION`: this run must not execute any live or dry-run migration command.
- `NO_RAW_DB_CONTENT`: future connections may reference approved source IDs
  later, but must never store raw database content or raw 500GB corpus content.

## Rollback
Revert only `IDS-V0_1-STAGE032-P1` entry/scope evidence, focused tests,
`BATCH031_040_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event
updates, compatibility-test updates, and rendered owner-file changes. Do not
touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs,
indexes, app entries, GitHub state, PostgreSQL data directories, or Phase 2
artifacts.
