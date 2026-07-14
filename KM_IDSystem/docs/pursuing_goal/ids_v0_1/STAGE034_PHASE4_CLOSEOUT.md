# IDS v0.1 STAGE-034 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE034-P4`
- Acceptance ID: `ACC-STAGE-034`
- Stage: `STAGE-034 · 数据保留表`
- Phase: `Phase 4`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE034_PHASE4_CLOSEOUT_NO_BATCH_UPLOAD_NO_STAGE_REVIEW_THIS_RUN_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes the local data-retention-table evidence using tracked contracts
only. The delivered helper is:

`KM_IDSystem/scripts/check_data_retention_table.py build_stage034_delivery_report`

It returns an in-memory `ids.stage034.data_retention_table.phase4.v1` object
with:

- `schema_diff`
- `migration_output`
- `recovery_test_log`
- `known_limits`
- `destructive_migration_confirmation`
- `rollback_steps`
- `backup_restore_steps`
- `chinese_owner_feedback`
- `contract_valid`

The helper reads only the tracked Stage 034 index and writes JSON to stdout
through the existing checker entry point. It does not choose an output path,
persist JSON, connect PostgreSQL, create runtime rows or jobs, or inspect raw
metadata content.

## schema_diff

Mode: `static_data_retention_table_contract_diff_not_executed`.

This is a tracked-contract summary, not a live PostgreSQL diff. It compares the
Phase 2/3 data-retention index and scenario evidence with this Phase 4 closeout:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json`
- `KM_IDSystem/scripts/check_data_retention_table.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE3_SCENARIO_VALIDATION.md`

The summary covers the five retained subject classes: 临时文件、缓存、旧索引、日志、
报告快照. It also covers TTL/keep-until, owner hold, cleanup dry-run, deletion
stop gate, audit evidence, rollback/restore, PostgreSQL storage scope,
database-size dependency, connection-pool dependency, raw metadata boundary,
and real-data-only policy.

Raw payload columns added: none. Credential fields added: none. No live schema
diff was executed. 不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## migration_output

Mode: `static_data_retention_table_migration_output_not_executed`.

The migration output is the static validator output from tracked data-retention,
scenario, migration-safety, connection-pool, and database-size contracts:

- Migration dependency ref: `../schema_migration_safety/stage031_migration_safety_index.json`
- Future migration identity: `ids_stage034_data_retention_table_static_policy`
- Expected static result: all Phase 2 guardrail/runtime checks are true and all
  Phase 3 scenarios are `PASS`.
- Live output ref: `NOT_AVAILABLE_BY_POLICY_NO_LIVE_POSTGRESQL_CONNECTION`.

This is intentionally not a PostgreSQL transcript. 本轮不连接 PostgreSQL、不创建
database/schema、不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff.

## recovery_test_log

Mode: `static_data_retention_table_recovery_log_not_executed`.

Static recovery checks:

1. `raw_metadata_boundary_path_only` is true.
2. `cleanup_default_mode_dry_run_only` is true.
3. `owner_impact_report_required` is true.
4. `no_delete_proof_required` is true.
5. `destructive_action_blocked_by_default` is true.
6. `owner_stop_gate_required` is true.
7. `rollback_restore_required` is true.
8. `backup_restore_steps_defined` is true.
9. `post_cleanup_verification_required` is true.
10. `no_raw_payloads_in_postgres` is true.

The report includes `recovery_test_log.check_results` for every item above.
Result is `PASS` only when every recovery check is true; otherwise it is
`FAIL`.

No backup, restore, live rollback, recovery smoke, retention scan, cleanup,
deletion, log compaction, cache eviction, old-index rebuild, or report snapshot
pruning was executed. 不执行 retention scan、cleanup、deletion、log compaction、cache eviction、old-index rebuild 或 report snapshot pruning.

## Whole-Stage Review Repair

The STAGE-034 review removed contradictory safety evidence:

- Top-level `does_not_*` values now derive from runtime-policy and guardrail
  checks instead of constants.
- `contract_valid=true` requires every Phase 2 guardrail/runtime check, every
  Phase 3 scenario, and every recovery check to pass.
- An invalid in-memory contract now returns `contract_valid=false`,
  `recovery_test_log.result=FAIL`, and false top-level safety values for the
  affected operations.
- The valid tracked index continues to return `contract_valid=true` and
  `recovery_test_log.result=PASS`.

## destructive_migration_confirmation

破坏性迁移和破坏性 retention action require explicit human confirmation.

Current contract value:

- `destructive_allowed_by_default=false`
- `current_contract_value=false`
- `manual_confirmation_required_before_change=true`
- destructive migration and deletion are blocked by default

Any `DROP`, destructive `ALTER`, data deletion, cleanup, log compaction, cache
eviction, old-index rebuild, report snapshot pruning, raw-payload storage,
retention-policy relaxation, or irreversible migration requires a future
explicit run with owner approval, backup evidence, rollback evidence, dry-run
impact evidence, and a separate stop gate.

## rollback_steps

数据库回滚 procedure for this Phase 4 run:

1. Stop before any live PostgreSQL connection, migration, retention scan,
   cleanup, deletion, compaction, eviction, rebuild, pruning, backup, restore,
   or schema diff if the static contract cannot explain the retention subject,
   TTL/hold policy, dry-run gate, deletion stop gate, raw boundary,
   real-data-only policy, or rollback evidence.
2. Revert the Phase 4 helper, this closeout file, batch lock, roadmap/event
   updates, Stage005 validator/tests, Stage034 focused tests, compatibility
   tests, and rendered owner files only.
3. Do not touch PostgreSQL data directories, DSN/secret stores, runtime
   outputs, app entries, GitHub PR state, or
   `/Users/linzezhang/Downloads/IDS_MetaData`.
4. Keep `data_retention_table_contract_id` stable unless a future authorized
   stage explicitly changes the retention contract.

## backup_restore_steps

备份恢复步骤 for a future authorized migration or retention action:

1. Before any future live migration or cleanup/deletion/compaction/eviction/
   rebuild/pruning action, create an owner-approved logical backup in a
   separate authorized run.
2. Record backup location, checksum, migration id, dry-run impact report,
   `data_retention_table_contract_id`, and owner approval in future evidence.
3. If a future apply or cleanup fails, stop writes immediately and run the
   approved rollback command from the migration-safety contract with
   `ON_ERROR_STOP=1` and single-transaction semantics where supported.
4. Restore only in a future authorized restore run, then re-run healthcheck,
   retention-state verification, no-delete proof, and raw metadata path-only
   checks.

## known_limits

已知限制:

- PostgreSQL connection, migration dry-run/apply/rollback, backup/restore,
  schema diff, retention scan, cleanup, deletion, compaction, eviction,
  rebuild, pruning, and recovery smoke were not executed.
- This file proves tracked data-retention contract readiness. It does not prove
  production database readiness or authorize deletion of retained artifacts.
- No DSN, credential-bearing config, runtime rows, retention jobs, cleanup
  outputs, reports, PDFs, manifests, ledgers, audit logs, JSON output files, or
  service state were generated.
- Raw metadata remains path-only at
  `/Users/linzezhang/Downloads/IDS_MetaData` and was not inspected.
- STAGE-034 review remains a separate next run. BATCH031_040 upload remains
  blocked until STAGE-031..040 are complete, reviewed, and repaired.

## Batch And Review Boundary

STAGE-034 已完成 Phase 4, but whole-stage review is not performed in this run.

- Current next gate: `IDS-STAGE034-REVIEW-GATE`
- Current upload switch: `push_allowed=false`
- Stage review status: `pending_next_run`
- `NO_BATCH_UPLOAD`
- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_GITHUB_UPLOAD`

This run does not perform whole-stage review, batch review, repair, GitHub
upload, PR creation, PR merge, issue cleanup, app reinstall, or STAGE-035
entry. The next run must review STAGE-034 and repair any findings before
entering STAGE-035.

## Raw Data Boundary

The local real IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, or commit any content from that root. 完整停止语句：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real user-approved data.
Fake industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, and fabricated evidence are forbidden.
不得使用虚构 IDS 业务数据.

## chinese_owner_feedback

STAGE-034 已完成 Phase 4：当前交付的是数据保留表的静态工程合同、schema diff
摘要、migration 输出说明、恢复测试日志、已知限制、破坏性迁移人工确认、数据库
回滚步骤、备份恢复步骤和中文反馈。

业务含义是：临时文件、缓存、旧索引、日志和报告快照都必须有明确保留字段、
TTL/keep-until、owner hold、dry-run 影响说明、删除 stop gate、审计证据和恢复路径；
默认不删除、不压缩、不驱逐、不重建、不裁剪，也不把原始数据库内容写进 PostgreSQL。

当前能力仍不是生产 PostgreSQL 连接、迁移或清理授权。真正执行 migration、
retention scan、cleanup/deletion、读取真实业务语料、写 runtime database、上传 GitHub
或重装 app，必须等待后续明确 Stage、复审、owner 授权和单独 run gate。
