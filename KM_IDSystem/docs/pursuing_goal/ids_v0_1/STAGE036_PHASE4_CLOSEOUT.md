# IDS v0.1 STAGE-036 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE036-P4`
- Acceptance ID: `ACC-STAGE-036`
- Stage: `STAGE-036 · 数据库质量约束`
- Phase: `Phase 4 · 数据库质量约束交付证据、回滚与中文反馈`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE036_PHASE4_CLOSEOUT_NO_STAGE_REVIEW_THIS_RUN_NO_BATCH_UPLOAD_NO_GITHUB_UPLOAD`

## P0 Binding

- Source archive: `IDS_Taskpack_v0_1_only_中文修订版.zip`
- Source member: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md`
- Source SHA-256: `13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b`
- P0 Phase 4 requires schema diff, migration output, recovery test log,
  known limits, destructive-migration confirmation, database rollback steps,
  backup/restore steps, and Chinese owner feedback.

## Delivery Evidence

Phase 4 closes local delivery evidence through tracked engineering contracts
only. The machine helper is:

`KM_IDSystem/scripts/check_database_quality_constraints.py build_stage036_delivery_report`

It returns an in-memory
`ids.stage036.database_quality_constraints.phase4.v1` report backed by the
tracked machine contract
`ids.stage036.database_quality_constraints.delivery_contract.v1`.

The helper loads one index, migration, and baseline snapshot, reuses those
snapshots for Phase 2, Phase 3, and Phase 4, and prints JSON to stdout. It does
not choose an output path, connect PostgreSQL, query rows, execute SQL, write a
database, or create a runtime log. Any invalid delivery field, runtime-policy
change, or SQL guard drift produces `delivery_contract_valid=false`,
`result=FAIL_CLOSED`, and
`execution_state=BLOCKED_INVALID_QUALITY_CONSTRAINT_CONTRACT`.

## schema_diff

Mode: `static_tracked_schema_diff_not_executed`.

This is a deterministic diff summary between the tracked STAGE-030 control
plane baseline and the tracked STAGE-036 `002` migration contract. The machine
report exposes the real SHA-256 values of both tracked snapshots and identifies:

- one added table contract: `ids_state_value_registry`
- nine candidate quality constraints
- three existing foreign keys preserved from STAGE-030
- the exact candidate ids and tracked source references

Current result:

- `live_schema_diff_result=NOT_EXECUTED`
- PostgreSQL schema inspected: `false`
- PostgreSQL schema changed: `false`
- Live output reference:
  `NOT_AVAILABLE_BY_POLICY_NO_POSTGRESQL_CONNECTION`

This evidence proves the tracked schema contract is internally consistent. It
does not prove compatibility with live rows or an installed database schema.

## migration_output

Mode: `static_tracked_migration_output_not_executed`.

The report binds the tracked migration id
`ids_stage036_002_database_quality_constraints`, its real tracked SHA-256,
ordered `migrate:up` / `migrate:down` sections, exact candidate guards,
rollback coverage, and the STAGE-031 safety requirements.

- `live_migration_result=NOT_EXECUTED`
- `live_constraint_validation_result=NOT_EXECUTED`
- `destructive_migration_allowed=false`
- Live output reference: `NOT_AVAILABLE_BY_POLICY_NO_MIGRATION_EXECUTION`

No `psql`, dry-run, apply, `VALIDATE CONSTRAINT`, rollback, backup, restore,
recovery smoke, transaction, row-count, duplicate-count, cleanup, or state
registry write command was run. No fabricated command transcript is presented
as migration output.

## recovery_test_log

Mode: `static_quality_constraint_recovery_log_expected_block`.

The in-memory log includes all fourteen Phase 3 scenario results and the Phase
4 delivery checks. The recovery scenario must preserve the missing-authorized-
profile stop state.

- `result=PASS_WITH_EXPECTED_BLOCK`
- `live_recovery_smoke_result=NOT_EXECUTED`
- `execution_ready=false`
- `execution_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE`
- `live_execution_performed=false`

`PASS_WITH_EXPECTED_BLOCK` means the checker proved that an incomplete or
tampered contract remains blocked. It does not mean migration, rollback,
restore, recovery smoke, healthcheck, or production readiness succeeded.

## destructive_migration_confirmation

任何破坏性 migration 必须单独人工确认。

Current contract:

- `required=true`
- `destructive_allowed_by_default=false`
- `current_migration_destructive=false`
- `authorized_this_run=false`
- `manual_owner_confirmation_required=true`

Any future destructive `DROP`, `TRUNCATE`, `DELETE`, source overwrite,
irreversible schema change, nonempty registry cleanup, or target cleanup needs
a separate run with owner approval, bounded real-data identity, verified backup
checkpoint, dry-run impact evidence, rollback evidence, and an explicit stop
gate. This Phase 4 run authorizes none of those actions.

## rollback_steps

数据库回滚步骤:

1. If any schema diff, migration, scenario, or delivery check fails, keep the
   system blocked and stop every database action.
2. Before any future authorized apply, create and verify a recoverable backup
   checkpoint. Missing checkpoint evidence is a hard stop.
3. If a separately authorized apply must be rolled back, execute only the
   tracked `002` migration `migrate:down` section with `ON_ERROR_STOP` and one
   transaction. This run does not execute it.
4. Preserve the source database. Rollback and restore may target only the
   separately approved target and must not overwrite, delete, migrate, or
   restore into the source.
5. If `ids_state_value_registry` is nonempty, automatic rollback must fail
   closed. Any value cleanup requires a later owner decision; automatic DROP
   is forbidden.
6. Failed-target or derived-artifact cleanup requires a separate owner cleanup
   gate. Phase 4 performs no cleanup.
7. To revert this run itself, revert only the P4 checker/index/doc/tests,
   governance updates, compatibility assertions, and rendered owner files.

## backup_restore_steps

未来单独授权 run 的备份恢复步骤:

1. Obtain an owner-authorized real control-plane data profile reference,
   bounded scope, source identity, schema version, and approval reference.
2. Provide credentials only through managed secret references. Do not expose
   plaintext credentials in Git, commands, reports, or audit bodies.
3. Create an isolated, identifiable backup checkpoint and verify that it can be
   used for recovery. Record only sanitized evidence references in Git.
4. Prepare an approved isolated non-production target and verify PostgreSQL
   version, schema head, storage budget, connection-pool budget, and source
   non-interference before dry-run.
5. Run the tracked migration dry-run against that isolated target. Stop on any
   unexpected schema, size, transaction, constraint, or source result.
6. Apply and validate the nine candidate constraints only when the owner-
   authorized real profile proves zero bounded violations for each candidate.
7. After apply, verify schema, migration ledger, constraints, indexes, bounded
   real counts, health/readiness, no-raw-payload rules, and recovery smoke.
8. On failure, stop writes, quarantine the target, and restore the approved
   checkpoint. Never overwrite the source database.

## known_limits

已知限制:

- No owner-authorized real data profile was available, so real duplicates,
  nulls, foreign-key violations, state values, and consistency violations were
  not measured.
- PostgreSQL connection, live schema diff, migration dry-run/apply/rollback,
  constraint validation, backup, restore, recovery smoke, healthcheck, and row
  checks were not executed.
- Static `PASS_WITH_EXPECTED_BLOCK` is not evidence that live data is clean,
  constraints are installed, or the database is production-ready.
- No database, DSN, credential config, profile, migration output file,
  recovery log file, report, or runtime output was created.
- The raw metadata root remains path-only and no content was accessed.
- `ids_state_value_registry` remains empty; STAGE-037 still owns state values
  and transitions.
- STAGE-036 whole-stage review remains pending. BATCH031_040 upload and app
  reinstall remain blocked.

## Stage And Batch Boundary

STAGE-036 has completed Phase 1 through Phase 4 locally. Whole-stage review is
a separate next run.

- `stage_review_status=pending_next_run`
- Current next gate: `IDS-STAGE036-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_BATCH_REVIEW`
- `NO_BATCH_UPLOAD`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE037`

This run does not perform whole-stage review, review remediation, STAGE-037,
batch review, upload gate, GitHub push/PR/merge, issue mutation, or app
reinstall.

## Raw Data Boundary

The local real IDS metadata database root is recorded as a path only:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, restore, or commit any content from that root. This Phase 4 run does
none of those actions.

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real owner-approved data.
不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据。

No fake row, fake profile, synthetic business record, placeholder corpus,
fixture database, or fabricated migration/recovery transcript was created or
used.

## chinese_owner_feedback

STAGE-036 Phase 4 已形成数据库质量约束的静态交付证据，包括 tracked schema
diff 摘要、migration 输出说明、expected-block recovery log、已知限制、破坏性
migration 人工确认、数据库回滚步骤、备份恢复步骤和中文反馈。

本轮未执行真实 migration、constraint validation、rollback、backup、restore 或
recovery smoke。当前没有 owner 授权真实数据 profile，因此所有 live 操作继续处于
`BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_DATA_PROFILE`；
`PASS_WITH_EXPECTED_BLOCK` 只证明系统正确拒绝了未授权或不完整执行条件。

下一步只能进入独立的 STAGE-036 review。该复审必须检查 Phase 1-4 证据并修复
发现的问题；本轮不上传 GitHub、不重装 app、不进入 STAGE-037，也不访问
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。
