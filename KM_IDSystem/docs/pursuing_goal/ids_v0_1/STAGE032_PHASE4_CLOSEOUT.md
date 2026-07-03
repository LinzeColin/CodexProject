# IDS v0.1 STAGE-032 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE032-P4`
- Acceptance ID: `ACC-STAGE-032`
- Stage: `STAGE-032 · 数据库连接与连接池基线`
- Phase: `Phase 4`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE032_PHASE4_CLOSEOUT_NO_BATCH_UPLOAD_NO_STAGE_REVIEW_THIS_RUN_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes the local database connection and connection-pool baseline
evidence using tracked contracts only. The delivered helper is:

`KM_IDSystem/scripts/check_database_connection_pool.py build_stage032_delivery_report`

It returns an in-memory
`ids.stage032.database_connection_pool.phase4.v1` object with:

- schema_diff
- migration_output
- recovery_test_log
- known_limits
- destructive_migration_confirmation
- rollback_steps
- backup_restore_steps
- chinese_owner_feedback

The helper does not choose an output path, does not persist JSON, does not
connect PostgreSQL, and does not create runtime connection pools, DSNs,
credential-bearing configs, database rows, reports, screenshots, PDFs,
evidence ledgers, audit logs, indexes, manifests, documents, chunks, jobs,
import rows, parser output, production data artifacts, or local service state.

## schema_diff

Mode: `static_connection_pool_contract_diff_not_executed`.

The schema diff is a tracked-contract summary, not a live database diff. It
compares the STAGE-032 Phase 2/3 tracked connection-pool index and scenario
validation against the Phase 4 closeout contract:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json`
- `KM_IDSystem/scripts/check_database_connection_pool.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE3_SCENARIO_VALIDATION.md`

Connection profiles closed by the contract:

- `backend_connection_profile`
- `worker_connection_profile`
- `report_task_connection_profile`
- `retrieval_task_connection_profile`

Key guardrails closed by the contract:

- credential guard
- pool-size guard
- timeout guard
- transaction guard
- retry/backoff guard
- healthcheck guard
- storage boundary guard
- raw metadata boundary guard
- real data only guard

Raw payload columns added: none. Credential fields added: none.

No live schema diff was executed. 不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## migration_output

Mode: `static_connection_pool_migration_output_not_executed`.

The migration output is the static validator output from tracked connection
pool, scenario, and migration-safety dependency contracts:

- Migration dependency ref: `../schema_migration_safety/stage031_migration_safety_index.json`
- Expected static result: all Phase 2 profiles, guardrails, and runtime policy
  checks are true, and all Phase 3 scenario statuses are `PASS`.
- Live output ref: `NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION`.

This is intentionally not a PostgreSQL transcript. 本轮不连接 PostgreSQL、不创建 database、不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## recovery_test_log

Mode: `static_connection_pool_recovery_log_not_executed`.

Static recovery checks:

1. `safe_healthcheck_only` is true.
2. `healthcheck_writes_database_false` is true.
3. `raw_metadata_boundary_path_only` is true.
4. `transaction_rollback_required` is true.
5. `retry_non_retryable_raw_boundary_violation` is true.
6. `storage_boundary_no_raw_payloads` is true.
7. `backup_restore_steps_defined` is true.
8. `rollback_steps_defined` is true.

Result: static `PASS` from tracked connection-pool index and scenario
validation contracts.

No backup, restore, live rollback, live recovery smoke, or connection-pool
runtime test was executed.

## destructive_migration_confirmation

破坏性迁移 requires explicit human confirmation.

Current contract value:

- `destructive_allowed_by_default=false`
- `current_contract_value=false`
- `manual_confirmation_required_before_change=true`
- destructive migration is blocked by default

Any `DROP`, `ALTER`, data deletion, backfill rewrite, index rebuild, connection
pool upper-bound expansion, raw payload storage change, credential policy
relaxation, or irreversible migration must be handled in a future explicit run
with owner approval, backup evidence, rollback evidence, and a separate stop
gate.

## rollback_steps

数据库回滚 procedure for this Phase 4 run:

1. Stop before live database connection or pool rollout if the static contract
   cannot explain the schema, pool, timeout, transaction, retry, healthcheck,
   storage, raw-boundary, or real-data-only change.
2. Revert the Phase 4 helper, this closeout file, batch lock, roadmap/event
   updates, Stage005 validator/tests, Stage032 focused tests, compatibility
   tests, and rendered owner files only.
3. Do not touch PostgreSQL data directories, DSN/secret stores, runtime
   outputs, app entries, GitHub PR state, or `/Users/linzezhang/Downloads/IDS_MetaData`.
4. Keep `connection_pool_contract_id` stable unless a future authorized stage
   explicitly changes the pool contract.

## backup_restore_steps

备份恢复步骤 for a future authorized migration or pool rollout:

1. Before any future live PostgreSQL migration or pool rollout, create an
   owner-approved logical backup in a separate authorized run.
2. Record backup location, checksum, migration id, dry-run evidence, pool
   contract id, and owner approval in future run evidence.
3. If a future apply fails, run the approved rollback command from the
   migration-safety contract with `ON_ERROR_STOP=1` and single-transaction
   semantics where supported.
4. Restore from the approved backup only in a future authorized restore run,
   then re-run safe healthcheck and keep the raw metadata root path-only.

## known_limits

已知限制:

- PostgreSQL live connection, connection-pool instantiation, migration dry-run, apply, rollback, backup, restore, and schema diff were not executed in this phase.
- This file proves tracked connection-pool contract readiness, not production database readiness.
- No DSN, credential-bearing config, runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs, JSON output files, or service state were generated.
- Raw metadata remains path-only at `/Users/linzezhang/Downloads/IDS_MetaData` and was not inspected.
- STAGE-032 review is blocked until a separate stage review run; BATCH031_040 upload remains blocked until STAGE-031..040 are complete, reviewed, and repaired.

## Batch And Review Boundary

STAGE-032 已完成 Phase 4, but whole-stage review is not performed in this
run.

- Current next gate: `IDS-STAGE032-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- Stage review status: `pending_next_run`
- `NO_BATCH_UPLOAD`
- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_GITHUB_UPLOAD`

This run does not perform whole-stage review, batch review, repair, GitHub
upload, PR creation, PR merge, issue cleanup, or app reinstall. The next run
should review STAGE-032 and fix review findings before entering STAGE-033.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, and fabricated evidence are forbidden.
不得使用虚构 IDS 业务数据.

## chinese_owner_feedback

STAGE-032 已完成 Phase 4：当前交付的是数据库连接与连接池基线的静态工程合同、schema diff 摘要、migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、数据库回滚步骤、备份恢复步骤和中文反馈。

业务上可以把它理解为：系统已经明确后端、worker、报告任务和检索任务未来如何使用 PostgreSQL 连接策略、连接池上限、超时、事务、重试、healthcheck、存储边界、raw metadata 边界和真实数据护栏。

当前能力仍不是生产 PostgreSQL 连接、迁移或连接池上线授权。真正连接 PostgreSQL、实例化 pool、执行 migration、写 runtime database、读取真实业务语料、写 manifest/database/index/import/report 或进入 GitHub upload，必须等待后续明确 Stage、复审、owner 授权和单独 run gate。
