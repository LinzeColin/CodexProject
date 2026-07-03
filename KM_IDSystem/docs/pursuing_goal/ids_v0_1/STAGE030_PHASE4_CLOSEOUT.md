# IDS v0.1 STAGE-030 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE030-P4`
- Acceptance ID: `ACC-STAGE-030`
- Stage: `STAGE-030 · PostgreSQL 控制面启动`
- Phase: `Phase 4`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE030_PHASE4_CLOSEOUT_NO_BATCH_UPLOAD_NO_STAGE_REVIEW_THIS_RUN`

## Delivery Evidence

Phase 4 closes the local PostgreSQL control-plane delivery evidence using
tracked contracts only. The delivered helper is:

`KM_IDSystem/scripts/check_postgresql_control_plane.py build_stage030_delivery_report`

It returns an in-memory
`ids.stage030.postgresql_control_plane.phase4.v1` object with:

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

Mode: `static_contract_diff_not_executed`.

The schema diff is a tracked-contract summary, not a live database diff. It
compares the pre-STAGE-030 state of no tracked PostgreSQL control-plane schema
against the tracked target contract:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json`

Tables added by the contract:

- `ids_metadata_sources`
- `ids_jobs`
- `ids_documents`
- `ids_chunks`
- `ids_evidence_records`
- `ids_audit_events`
- `ids_index_versions`
- `ids_schema_migrations`

Key guard constraints:

- `chk_payload_size_bytes`
- `chk_connection_pool_size`
- `chk_no_raw_content_stored`
- `chk_fact_level`
- `chk_index_state`

Raw payload columns added: none.

No live schema diff was executed. 不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## Migration Output

Mode: `static_contract_output_not_executed`.

The migration output is the static validator output from tracked SQL/index
contracts:

- `dry_run_command_ref`: `psql --set ON_ERROR_STOP=1 --single-transaction --file 001_control_plane_schema.sql --dry-run-equivalent-in-future-run`
- `rollback_command_ref`: `psql --set ON_ERROR_STOP=1 --single-transaction --file 001_control_plane_schema.sql --section migrate:down`
- Expected static result: all Phase 2 migration guards are true and all Phase 3 scenario statuses are `PASS`.
- Live output ref: `NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION`.

This is intentionally not a PostgreSQL transcript. 本轮不连接 PostgreSQL、不创建 database、不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## Recovery Test Log

Mode: `static_recovery_log_not_executed`.

Static recovery checks:

1. `recovery_checkpoint_ref` exists in `ids_schema_migrations`.
2. `rollback_sql_ref` exists in `ids_schema_migrations`.
3. `DROP TABLE IF EXISTS ids_schema_migrations` exists in `migrate:down`.
4. `ON_ERROR_STOP=1` is required by migration refs.
5. `--single-transaction` is required by migration refs.

Result: static `PASS` from tracked SQL/index contracts.

No backup, restore, live rollback, or live recovery smoke was executed.

## Destructive Migration Confirmation

破坏性迁移 requires explicit human confirmation.

Current contract value:

- `destructive_allowed=false`
- destructive migration is blocked by default
- manual confirmation is required before any future destructive change

Any `DROP`, `ALTER`, data deletion, backfill rewrite, index rebuild, or
irreversible migration must be handled in a future explicit run with owner
approval, backup evidence, rollback evidence, and a separate stop gate.

## Rollback And Backup Recovery Steps

备份恢复步骤 and 数据库回滚 procedure for a future authorized migration run:

1. Stop before live migration if schema diff cannot be explained from tracked SQL/index contracts.
2. Create a PostgreSQL logical backup in a future authorized run before apply.
3. Record backup location, checksum, migration id, and owner approval in future run evidence.
4. Run `rollback_command_ref` with `ON_ERROR_STOP=1` and `--single-transaction` if apply fails.
5. Restore from the approved backup only in a future authorized restore run.
6. Re-run recovery smoke checks and keep the raw metadata root path-only after rollback.

Rollback for this Phase 4 run is simpler: revert the helper additions, this
closeout file, batch lock changes, roadmap/event updates, Stage005
validator/test updates, compatibility test updates, and rendered owner files.
Do not touch PostgreSQL data directories, runtime data, reports, outputs,
manifests, evidence ledgers, audit logs, indexes, app entries, GitHub state, or
`/Users/linzezhang/Downloads/IDS_MetaData`.

## Known Limits

已知限制:

- PostgreSQL live connection, dry-run, apply, rollback, backup, restore, and schema diff were not executed in this phase.
- This file proves tracked contract readiness, not production database readiness.
- No runtime database rows, document/chunk/job rows, indexes, reports, screenshots, PDFs, or JSON output files were generated.
- Raw metadata remains path-only at `/Users/linzezhang/Downloads/IDS_MetaData` and was not inspected.
- Batch upload is blocked until the STAGE-021..030 batch review gate and repair gate pass.

## Batch And Review Boundary

STAGE-030 已完成 Phase 4, but the ten-stage batch is not uploaded.

- Current next gate: `IDS-V0_1-BATCH-021-030-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- Stage review status: `pending_next_run`
- `NO_BATCH_UPLOAD`
- `NO_STAGE_REVIEW_THIS_RUN`

This run does not perform whole-stage review, batch review, repair, GitHub
upload, PR creation, PR merge, issue cleanup, or app reinstall. The next run
should review `STAGE-021..STAGE-030` and fix review findings before a separate
upload gate is allowed.

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

STAGE-030 已完成 Phase 4：当前交付的是 PostgreSQL 控制面 schema/migration 的静态工程合同、回滚和备份恢复说明，以及中文 owner 反馈。

业务上可以把它理解为：系统已经明确“PostgreSQL 只存控制面、状态和热索引，不存原始大文件”，并且记录了未来 migration 需要如何 dry-run、如何阻断破坏性变更、如何回滚和如何恢复。

当前能力仍不是生产数据库迁移授权。真正连接 PostgreSQL、执行 migration、写 runtime database、读取真实业务语料、写 manifest/database/index/import/report 或进入 GitHub upload，必须等待后续明确 Stage、批次复审、owner 授权和单独 run gate。
