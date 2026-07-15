# IDS v0.1 STAGE-031 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE031-P4`
- Acceptance ID: `ACC-STAGE-031`
- Stage: `STAGE-031 · Schema 迁移安全`
- Phase: `Phase 4`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE031_PHASE4_CLOSEOUT_NO_BATCH_UPLOAD_NO_STAGE_REVIEW_THIS_RUN`

## Delivery Evidence

Phase 4 closes the local schema migration safety evidence using tracked
contracts only. The delivered helper is:

`KM_IDSystem/scripts/check_schema_migration_safety.py build_stage031_delivery_report`

It returns an in-memory
`ids.stage031.schema_migration_safety.phase4.v1` object with:

- schema diff
- migration 输出
- 恢复测试日志
- 已知限制
- 破坏性迁移人工确认
- 数据库回滚
- 备份恢复步骤
- 中文 owner feedback

The helper does not choose an output path, does not persist JSON, does not
connect PostgreSQL, and does not create runtime database rows, reports,
screenshots, PDFs, evidence ledgers, audit logs, indexes, manifests, documents,
chunks, jobs, import rows, parser output, production data artifacts, or local
service state.

## Schema Diff

Mode: `static_schema_migration_safety_diff_not_executed`.

The schema diff is a tracked-contract summary, not a live database diff. It
compares the STAGE-030 tracked PostgreSQL control-plane schema contract against
the STAGE-031 safety closeout contract:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json`

Safety gates added by the contract:

- `dry_run_guard`
- `backup_checkpoint_guard`
- `validation_guard`
- `rollback_guard`
- `recovery_smoke_guard`
- `audit_guard`
- `owner_stop_gate`

Key guard constraints:

- `chk_payload_size_bytes`
- `chk_connection_pool_size`
- `chk_no_raw_content_stored`
- `chk_fact_level`
- `chk_index_state`

Raw payload columns added: none.

No live schema diff was executed. 不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## Migration Output

Mode: `static_migration_safety_output_not_executed`.

The migration output is the static validator output from tracked safety,
SQL, and schema-index contracts:

- `dry_run_command_ref`: `psql --set ON_ERROR_STOP=1 --single-transaction --file 001_control_plane_schema.sql --dry-run-equivalent-in-future-run`
- `rollback_command_ref`: `psql --set ON_ERROR_STOP=1 --single-transaction --file 001_control_plane_schema.sql --section migrate:down`
- Expected static result: all Phase 2 safety gates and guardrails are true and
  all Phase 3 scenario statuses are `PASS`.
- Live output ref: `NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION`.

This is intentionally not a PostgreSQL transcript. 本轮不连接 PostgreSQL、不创建 database、不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## Recovery Test Log

Mode: `static_recovery_log_not_executed`.

Static recovery checks:

1. `dry_run_guard` is present.
2. `backup_checkpoint_guard` is present.
3. `rollback_guard` is present.
4. `recovery_smoke_guard` is present.
5. `recovery_checkpoint_ref` exists in `ids_schema_migrations`.
6. `rollback_sql_ref` exists in `ids_schema_migrations`.
7. `ON_ERROR_STOP=1` is required by migration refs.
8. `--single-transaction` is required by migration refs.

Result: static `PASS` from tracked safety index, SQL, and schema index
contracts.

No backup, restore, live rollback, or live recovery smoke was executed.

## Destructive Migration Confirmation

破坏性迁移 requires explicit human confirmation.

Current contract value:

- `destructive_auto_approval_allowed=false`
- destructive migration is blocked by default
- manual confirmation is required before any future destructive schema migration

Any `DROP`, `ALTER`, data deletion, backfill rewrite, index rebuild, or
irreversible migration must be handled in a future explicit run with owner
approval, backup evidence, rollback evidence, and a separate stop gate.

## Rollback And Backup Recovery Steps

备份恢复步骤 and 数据库回滚 procedure for a future authorized migration run:

1. Stop before live migration if schema diff cannot be explained from tracked
   SQL/index/safety contracts.
2. Create a PostgreSQL logical backup in a future authorized run before apply.
3. Record backup location, checksum, migration id, dry-run evidence, and owner
   approval in future run evidence.
4. Run `rollback_command_ref` with `ON_ERROR_STOP=1` and `--single-transaction`
   if apply fails.
5. Restore from the approved backup only in a future authorized restore run.
6. Re-run recovery smoke checks and keep the raw metadata root path-only after
   rollback.

Rollback for this Phase 4 run is simpler: revert the helper additions, this
closeout file, batch lock changes, roadmap/event updates, Stage005
validator/test updates, Stage031 focused test updates, and rendered owner
files. Do not touch PostgreSQL data directories, runtime data, reports,
outputs, manifests, evidence ledgers, audit logs, indexes, app entries, GitHub
state, or `/Users/linzezhang/Downloads/IDS_MetaData`.

## Known Limits

已知限制:

- PostgreSQL live connection, dry-run, apply, rollback, backup, restore, and schema diff were not executed in this phase.
- This file proves tracked schema migration safety contract readiness, not production database readiness.
- No runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, manifests, ledgers, audit logs, or JSON output files were generated.
- Raw metadata remains path-only at `/Users/linzezhang/Downloads/IDS_MetaData` and was not inspected.
- STAGE-031 review is blocked until a separate stage review run; BATCH031_040 upload remains blocked until STAGE-031..040 are complete, reviewed, and repaired.

## Batch And Review Boundary

STAGE-031 已完成 Phase 4, but whole-stage review is not performed in this
run.

- Current next gate: `IDS-STAGE031-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- Stage review status: `pending_next_run`
- `NO_BATCH_UPLOAD`
- `NO_STAGE_REVIEW_THIS_RUN`

This run does not perform whole-stage review, batch review, repair, GitHub
upload, PR creation, PR merge, issue cleanup, or app reinstall. The next run
should review STAGE-031 and fix review findings before entering STAGE-032.

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

## Chinese Owner Feedback

STAGE-031 已完成 Phase 4：当前交付的是 schema migration safety 的静态工程合同、schema diff 摘要、migration 输出说明、恢复测试日志、回滚/备份恢复步骤、破坏性迁移人工确认和中文反馈。

业务上可以把它理解为：系统已经明确“所有 schema migration 必须先有 dry-run、备份、校验、回滚和恢复证据”，并且记录了未来 migration 需要如何解释差异、如何阻断破坏性变更、如何回滚和如何恢复。

当前能力仍不是生产数据库迁移授权。真正连接 PostgreSQL、执行 migration、写 runtime database、读取真实业务语料、写 manifest/database/index/import/report 或进入 GitHub upload，必须等待后续明确 Stage、复审、owner 授权和单独 run gate。
