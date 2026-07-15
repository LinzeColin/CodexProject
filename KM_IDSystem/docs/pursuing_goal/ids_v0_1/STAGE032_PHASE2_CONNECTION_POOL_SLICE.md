# IDS v0.1 STAGE-032 Phase 2 Connection Pool Slice

## Scope
- Schema version: `ids.stage032.database_connection_pool.phase2.v1`
- Stage: `STAGE-032 · 数据库连接与连接池基线`
- Task: `IDS-V0_1-STAGE032-P2`
- Acceptance: `ACC-STAGE-032`
- Local code: `D06-S003`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 静态连接池策略切片`
- Recorded at UTC: `2026-07-03T10:02:14Z`

This phase implements a static, machine-readable connection-pool strategy
slice for backend, worker, report-task, and retrieval-task roles. It is a
tracked governance and validation artifact only. It does not connect to
PostgreSQL, create a runnable pool, create a DSN file, execute migration
commands, start services, install dependencies, or read raw database content.

## Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-032_数据库连接与连接池基线.md` |
| Stage file SHA-256 | `a780cbf5eaf4b565dc0f0e7da1c503275bfa4e066d3409f8a258f13f09a0035a` |
| Prior phase | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE1_SCOPE_BOUNDARY.md` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json` |
| Static checker | `KM_IDSystem/scripts/check_database_connection_pool.py` |

The taskpack was read from the user-provided v0.1 zip as source evidence in
the earlier STAGE-032 entry work. This phase does not extract the taskpack into
the worktree and does not inspect `/Users/linzezhang/Downloads/IDS_MetaData`.

## Implemented Static Slice

- `CONNECTION_POOL_STATIC_SLICE`: a Git-tracked JSON index defines the database
  connection strategy and guardrails without live database behavior.
- `backend_connection_profile`: backend API role, `ENV:IDS_POSTGRES_DSN` ref,
  bounded pool size, timeout, request-scoped transaction, safe healthcheck, and
  no raw-content storage.
- `worker_connection_profile`: background worker role, bounded pool size,
  job-scoped transaction, bounded retry/backoff, shutdown behavior, and no
  raw-content storage.
- `report_task_connection_profile`: report generation task role, idempotent
  transaction boundary, bounded read/write behavior, and no report-binary or raw
  payload storage in PostgreSQL.
- `retrieval_task_connection_profile`: retrieval and hot-index task role,
  bounded batch transaction, hot-index metadata boundary, and no raw document
  bodies, OCR full text, vector payloads, or raw database rows.
- `check_database_connection_pool.py`: validates the tracked index and prints a
  JSON report to stdout only; it does not persist reports or runtime outputs.

## Guardrails

- Credential guard: all profiles use `ENV:IDS_POSTGRES_DSN` as a reference
  name only. Plaintext DSN values, API keys, database passwords,
  credential-bearing config files, cloud credentials, and secret echoing are
  forbidden.
- Pool-size guard: all four profiles have bounded pool sizes and aggregate
  `max_pool_size <= 10`; unbounded pools and overflow are forbidden.
- Timeout guard: statement timeout, lock timeout, idle timeout, and shutdown
  timeout are bounded so later runnable code can fail fast with owner-readable
  stop reasons.
- Transaction guard: backend requests, worker jobs, report tasks, and retrieval
  batches must have explicit transaction boundaries, rollback requirements, and
  idempotency requirements.
- Retry/backoff guard: retries are bounded, non-destructive, owner-explainable,
  and must stop on authentication, migration, schema mismatch, destructive
  migration, or raw metadata boundary errors.
- Healthcheck guard: future healthchecks are safe readiness checks only and
  must not write database rows, echo secrets, or touch raw metadata.
- Storage guard: PostgreSQL remains control-plane and hot-index metadata only.
  It may store ids, refs, status, evidence refs, audit refs, migration refs, and
  bounded hot-index metadata; it must not store 500GB raw files, raw database
  rows, production document bodies, archive bodies, OCR full text, vector
  payloads, report binaries, or secrets.
- Real-data guard: the system may use real user-approved data only. 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` is recorded as a path-only,
read-only real database source boundary. This phase does not read, list, hash,
open, copy, move, delete, modify, dump, scan, normalize, or commit any content
from that location. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容.

## Explicit Non-Goals

- `NO_POSTGRES_CONNECTION`: no local or remote PostgreSQL connection is opened.
- `NO_CONNECTION_POOL_RUNTIME`: no backend, worker, report, or retrieval pool is
  instantiated.
- `NO_LIVE_MIGRATION`: no migration dry-run, apply, rollback, backup, restore,
  schema diff, checksum verification, or recovery smoke command is executed.
- `NO_RAW_DB_CONTENT`: no raw metadata database content or raw 500GB corpus
  content is read, listed, hashed, opened, copied, moved, deleted, modified,
  dumped, scanned, normalized, or committed.
- No runtime output, database, manifest, evidence ledger, audit log, report,
  PDF, screenshot, JSON output file, document/chunk/job/import row, parser
  output, or production data artifact is generated.
- No GitHub upload, PR, merge, app reinstall, batch review, upload gate, or
  Phase 3 work is performed.

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE2_CONNECTION_POOL_SLICE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json`
- `KM_IDSystem/scripts/check_database_connection_pool.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_database_connection_pool.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## Rollback

Revert only `IDS-V0_1-STAGE032-P2` evidence, the static connection-pool index,
the static checker, focused tests, Stage005 validator/test updates,
`BATCH031_040_UPLOAD_LOCK.yaml`, roadmap/event updates, compatibility-test
updates, and rendered owner-file changes. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, runtime
data, reports, outputs, manifests, evidence ledgers, audit logs, app entries,
GitHub state, PostgreSQL data directories, or Phase 3 artifacts.
