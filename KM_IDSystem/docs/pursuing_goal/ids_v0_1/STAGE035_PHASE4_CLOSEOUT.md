# IDS v0.1 STAGE-035 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE035-P4`
- Acceptance ID: `ACC-STAGE-035`
- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Phase: `Phase 4 · 数据库恢复冒烟测试交付证据、回滚与中文反馈`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE035_PHASE4_CLOSEOUT_NO_STAGE_REVIEW_THIS_RUN_NO_BATCH_UPLOAD_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes the local STAGE-035 delivery evidence with tracked contracts
only. The delivered helper is:

`KM_IDSystem/scripts/check_database_recovery_smoke.py build_stage035_delivery_report`

It returns an in-memory `ids.stage035.database_recovery_smoke.phase4.v1`
object containing:

- `delivery_contract_valid` and dynamic `delivery_check_results`
- `schema_diff`
- `migration_output`
- `recovery_test_log`
- `known_limits`
- `destructive_migration_confirmation`
- `rollback_steps`
- `backup_restore_steps`
- `chinese_owner_feedback`

The helper reads only tracked STAGE-030..035 engineering contracts and emits
JSON to stdout through the existing checker. It does not choose or create an
output path, connect to PostgreSQL, read a metadata dump, execute migration or
restore commands, or create runtime data. A tampered in-memory restore policy
causes `delivery_contract_valid=false`, `result=FAIL_CLOSED`, and
`execution_state=BLOCKED_INVALID_RECOVERY_CONTRACT`.

## schema_diff

Mode: `static_recovery_contract_diff_not_executed`.

This is a static contract diff between the Phase 2 preflight contract, the
eleven Phase 3 scenario results, and the Phase 4 closeout fields. It records
the required bounded control-plane tables, recovery contract identity,
destructive migration gate, rollback steps, and backup/restore steps.

- `live_schema_diff_result=NOT_EXECUTED`
- New live schema file created: `false`
- New live migration file created: `false`
- Live output reference: `NOT_AVAILABLE_BY_POLICY_NO_POSTGRESQL_CONNECTION`

No PostgreSQL schema was inspected or changed. This result does not prove
schema compatibility with a real dump.

## migration_output

Mode: `static_recovery_migration_output_not_executed`.

The output records only the tracked STAGE-030 control-plane migration identity
and the STAGE-031 safety requirements: dry-run first, approved backup
checkpoint, rollback evidence, and destructive actions blocked by default.

- `live_migration_result=NOT_EXECUTED`
- Live output reference: `NOT_AVAILABLE_BY_POLICY_NO_MIGRATION_EXECUTION`
- Destructive migration allowed: `false`

No `pg_dump`, `pg_restore`, `psql`, migration dry-run, apply, rollback,
backup, restore, transaction, constraint, index, row-count, healthcheck, or
cleanup command was run.

## recovery_test_log

Mode: `static_recovery_test_log_expected_block`.

The in-memory log checks Phase 2 contract validity, all eleven Phase 3
scenarios, the expected missing-owner-dump stop state, raw-data boundary,
source non-interference, rollback contract, real-data-only policy, and every
no-live-execution guard.

- `live_restore_result=NOT_EXECUTED`
- `live_healthcheck_result=NOT_EXECUTED`
- `result=PASS_WITH_EXPECTED_BLOCK`
- `execution_ready=false`
- `execution_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`
- `live_execution_performed=false`

`PASS_WITH_EXPECTED_BLOCK` means the engineering contract correctly refused
to restore without an owner-authorized real metadata dump. It does not mean a
database was restored, started, queried, or proven production-ready.

## destructive_migration_confirmation

任何破坏性 migration 或 restore 必须单独人工确认。

Current contract:

- `required=true`
- `destructive_allowed_by_default=false`
- `current_contract_value=false`
- `manual_owner_confirmation_required=true`

Any future destructive `DROP`, `ALTER`, truncation, deletion, overwrite,
restore, target cleanup, or irreversible migration requires a separate run,
owner approval, real bounded input identity, backup evidence, dry-run impact
evidence, rollback evidence, and an explicit stop gate.

## rollback_steps

数据库回滚 procedure for this Phase 4 run:

1. If any static contract, scenario, or delivery check fails, keep recovery
   blocked and stop all subsequent database actions.
2. Revert only the Phase 4 checker helper, closeout document, focused tests,
   compatibility assertions, batch lock, roadmap/event updates, Stage005
   validator changes, and rendered owner files.
3. Do not revert, edit, clean, migrate, truncate, delete, overwrite, or inspect
   any source database, runtime database, dump, backup, PostgreSQL data
   directory, restore target, or raw metadata content.
4. Keep any future isolated restore target separate from the source database.
   Source mutation remains prohibited.
5. If a future authorized restore fails, stop writes, quarantine the target,
   preserve sanitized error evidence, and use the separately approved
   STAGE-031 rollback procedure. Target deletion still requires the STAGE-034
   owner stop gate.

## backup_restore_steps

备份恢复步骤 for a future separately authorized run:

1. Obtain an owner-approved real metadata dump identity, bounded scope,
   checksum evidence, approval reference, and source-system version metadata.
2. Create and verify an owner-approved backup checkpoint before any migration
   or restore; record its location outside Git without exposing credentials or
   raw payloads.
3. Verify PostgreSQL tool compatibility, source schema version, migration head,
   isolated non-production target identity, storage budget, and STAGE-032 pool
   budget.
4. Run migration and restore dry-runs only under that future run's explicit
   gate; stop on any unexpected schema, constraint, size, transaction, or
   source-interference result.
5. Execute restore only against the approved isolated target, then verify
   schema, migration ledger, required tables, constraints, indexes, bounded
   real metadata counts, health/readiness, and no-raw-payload rules.
6. On failure, stop writes and restore the approved checkpoint or rebuild the
   isolated target according to the authorized rollback plan. Never overwrite
   the source database.

## known_limits

已知限制:

- No owner-authorized real metadata dump was available to this run, so real
  dump format, checksum, compatibility, row counts, and business values were
  not validated.
- PostgreSQL connection, schema diff, migration dry-run/apply/rollback,
  backup, restore, healthcheck, recovery smoke, transaction, constraint,
  index, and row-count checks were not executed.
- Static `PASS_WITH_EXPECTED_BLOCK` proves safe blocking behavior only. It is
  not live database recovery or production-readiness evidence.
- No database, schema, migration file, DSN, credential config, restore target,
  runtime output, report, manifest, audit log, or recovery-log file was
  created.
- The raw metadata root remains path-only and its contents were not accessed.
- STAGE-035 whole-stage review remains pending. BATCH031_040 upload and app
  reinstall remain blocked.

## Batch And Review Boundary

STAGE-035 has completed Phase 1 through Phase 4 locally. Whole-stage review is
a separate next run.

- `stage_review_status=pending_next_run`
- Current next gate: `IDS-STAGE035-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_BATCH_UPLOAD`
- `NO_GITHUB_UPLOAD`

This run does not perform STAGE-035 review, review remediation, STAGE-036,
batch review, upload gate, GitHub push/PR/merge, issue operations, or app
reinstall.

## Raw Data Boundary

The local real IDS metadata database root is recorded as a path only:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, restore, or commit any content from that root. This Phase 4 run did
none of those actions.

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real owner-approved data.
不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据。

No fake dump, fake row, mock corpus, synthetic business record, fixture
database, or fabricated recovery transcript was created or used.

## chinese_owner_feedback

STAGE-035 Phase 4 已形成数据库恢复冒烟测试的静态交付证据，包括 schema diff
摘要、migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、数据库
回滚步骤、备份恢复步骤和中文反馈。

本阶段未执行真实恢复。当前没有 owner 授权的真实 metadata dump，因此恢复路径
继续处于 `BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP`；静态结果
`PASS_WITH_EXPECTED_BLOCK` 只说明系统正确拒绝了不完整输入，不说明数据库已恢复
或可运行。

下一步只能进入独立的 STAGE-035 whole-stage review。该复审必须检查 Phase 1-4
证据并修复发现的问题；本轮不上传 GitHub、不重装 app、不进入 STAGE-036，也不
访问 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。
