# STAGE-035 Phase 3 · 数据库恢复冒烟测试专项验证与异常场景

- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Phase: `Phase 3 · 数据库恢复冒烟测试专项验证与异常场景`
- Task ID: `IDS-V0_1-STAGE035-P3`
- Acceptance ID: `ACC-STAGE-035`
- Schema: `ids.stage035.database_recovery_smoke.phase3.v1`
- Checker: `KM_IDSystem/scripts/check_database_recovery_smoke.py#build_stage035_scenario_validation_report`
- Input index: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/stage035_database_recovery_smoke_index.json`
- Recorded at UTC: `2026-07-10T15:04:06Z`

## 目标与结论边界

本阶段按 P0 taskpack 验证 migration dry-run、重复执行、失败回滚、恢复冒烟、
raw/大文件与无限制派生产物阻断、连接池、事务边界和约束错误解释。

所有结果只来自 Git 已追踪的 STAGE-030..035 合同、机器索引和 checker。
场景 `status=PASS` 表示静态工程合同按预期约束了该场景，不表示执行过真实
PostgreSQL 操作。当前没有 owner 授权真实 metadata dump：

- `execution_ready=false`
- `observed_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`
- `live_execution_performed=false`
- 无 owner 授权真实 metadata dump，恢复执行保持阻断。

不执行 live migration dry-run、apply、rollback、backup、restore、schema diff 或 recovery smoke。

## P0 Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack Stage | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md` |
| Stage file SHA-256 | `2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62` |
| P0 Phase 3 item 1 | migration dry-run、重复执行、失败回滚和恢复冒烟 |
| P0 Phase 3 item 2 | 不写入原始大文件或无限制派生产物 |
| P0 Phase 3 item 3 | 连接池、事务边界和约束错误可解释 |
| Phase 2 contract | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_recovery_smoke/stage035_database_recovery_smoke_index.json` |

Phase 3 没有提取 taskpack、读取 metadata dump 或检查
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## 场景矩阵

| Scenario | 静态验证点 | 当前结果 | 真实执行状态 |
|---|---|---|---|
| `migration_dry_run` | STAGE-031 dry-run/rollback/backup 要求存在；连接、migration、backup、restore、schema diff 均禁止 | PASS | 未执行 |
| `repeat_execution` | 重复调用只读取相同 tracked index/dependencies，并输出确定性 stdout JSON | PASS | 未写 runtime artifact |
| `failure_rollback` | rollback、target quarantine、source preservation、backup checkpoint 与 post-rollback evidence 均为强制要求 | PASS | 未执行 rollback/restore |
| `recovery_smoke` | 合同有效，但无 owner 授权 dump，必须保持 blocked | PASS | `BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP` |
| `owner_dump_absence_stop_gate` | dump identity、checksum evidence、owner approval 缺失时停止 | PASS | 禁止用 fake dump/rows 替代 |
| `raw_large_file_block` | STAGE-030/033 与 storage/raw boundary 均阻断 500GB 原始文件和 raw rows | PASS | 未读写原始内容 |
| `unbounded_derived_artifact_block` | STAGE-033 继续阻断无限制派生产物，恢复合同不能覆盖 | PASS | 未生成派生产物 |
| `connection_pool_boundary` | STAGE-032 aggregate pool 10、overflow 0、backpressure，且不创建连接/config | PASS | 未连接 PostgreSQL |
| `transaction_boundary` | 只验证 schema/migration/pool 静态边界 | PASS | 未打开、提交或回滚事务 |
| `constraint_error_explanations` | 11 个场景都有非空中文 owner 解释 | PASS | 无 runtime error output |
| `source_non_interference` | isolated target、source preservation 与禁止 source mutation/migration/deletion | PASS | source 未被访问或修改 |

## 恢复冒烟解释

`recovery_smoke` 的 `PASS` 只表示系统正确执行了停止策略：

1. Phase 2 工程合同有效。
2. `owner_authorized_real_dump_available=false`。
3. `execution_ready=false`。
4. `execute_pg_restore=false`、`execute_psql=false`、`execute_restore=false`、
   `execute_healthcheck=false`。
5. `observed_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`。
6. `live_execution_performed=false`。

它不证明 dump 可恢复、schema 可在真实目标运行、数据行一致、healthcheck 通过、
生产 readiness 或 owner 已授权。未来只有在单独 owner 授权 run 中获得真实 dump
身份、checksum evidence、隔离目标和凭证引用后，才允许重新评估 live recovery。

## 约束错误解释

- `migration_dry_run`: 缺少 STAGE-031 dry-run/rollback/backup 要求，或任何 live
  migration flag 被打开时 FAIL。
- `repeat_execution`: source refs 不一致、依赖缺失、读取 dump 或写 runtime output
  时 FAIL。
- `failure_rollback`: 缺少 rollback/quarantine/source-preservation evidence，或
  backup/restore/migration 被执行时 FAIL。
- `recovery_smoke`: 合同无效、执行状态未阻断，或 restore/healthcheck action 被打开时 FAIL。
- `owner_dump_absence_stop_gate`: 缺失真实 dump 时未停止，或允许 fake/fabricated
  替代时 FAIL。
- `raw_large_file_block`: PostgreSQL 允许 raw files/raw rows，或原始路径不再
  path-only 时 FAIL。
- `unbounded_derived_artifact_block`: STAGE-033 不再 authoritative 或允许无界派生产物时 FAIL。
- `connection_pool_boundary`: pool 超预算、overflow 非零、无 backpressure 或创建连接配置时 FAIL。
- `transaction_boundary`: 连接、psql 或 migration 执行被打开时 FAIL。
- `constraint_error_explanations`: 场景集合不完整或中文解释为空时 FAIL。
- `source_non_interference`: source 与 target 未分离，或允许 source mutation、
  migration、deletion/restore write 时 FAIL。

## 原始数据与真实数据边界

`/Users/linzezhang/Downloads/IDS_MetaData` 只作为本机 `path-only` 地址进入 Git
合同。本阶段不读取、列出、hash、打开、复制、移动、删除、修改、dump、扫描、
normalize 或提交该目录内容，也不记录 raw filenames、table rows、schema details、
business values、dump bytes、checksum 或派生数据。

不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据。
本阶段没有 fixture，也没有用测试数据模拟 live restore；负向测试只修改内存中的
合同字典，不创建文件、数据库行或业务数据。

## No-Go

- `NO_PHASE4`
- `NO_POSTGRES_CONNECTION`
- `NO_LIVE_MIGRATION`
- `NO_LIVE_RESTORE`
- `NO_DUMP_ACCESS`
- `NO_RAW_DB_CONTENT`
- `NO_RUNTIME_OUTPUT`
- `NO_FAKE_DATA`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE_REVIEW_THIS_RUN`

## 验收证据

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage035_database_recovery_smoke.Stage035DatabaseRecoverySmokePhase3Tests -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage035_phase3_recovery_smoke_scenarios -q`
- `python3 -B KM_IDSystem/scripts/check_database_recovery_smoke.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## 回滚

Revert `STAGE035_PHASE3_SCENARIO_VALIDATION.md`、checker 的 Phase 3 scenario
report、Stage035/Stage005 tests、Stage005 validator、batch lock、roadmap/event、
必要兼容测试和 owner render 变更。不得触碰
`/Users/linzezhang/Downloads/IDS_MetaData`、`00_ORIGINAL_RAW_DATA`、metadata dump、
source/runtime database、PostgreSQL data directory、reports、outputs、manifest、
evidence ledger、audit log、app entries、GitHub state 或 Phase 4 artifacts。
