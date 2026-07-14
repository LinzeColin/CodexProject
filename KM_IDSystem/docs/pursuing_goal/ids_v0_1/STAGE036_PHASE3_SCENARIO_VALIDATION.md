# STAGE-036 Phase 3 · 数据库质量约束专项验证与异常场景

- Stage: `STAGE-036 · 数据库质量约束`
- Phase: `Phase 3 · 数据库质量约束专项验证与异常场景`
- Task ID: `IDS-V0_1-STAGE036-P3`
- Acceptance ID: `ACC-STAGE-036`
- Schema: `ids.stage036.database_quality_constraints.phase3.v1`
- Checker: `KM_IDSystem/scripts/check_database_quality_constraints.py#build_stage036_scenario_validation_report`
- Input index: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/stage036_database_quality_constraints_index.json`
- Migration contract: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_quality_constraints/002_database_quality_constraints.sql`
- Recorded at UTC: `2026-07-10T17:20:42Z`

## 目标与结论边界

本阶段按 P0 taskpack 验证 migration dry-run、重复执行、失败回滚、恢复冒烟、
raw/大文件和无限制派生产物阻断、连接池、事务边界及约束错误解释。

所有结果来自同一份 Git tracked index、migration、STAGE-030 baseline 和
STAGE-031..035 contracts。场景 `status=PASS` 表示静态工程合同按预期覆盖并阻断
该场景，不表示执行过真实 PostgreSQL 操作。当前没有 owner 授权真实数据 profile：

- `scenario_validation_valid=true`
- `execution_ready=false`
- `execution_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE`
- `live_execution_performed=false`
- `migration_dry_run_performed=false`
- `migration_apply_performed=false`
- `constraint_validation_performed=false`
- `rollback_performed=false`
- `backup_performed=false`
- `restore_performed=false`
- `recovery_smoke_performed=false`

本阶段不执行 live migration dry-run、apply、constraint validation、rollback、
backup、restore、schema diff 或 recovery smoke。

## P0 Source Binding

| Check | Result |
|---|---|
| P0 taskpack ZIP | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack Stage | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md` |
| Stage file SHA-256 | `13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b` |
| P0 Phase 3 item 1 | migration dry-run、重复执行、失败回滚和恢复冒烟 |
| P0 Phase 3 item 2 | 数据库不写入原始大文件或无限制派生产物 |
| P0 Phase 3 item 3 | 连接池、事务边界和约束错误可解释 |
| Phase 2 contract | `STAGE036_PHASE2_DATABASE_QUALITY_CONSTRAINTS_SLICE.md` |

Phase 3 没有解压 taskpack 到仓库，没有读取数据库或
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## 场景矩阵

| Scenario | 静态验证点 | 当前结果 | 真实执行状态 |
|---|---|---|---|
| `migration_dry_run` | STAGE-031 safety、apply guards、`ON_ERROR_STOP`、single transaction 和全部 live flags=false | PASS | 未执行 dry-run/apply |
| `repeat_execution` | table/index `IF NOT EXISTS`、九个 `pg_constraint` guards、同快照 deterministic stdout | PASS | 未重复执行 SQL |
| `failure_rollback` | down 覆盖九个候选、非空 registry rollback guard、single transaction | PASS | 未执行 rollback |
| `recovery_smoke` | 合同有效但无 owner 授权 profile，必须保持 expected blocked | PASS | 未执行 recovery |
| `candidate_constraint_semantics` | 九个 id、table、columns、validation kind 和 SQL clauses 精确一致 | PASS | 未安装约束 |
| `duplicate_uniqueness_profile_gate` | `ids_chunks(document_id, chunk_ordinal)` 等待真实 duplicate-count profile | PASS | 未查询真实行 |
| `existing_foreign_key_integrity` | 三条 STAGE-030 外键精确保留，不推导 text-ref 外键 | PASS | 未修改 FK |
| `state_registry_deferred` | registry 为空、回滚受保护、values/transitions 归 STAGE-037 | PASS | 未 seed state |
| `raw_large_file_block` | raw files/rows/bodies/vectors/binaries 禁止进入 PostgreSQL，raw root path-only | PASS | 未读写原始内容 |
| `unbounded_derived_artifact_block` | STAGE-033 无界派生产物禁令与 `write_runtime_outputs=false` | PASS | 未生成派生产物 |
| `connection_pool_boundary` | aggregate pool 10、overflow 0、backpressure、无 pool/connection | PASS | 未创建连接池 |
| `transaction_boundary` | future apply 需单事务；当前 connect/migration/validation=false | PASS | 未打开事务 |
| `constraint_error_explanations` | 14 个场景均有非空中文 owner 解释和 no-live 语义 | PASS | 无 runtime error output |
| `source_non_interference` | STAGE-035 isolated target/source preservation 继续有效 | PASS | source 未访问或修改 |

## 核心异常解释

### Migration dry-run

`migration_dry_run=PASS` 只证明 tracked migration 具备 STAGE-031 所需的
owner profile、backup checkpoint、rollback plan、`ON_ERROR_STOP` 和 single
transaction 合同，并且 runtime policy 禁止执行。它不证明 SQL 能在任何真实数据库
上成功运行。

### Repeat execution

`repeat_execution=PASS` 证明静态 SQL 对 registry table/index 使用存在性保护，并为
九个候选约束检查 `pg_constraint`。checker 两次读取同一 tracked 快照时结果一致。
它不证明 migration 已在 PostgreSQL 上重复运行，也不证明并发执行安全。

### Failure rollback

`failure_rollback=PASS` 证明 down contract 覆盖 Stage036 候选，并在
`ids_state_value_registry` 非空时拒绝删表。future rollback 仍必须在单事务、backup、
owner 授权和 STAGE-035 recovery 边界内执行。本阶段没有删除任何约束、表或行。

### Recovery smoke

`recovery_smoke=PASS` 表示停止策略按预期成立：

1. Phase 2 contract 有效。
2. `real_data_profile_available=false`。
3. `execution_ready=false`。
4. migration/backup/restore/recovery actions 全部为 false。
5. `observed_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE`。
6. `live_execution_performed=false`。

它不证明备份可恢复、约束能应用、现有行 clean、数据库可连接或 production ready。

## 约束错误解释

- `migration_dry_run`: 缺少 migration safety、apply guard、单事务要求，或任何 live
  action 被打开时 FAIL。
- `repeat_execution`: table/index 存在性保护或任一候选 guard 缺失、错表、增加
  `OR TRUE` 等额外布尔谓词时 FAIL。
- `failure_rollback`: down coverage、registry 非空保护、完整 `EXISTS -> variable ->
  IF -> RAISE` 控制流或单事务要求缺失/反转/附加 `AND FALSE`，或 registry
  `DROP TABLE` 出现在保护门之前/重复出现时 FAIL。
- `recovery_smoke`: 合同无效、状态未按预期阻断，或 restore/recovery action 打开时 FAIL。
- `candidate_constraint_semantics`: id、table、columns、validation kind 或 SQL clause
  任一漂移时 FAIL。
- `duplicate_uniqueness_profile_gate`: 无真实 duplicate profile 却允许 apply 时 FAIL。
- `existing_foreign_key_integrity`: 三条 tracked FK 缺失、增加未授权关系或 baseline
  不一致时 FAIL。
- `state_registry_deferred`: registry 被预填、状态 values/transitions 被提前定义或
  rollback guard 缺失时 FAIL。
- `raw_large_file_block`: raw root 不再 path-only 或允许 raw read/write 时 FAIL。
- `unbounded_derived_artifact_block`: 允许无界派生产物或 runtime output 时 FAIL。
- `connection_pool_boundary`: pool 超过 10、overflow 非零、缺少 backpressure 或创建
  pool/connection 时 FAIL。
- `transaction_boundary`: 缺少 `ON_ERROR_STOP`/single transaction，或打开 live
  connection/migration/validation 时 FAIL。
- `constraint_error_explanations`: 场景集合不完整、中文解释为空或把静态 PASS 写成
  live 成功时 FAIL。
- `source_non_interference`: 允许 source mutation/migration/restore write 时 FAIL。

## 原始数据与真实数据边界

`/Users/linzezhang/Downloads/IDS_MetaData` 仅作为本机 `path-only` 地址进入 Git
合同。本阶段不读取、列出、hash、打开、复制、移动、删除、修改、dump、扫描、
normalize、restore 或提交其内容，也不记录 raw filenames、table rows、business
values、schema details、checksum 或派生数据。

不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据。
负向测试只修改内存中的合同字典或 SQL 字符串，不创建 fixture、数据库行、文件或
业务数据，也不把 mutation 当作真实 IDS 数据。

## No-Go

- `NO_PHASE4`
- `NO_POSTGRES_CONNECTION`
- `NO_LIVE_MIGRATION`
- `NO_LIVE_CONSTRAINT_VALIDATION`
- `NO_LIVE_BACKUP_RESTORE_RECOVERY`
- `NO_RAW_DB_CONTENT`
- `NO_RUNTIME_OUTPUT`
- `NO_FAKE_DATA`
- `NO_STAGE037`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE_REVIEW_THIS_RUN`

## 验收证据

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage036_database_quality_constraints.Stage036DatabaseQualityConstraintsPhase3Tests -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage036_phase3_quality_constraint_scenarios -q`
- `python3 -B KM_IDSystem/scripts/check_database_quality_constraints.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## 回滚

Revert `STAGE036_PHASE3_SCENARIO_VALIDATION.md`、checker 的 Phase 3 scenario
report、Stage036/Stage005 tests、Stage005 validator、batch lock、roadmap/event、
必要兼容测试和 owner render 变更。不得执行 migration down，也不得触碰
`/Users/linzezhang/Downloads/IDS_MetaData`、`00_ORIGINAL_RAW_DATA`、source/runtime
database、PostgreSQL data directory、rows、dumps、backups、reports、outputs、
manifest、evidence ledger、audit log、app entries、GitHub state、STAGE-037 或
Phase 4 artifacts。
