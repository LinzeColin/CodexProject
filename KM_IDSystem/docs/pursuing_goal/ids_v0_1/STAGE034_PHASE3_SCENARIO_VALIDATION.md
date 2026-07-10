# STAGE-034 Phase 3 · 数据保留表专项验证与异常场景

- Stage: `STAGE-034 · 数据保留表`
- Phase: `Phase 3 · 专项验证与异常场景`
- Task ID: `IDS-V0_1-STAGE034-P3`
- Acceptance ID: `ACC-STAGE-034`
- Schema: `ids.stage034.data_retention_table.phase3.v1`
- Checker: `KM_IDSystem/scripts/check_data_retention_table.py#build_stage034_scenario_validation_report`
- Input index: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json`
- Raw metadata root: `/Users/linzezhang/Downloads/IDS_MetaData`

## 目标

本阶段验证 STAGE-034 数据保留表的静态异常场景：migration dry-run 依赖、
重复执行、失败回滚、恢复冒烟、raw payload 阻断、无限制派生产物阻断、
保留对象校验、TTL/owner hold、cleanup dry-run、deletion stop gate、连接池边界、
事务边界和约束错误解释。

所有验证只来自 Git 已追踪的 Phase 1/Phase 2 文档、机器索引和 checker 输出。
本阶段不连接 PostgreSQL。
不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff。
不执行 retention scan、cleanup、deletion、log compaction、cache eviction、old-index rebuild 或 report snapshot pruning。

## 场景矩阵

| Scenario | 验证点 | 当前结论 |
|---|---|---|
| `migration_dry_run` | `schema_change_plan.mode=static_data_retention_table_contract_only`，且 `migration_executed=false`、`connect_to_postgres=false` | PASS |
| `repeat_execution` | checker 只读取 tracked index 并输出 stdout JSON，不写 runtime outputs | PASS |
| `failure_rollback` | `rollback_restore_guard` 要求 rollback/restore/backup 证据，但当前不执行 backup/restore/migration | PASS |
| `recovery_smoke` | `recovery_smoke_executed=false`，恢复冒烟只作为后续 gate 要求 | PASS |
| `raw_payload_block` | PostgreSQL 只存有界 metadata/ref，raw metadata root 仅 path-only | PASS |
| `unbounded_derived_artifact_block` | 不存无限制派生产物，继续服从 STAGE-033 database-size guard | PASS |
| `retention_subject_validation` | 只允许 `temporary_file`、`cache`、`old_index`、`log`、`report_snapshot` | PASS |
| `ttl_owner_hold_policy` | 每类对象必须有 TTL、keep-until、到期原因、warning window 和 owner hold | PASS |
| `cleanup_dry_run` | cleanup 默认只允许 dry-run，当前 `execute_cleanup=false` | PASS |
| `deletion_stop_gate` | 删除、压缩、驱逐、重建、裁剪都必须等待后续 owner stop gate | PASS |
| `connection_pool_boundary` | 不增加 STAGE-032 pool budget，不建立 PostgreSQL 连接 | PASS |
| `transaction_boundary` | 只验证静态事务边界；不打开、不提交、不回滚真实数据库事务 | PASS |
| `constraint_error_explanations` | 每个 guardrail 都有 owner 可解释的失败原因 | PASS |

## 原始数据库边界

`/Users/linzezhang/Downloads/IDS_MetaData` 是真实 IDS metadata database 根路径。
本阶段只把该本机地址作为 `path-only` 边界写入 Git 可追踪证据，供后续 GitHub
main tree 同步；不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
该目录内容，不得把 raw filenames、table rows、schema details、business values
或 derived dump 提交到 GitHub。

所有 IDS runtime corpus、database-backed content、analytics inputs、reports、indexes、
manifests 和 committed examples 必须使用真实用户批准数据。
不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据。

## 约束错误解释

- `retention_subject_class_guard`: 只允许五类保留对象，未知对象和 raw payload subject 必须拒绝。
- `ttl_policy_guard`: 每类保留对象都必须有 TTL、keep-until、到期原因和 warning window。
- `owner_hold_guard`: 人工 hold 或合规 hold 会阻断 cleanup/deletion/compaction/eviction/pruning。
- `cleanup_dry_run_guard`: 清理默认仅 dry-run，当前不执行 cleanup。
- `deletion_stop_gate_guard`: 删除、日志压缩、缓存驱逐、旧索引重建和报告快照裁剪默认禁止。
- `audit_evidence_guard`: 保留状态变化必须引用 event/evidence/fact level/中文 owner reason。
- `rollback_restore_guard`: 未来清理或删除前必须具备 rollback/restore、backup restore plan 和 post-cleanup verification。
- `postgres_storage_scope_guard`: PostgreSQL 只存控制面保留策略 metadata 和 refs，不存 raw payload。
- `database_size_guard_dependency`: STAGE-034 不能覆盖 STAGE-033 数据库体积护栏。
- `connection_pool_budget_guard`: STAGE-034 不增加 STAGE-032 连接池预算。
- `raw_metadata_boundary_guard`: 原始数据库根只记录本机 path，不读取或派生原始内容。
- `real_data_only_guard`: 禁止 fake、placeholder、fabricated IDS 数据或证据。

## No-Go

- `NO_PHASE4`
- `NO_POSTGRES_CONNECTION`
- `NO_LIVE_MIGRATION`
- `NO_RAW_DB_CONTENT`
- `NO_RETENTION_CLEANUP_RUNTIME`
- `NO_DELETION_RUNTIME`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`

## 验收证据

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage034_data_retention_table.Stage034DataRetentionTablePhase3Tests -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage034_phase3_data_retention_table_scenarios -q`
- `python3 -B KM_IDSystem/scripts/check_data_retention_table.py`

## 回滚

Revert `STAGE034_PHASE3_SCENARIO_VALIDATION.md`、`check_data_retention_table.py`
的 Phase 3 scenario report、batch lock、Stage034/Stage005 tests、Stage005 validator、
roadmap/event 更新和必要兼容测试更新即可。回滚不得触碰
`/Users/linzezhang/Downloads/IDS_MetaData`、runtime data、reports、outputs、app entries、
GitHub state、PostgreSQL data directories、retention outputs、cleanup outputs 或 deletion outputs。
