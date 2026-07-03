# IDS v0.1 STAGE-031 Phase 3 Scenario Validation

## Scope
- Schema: `ids.stage031.schema_migration_safety.phase3.v1`
- Stage: `STAGE-031 · Schema 迁移安全`
- Task: `IDS-V0_1-STAGE031-P3`
- Acceptance: `ACC-STAGE-031`
- Phase: `Phase 3 · Schema 迁移安全 专项验证与异常场景`
- Recorded at UTC: `2026-07-03T09:04:00Z`

This phase validates schema migration safety scenarios from tracked Git
contracts only. It uses `build_stage031_scenario_validation_report` in
`KM_IDSystem/scripts/check_schema_migration_safety.py`.

It does not connect to PostgreSQL, execute live migration dry-run, apply,
rollback, backup, restore, schema diff, create a database, start services,
install dependencies, inspect raw metadata, or write runtime outputs.

## Scenario Coverage
- `migration_dry_run`: verifies dry-run guard, `ON_ERROR_STOP=1`, and
  `--single-transaction` requirements.
- `repeat_execution`: verifies repeat execution is guarded by
  `CREATE TABLE IF NOT EXISTS` and `ids_schema_migrations`.
- `failure_rollback`: verifies rollback guard and tracked `migrate:down` text.
- `backup_restore_checkpoint`: verifies backup checkpoint and restore refs are
  required before any future apply path.
- `recovery_smoke`: verifies `recovery_checkpoint_ref` and `rollback_sql_ref`
  are present for future recovery smoke.
- `raw_payload_block`: verifies database size and storage quality guardrails
  block raw files, raw database rows, full text, OCR text, vector payloads,
  report binaries, secrets, fake IDS business data, and fabricated evidence.
- `connection_pool_boundary`: verifies pool and timeout limits are
  machine-readable and owner-explainable.
- `transaction_boundary`: verifies fail-fast, single-transaction, and destructive
  owner stop-gate requirements.
- `constraint_error_explanations`: verifies constraint errors are explainable
  for payload size, connection pool, raw content, fact level, and index state.

## Acceptance Mapping
- migration dry-run: static contract requires dry-run evidence before any apply
  path.
- 重复执行: tracked schema uses idempotent DDL and migration identity refs.
- 失败回滚: rollback SQL and rollback guard are present.
- 恢复冒烟: checkpoint and rollback refs exist for future smoke tests.
- 不会写入原始大文件或无限制派生产物: payload size, raw-content, and
  forbidden-token guards are present.
- 连接池: pool and timeout limits are machine-readable.
- 事务边界: migration refs require single transaction and `ON_ERROR_STOP`.
- 约束错误可解释: each required constraint has an owner-facing explanation.

## Raw Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容。
- This phase does not inspect raw filenames, table contents, row values, schema
  details, credentials, private business values, or derived dumps.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据。

## Non-Goals
- 不连接 PostgreSQL。
- 不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff。
- 不创建 database、schema、runtime data directory、local service 或连接配置。
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact。
- 不提交 secrets、API key、数据库密码、DSN with credentials 或云端凭证。
- 不执行 GitHub upload、PR、merge 或 app reinstall。
- `NO_PHASE4`: this run must not produce final schema diff, real migration
  output, recovery test logs, destructive-migration approval, database rollback
  procedure, backup/restore procedure, whole-stage review, or closeout feedback.

## Verification Targets
- Stage031 focused tests validate `build_stage031_scenario_validation_report`,
  this evidence file, batch lock, roadmap, event, and no-upload gate.
- Stage005 governance regression accepts `IDS-STAGE031-P3` as the current local
  no-upload state.
- Full v0.1 discovery, Stage005 validator, render drift, event uniqueness,
  py_compile, diff checks, and sparse semantic diagnostic remain required before
  commit.

## Rollback
Revert the Phase 3 additions to `check_schema_migration_safety.py`, this
evidence file, Stage031/Stage005 tests, `BATCH031_040_UPLOAD_LOCK.yaml`,
roadmap/events, validator updates, and rendered owner-file changes. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, runtime data,
reports, outputs, manifests, evidence ledgers, audit logs, indexes, PostgreSQL
data directories, app entries, GitHub state, or Phase 4 artifacts.
