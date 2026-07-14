# IDS v0.1 STAGE-035 Phase 2 Database Recovery Smoke Slice

## Scope
- Schema version: `ids.stage035.database_recovery_smoke.phase2.v1`
- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Task: `IDS-V0_1-STAGE035-P2`
- Acceptance: `ACC-STAGE-035`
- Local code: `D06-S006`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 静态恢复 preflight 合同切片`
- Recorded at UTC: `2026-07-10T14:34:59Z`

This phase implements a Git-tracked, stdout-only recovery preflight contract.
It validates the existing STAGE-030 through STAGE-034 contracts without opening
a metadata dump or connecting to PostgreSQL. The result is deliberately split:
`contract_valid=true` and `execution_ready=false`.

Execution state is
`BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`: 无 owner 授权真实
metadata dump，恢复执行保持阻断。

## Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md` |
| Stage file SHA-256 | `2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62` |
| Prior phase | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE1_SCOPE_BOUNDARY.md` |
| STAGE-030 schema/index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json` |
| STAGE-031 migration safety | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json` |
| STAGE-032 connection pool | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json` |
| STAGE-033 database size | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json` |
| STAGE-034 data retention | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/stage035_database_recovery_smoke_index.json` |
| Static checker | `KM_IDSystem/scripts/check_database_recovery_smoke.py` |

The taskpack source was read directly in Phase 1. Phase 2 reads only tracked
contracts. It does not extract the taskpack or inspect
`/Users/linzezhang/Downloads/IDS_MetaData`.

## Implemented Static Contract

- `database_recovery_smoke_contract_id` identifies one static preflight
  contract with state `STATIC_RECOVERY_PREFLIGHT_CONTRACT_VALID`.
- `metadata_dump_contract` requires
  `owner_authorized_real_dump_required=true` while recording
  `owner_authorized_real_dump_available=false`. No dump reference, bytes,
  path, checksum, row count, or content identity is invented.
- `restore_target_contract` requires an isolated, owner-authorized,
  non-production target and blocks production targets and source mutation.
- `schema_migration_compatibility` reuses the tracked STAGE-030 schema and
  STAGE-031 migration-safety contracts. This phase creates no schema or
  migration file and runs no migration.
- `connection_pool_guard` preserves the STAGE-032 aggregate pool limit of 10,
  overflow 0, backpressure, timeout, transaction, and secret boundaries.
- `database_size_guard` keeps STAGE-033 authoritative and does not perform a
  runtime size query or weaken raw/OCR/large/unbounded-payload blocks.
- `quality_constraint_guard` requires fail-closed checks, real-data-only
  evidence, and a Chinese owner-readable failure reason.
- `storage_boundary` permits only bounded control-plane metadata, state, refs,
  audit/evidence, migration/retention state, and hot-index metadata. It blocks
  raw files, raw database rows, source bodies, OCR full text, report binaries,
  vector payloads, secrets, and unbounded derived artifacts.
- `restore_validation_contract` defines future checks for dump identity,
  compatibility, schema/migration/table/constraint/index state, bounded real
  metadata counts, readiness, and no-raw-payload evidence.
- `rollback_contract` requires target quarantine, source non-interference,
  rollback/restore evidence, post-rollback verification, and an owner stop gate
  before target cleanup.
- `audit_contract` requires fact-level event/evidence refs and Chinese reasons
  without credentials or raw values.
- `real_data_only_guard` forbids fake IDS business data, fake rows, fabricated
  dumps, placeholder corpus, and fabricated evidence.

## Static Checker Result

`python3 -B KM_IDSystem/scripts/check_database_recovery_smoke.py` reads the
tracked index and its tracked STAGE-030 through STAGE-034 dependencies, then
prints JSON to stdout only. The accepted Phase 2 result is:

- `contract_valid=true`
- `execution_ready=false`
- `execution_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`
- `block_reason_zh=无 owner 授权真实 metadata dump，恢复执行保持阻断。`

An invalid in-memory contract fails closed as
`BLOCKED_INVALID_RECOVERY_CONTRACT`. The negative test mutates only an in-memory
copy and creates no files or data. Contract identity, required control-plane
table identity, and the complete runtime-policy key set are mandatory; a
tampered contract id, missing guard, extra guard, or non-false runtime action
also invalidates the contract.

## Explicit Non-Goals And Stop Conditions

- 不执行 pg_dump、pg_restore、psql、migration、backup、restore 或 recovery smoke.
- 不连接 PostgreSQL，不创建 database、schema、migration、DSN、connection
  config、credential、restore target、runtime data directory 或 service.
- 不读取、列出、hash、打开、复制、移动、删除、修改、inspect、dump、scan、
  normalize 或恢复 metadata dump、backup、database file 或
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不写 runtime output、database、dump、backup、manifest、evidence ledger、
  audit log、report、PDF、screenshot、JSON output file、restore output、
  recovery log、cleanup output 或 production data artifact.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据.
- 不启动服务、不安装依赖、不调用外部 API、不上传 GitHub、不创建或合并
  PR、不重装 app entry、不运行 stage/batch review 或 upload gate.
- `NO_PHASE3`: this run stops after the Phase 2 static contract, checker,
  governance evidence, and local verification.

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/stage035_database_recovery_smoke_index.json`
- `KM_IDSystem/scripts/check_database_recovery_smoke.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage035_database_recovery_smoke.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## Rollback

Revert only `IDS-V0_1-STAGE035-P2` documentation, machine index, static
checker, focused tests, Stage005 validator/test updates, batch lock,
roadmap/event updates, compatibility-test updates, and rendered owner-file
changes. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
`00_ORIGINAL_RAW_DATA`, source/runtime databases, dumps, backups, reports,
outputs, manifests, evidence ledgers, audit logs, indexes, app entries, GitHub
state, PostgreSQL data directories, restore targets, recovery outputs, or Phase
3 artifacts.
