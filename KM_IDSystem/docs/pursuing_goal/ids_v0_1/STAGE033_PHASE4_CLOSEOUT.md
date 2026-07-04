# IDS v0.1 STAGE-033 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE033-P4`
- Acceptance ID: `ACC-STAGE-033`
- Stage: `STAGE-033 · 数据库体积护栏`
- Phase: `Phase 4`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE033_PHASE4_CLOSEOUT_NO_BATCH_UPLOAD_NO_STAGE_REVIEW_THIS_RUN_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes the local database size-guard evidence using tracked contracts
only. The delivered helper is:

`KM_IDSystem/scripts/check_database_size_guard.py build_stage033_delivery_report`

It returns an in-memory `ids.stage033.database_size_guard.phase4.v1` object
with:

- schema_diff
- migration_output
- recovery_test_log
- known_limits
- destructive_migration_confirmation
- rollback_steps
- backup_restore_steps
- chinese_owner_feedback

The helper does not choose an output path, does not persist JSON, does not
connect PostgreSQL, and does not create runtime database rows, reports,
screenshots, PDFs, evidence ledgers, audit logs, indexes, manifests,
documents, chunks, jobs, parser output, PostgreSQL statistics, cleanup output,
production data artifacts, local service state, DSNs, credential-bearing
configs, or app entries.

## schema_diff

Mode: `static_database_size_guard_contract_diff_not_executed`.

The schema diff is a tracked-contract summary, not a live PostgreSQL diff. It
compares the STAGE-033 Phase 2/3 tracked database-size guard index and scenario
validation against the Phase 4 closeout contract:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json`
- `KM_IDSystem/scripts/check_database_size_guard.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE3_SCENARIO_VALIDATION.md`

Size-guard areas closed by the contract:

- PostgreSQL storage scope guard
- raw content block guard
- OCR full-text block guard
- large-file block guard
- derived-artifact limit guard
- database-size budget guard
- table-size guard
- index-bloat guard
- row-payload guard
- retention-cleanup guard
- connection-pool budget guard
- quality constraint guard
- rollback verification guard
- raw metadata boundary guard
- real data only guard

Raw payload columns added: none. Large-file columns added: none. Credential
fields added: none.

No live schema diff was executed. 不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## migration_output

Mode: `static_database_size_guard_migration_output_not_executed`.

The migration output is the static validator output from tracked database-size
guard, scenario, connection-pool, and migration-safety dependency contracts:

- Migration dependency ref: `../schema_migration_safety/stage031_migration_safety_index.json`
- Connection-pool dependency ref: `../database_connection_pool/stage032_connection_pool_index.json`
- Expected static result: all Phase 2 guardrail/runtime policy checks are
  true, and all Phase 3 scenario statuses are `PASS`.
- Live output ref: `NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION`.

This is intentionally not a PostgreSQL transcript. 本轮不连接 PostgreSQL、不创建 database、不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## recovery_test_log

Mode: `static_database_size_guard_recovery_log_not_executed`.

Static recovery checks:

1. `raw_metadata_boundary_path_only` is true.
2. `runtime_size_query_blocked` is true.
3. `cleanup_default_mode_dry_run_only` is true.
4. `auto_delete_blocked` is true.
5. `rollback_verification_required` is true.
6. `backup_restore_steps_defined` is true.
7. `post_cleanup_verification_required` is true.
8. `no_raw_or_ocr_payloads_in_postgres` is true.

Result: static `PASS` from tracked database-size guard index and scenario
validation contracts.

No backup, restore, live rollback, live recovery smoke, size query, VACUUM,
reindex, cleanup, retention deletion, or database-size runtime test was
executed. 不运行 size query、VACUUM、reindex、cleanup 或 retention deletion.

## destructive_migration_confirmation

破坏性迁移 requires explicit human confirmation.

Current contract value:

- `destructive_allowed_by_default=false`
- `current_contract_value=false`
- `manual_confirmation_required_before_change=true`
- destructive migration is blocked by default

Any `DROP`, `ALTER`, data deletion, backfill rewrite, table/index rebuild,
retention deletion, automatic cleanup, VACUUM/reindex, raw payload storage,
OCR full-text storage, large-file storage, size-threshold relaxation, or
irreversible migration must be handled in a future explicit run with owner
approval, backup evidence, rollback evidence, and a separate stop gate.

## rollback_steps

数据库回滚 procedure for this Phase 4 run:

1. Stop before any live PostgreSQL connection, migration, size query, cleanup,
   VACUUM, reindex, backup, restore, or schema diff if the static contract
   cannot explain the storage scope, table/index/payload limits, cleanup gate,
   raw-boundary, real-data-only policy, or rollback verification.
2. Revert the Phase 4 helper, this closeout file, batch lock, roadmap/event
   updates, Stage005 validator/tests, Stage033 focused tests, compatibility
   tests, and rendered owner files only.
3. Do not touch PostgreSQL data directories, DSN/secret stores, runtime
   outputs, app entries, GitHub PR state, or `/Users/linzezhang/Downloads/IDS_MetaData`.
4. Keep `database_size_guard_contract_id` stable unless a future authorized
   stage explicitly changes the database size-guard contract.

## backup_restore_steps

备份恢复步骤 for a future authorized migration, size-policy rollout, or cleanup:

1. Before any future live PostgreSQL migration, size-policy rollout, cleanup,
   VACUUM, reindex, retention deletion, or raw-payload storage change, create
   an owner-approved logical backup in a separate authorized run.
2. Record backup location, checksum, migration id, dry-run evidence,
   `database_size_guard_contract_id`, and owner approval in future run
   evidence.
3. If a future apply or cleanup fails, stop writes immediately and run the
   approved rollback command from the migration-safety contract with
   `ON_ERROR_STOP=1` and single-transaction semantics where supported.
4. Restore from the approved backup only in a future authorized restore run,
   then re-run safe healthcheck, size-budget verification, and raw metadata
   path-only checks.

## known_limits

已知限制:

- PostgreSQL live connection, migration dry-run, apply, rollback, backup,
  restore, schema diff, size queries, VACUUM, reindex, cleanup, retention
  deletion, and recovery smoke were not executed in this phase.
- This file proves tracked database-size guard contract readiness, not
  production database readiness or measured runtime database size.
- No DSN, credential-bearing config, runtime database rows, document/chunk/job
  rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs,
  JSON output files, size statistics, cleanup outputs, or service state were
  generated.
- Raw metadata remains path-only at `/Users/linzezhang/Downloads/IDS_MetaData`
  and was not inspected.
- STAGE-033 review is blocked until a separate stage review run; BATCH031_040
  upload remains blocked until STAGE-031..040 are complete, reviewed, and
  repaired.

## Batch And Review Boundary

STAGE-033 已完成 Phase 4, but whole-stage review is not performed in this run.

- Current next gate: `IDS-STAGE033-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- Stage review status: `pending_next_run`
- `NO_BATCH_UPLOAD`
- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_GITHUB_UPLOAD`

This run does not perform whole-stage review, batch review, repair, GitHub
upload, PR creation, PR merge, issue cleanup, app reinstall, or STAGE-034
entry. The next run should review STAGE-033 and fix review findings before
entering STAGE-034.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, or commit any content from that root. 中文边界原文：不得读取、列出、
hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

完整停止语句：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, and fabricated evidence are forbidden.
不得使用虚构 IDS 业务数据.

## chinese_owner_feedback

STAGE-033 已完成 Phase 4：当前交付的是数据库体积护栏的静态工程合同、schema diff
摘要、migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、数据库回滚步骤、备份恢复步骤和中文反馈。

业务上可以把它理解为：系统已经明确 PostgreSQL 未来只能保存控制面 metadata、状态 refs、audit/evidence refs、migration/job state 和有界 hot-index metadata；raw 文件、OCR 全文、大文件、无限制派生产物、report binary、vector payload、虚构业务数据和伪造证据默认不得进入 PostgreSQL。

当前能力仍不是生产 PostgreSQL 连接、迁移、体积统计或清理授权。真正连接 PostgreSQL、执行 migration、写 runtime database、读取真实业务语料、运行 size query/VACUUM/reindex/cleanup、写 manifest/database/index/import/report 或进入 GitHub upload，必须等待后续明确 Stage、复审、owner 授权和单独 run gate。
