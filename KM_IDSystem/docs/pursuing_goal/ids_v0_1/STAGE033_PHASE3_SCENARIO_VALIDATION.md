# IDS v0.1 STAGE-033 Phase 3 Scenario Validation

## Scope
- Schema version: `ids.stage033.database_size_guard.phase3.v1`
- Stage: `STAGE-033 · 数据库体积护栏`
- Task: `IDS-V0_1-STAGE033-P3`
- Acceptance: `ACC-STAGE-033`
- Local code: `D06-S004`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 3 · 数据库体积护栏 专项验证与异常场景`
- Recorded at UTC: `2026-07-03T11:56:33Z`

This phase validates database-size guard scenarios from tracked Git contracts
only. It does not connect to PostgreSQL, execute live migration dry-run, apply,
rollback, backup, restore, schema diff, recovery smoke, size query, VACUUM,
reindex, cleanup, retention deletion, service startup, dependency install, raw
metadata inspection, or runtime-output writes.

## Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md` |
| Stage file SHA-256 | `454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777` |
| Prior phase | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json` |
| Static checker function | `build_stage033_scenario_validation_report` in `KM_IDSystem/scripts/check_database_size_guard.py` |

## Static Scenario Results

`build_stage033_scenario_validation_report` validates these static scenarios:

- `migration_dry_run`: verifies the future migration identity, source refs,
  static schema-change plan, and `execute_migration=false`. It does not execute
  a live dry-run.
- `repeat_execution`: verifies stable `database_size_guard_contract_id` and no
  runtime-output writes, so repeated checker execution cannot mutate database
  state, size-statistics output, audit log, or cleanup output.
- `failure_rollback`: verifies rollback, backup/restore, owner stop gate, and
  cleanup dry-run requirements from tracked contracts. It does not execute live
  rollback or restore.
- `recovery_smoke`: verifies recovery-smoke prerequisites as a static contract;
  no PostgreSQL connection, readiness query, backup, restore, or raw metadata
  access is performed.
- `raw_large_file_block`: verifies PostgreSQL 不存 500GB 原始文件, raw metadata
  database content, raw rows, source bodies, archive bodies, report binaries,
  media blobs, or other large file payloads.
- `ocr_full_text_block`: verifies PostgreSQL 不存 OCR 全文, document bodies,
  unbounded extracted text, or chunk body text.
- `derived_artifact_limit`: verifies PostgreSQL 不存无限制派生产物 and only allows
  bounded refs or re-creatable hot-index metadata.
- `database_size_budget`: verifies policy thresholds for protecting the 800 GiB
  internal disk while explicitly recording measured database size as
  `NOT_MEASURED_BY_POLICY`.
- `connection_pool_boundary`: verifies this size guard does not increase the
  STAGE-032 aggregate pool budget, overflow, or backpressure contract.
- `transaction_boundary`: verifies the scenario is bounded by STAGE-031
  migration safety, STAGE-032 connection-pool dependency, dry-run cleanup, and
  rollback verification.
- `constraint_error_explanations`: verifies owner-facing explanations exist for
  storage scope, database size budget, row payload, retention cleanup,
  connection pool budget, rollback verification, raw metadata boundary, and
  real-data-only constraints.

All scenarios must return `PASS` from tracked contracts before Phase 3 can be
accepted locally.

## Explicit Non-Goals

- `NO_PHASE4`: this run does not produce schema diff closeout, migration output
  closeout, recovery test log closeout, destructive migration confirmation,
  final rollback steps, backup restore steps, Chinese owner feedback closeout,
  stage review, batch review, upload gate, GitHub upload, PR, merge, or app
  reinstall.
- 不连接 PostgreSQL.
- 不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不运行 size query、VACUUM、reindex、cleanup 或 retention deletion.
- 不创建 live schema、migration file、DSN、credential-bearing connection config、
  database/runtime data directory、runtime output、statistics output、cleanup
  output、report、PDF、screenshot、manifest、evidence ledger、audit log、
  document/chunk/job/import row、parser output 或 production data artifact.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only, read-only real
database source boundary. Phase 3 does not read, list, hash, open, copy, move,
delete, modify, dump, scan, normalize, or commit content from that location.

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/scripts/check_database_size_guard.py#build_stage033_scenario_validation_report`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## Rollback

Revert only `IDS-V0_1-STAGE033-P3` evidence, checker scenario-report changes,
focused tests, Stage005 validator/test updates, `BATCH031_040_UPLOAD_LOCK.yaml`,
roadmap/event updates, compatibility-test updates, and rendered owner-file
changes. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
`00_ORIGINAL_RAW_DATA`, runtime data, reports, outputs, manifests, evidence
ledgers, audit logs, app entries, GitHub state, PostgreSQL data directories,
size-statistics outputs, cleanup outputs, or Phase 4 artifacts.
