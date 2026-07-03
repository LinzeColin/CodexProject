# IDS v0.1 STAGE-030 Phase 3 Scenario Validation

## Scope
- Schema: `ids.stage030.postgresql_control_plane.phase3.v1`
- Stage: `STAGE-030 · PostgreSQL 控制面启动`
- Task: `IDS-V0_1-STAGE030-P3`
- Acceptance: `ACC-STAGE-030`
- Phase: `Phase 3 · PostgreSQL 控制面启动 专项验证与异常场景`
- Recorded at UTC: `2026-07-03T08:18:00Z`

This phase validates PostgreSQL control-plane migration and failure scenarios
from tracked SQL and machine-readable index contracts. It uses
`build_stage030_scenario_report` in `check_postgresql_control_plane.py`.

It does not connect to PostgreSQL, execute real DDL, create a database, start a
service, install dependencies, or write runtime outputs.

## Scenario Coverage
- `migration_dry_run`: verifies `-- migrate:up`, `-- migrate:down`,
  `dry_run_required=true`, `ON_ERROR_STOP=1`, and `--single-transaction`.
- `repeat_execution`: verifies repeat execution is guarded by
  `CREATE TABLE IF NOT EXISTS` and `ids_schema_migrations`.
- `failure_rollback`: verifies `rollback_required=true` and reverse
  `DROP TABLE IF EXISTS` rollback text.
- `recovery_smoke`: verifies `recovery_checkpoint_ref` and `rollback_sql_ref`
  are recorded for control-plane recovery smoke.
- `raw_payload_block`: verifies the database will not write raw large files,
  raw database rows, full document bodies, OCR text, vector payloads, report
  binaries, secrets, or unbounded derived payloads.
- `connection_pool_boundary`: verifies max pool size, statement timeout, lock
  timeout, and idle timeout guards.
- `transaction_boundary`: verifies single-transaction and fail-fast migration
  references with destructive migrations blocked by default.
- `constraint_error_explanations`: verifies constraint errors are explainable
  for payload size, connection pool, raw content, fact level, and index state.

## Acceptance Mapping
- migration dry-run: static contract requires dry-run command refs before any
  apply command.
- 重复执行: table DDL is repeat-safe and migration identity is recorded.
- 失败回滚: rollback SQL is present and destructive migration is blocked.
- 恢复冒烟: recovery checkpoint refs exist for future runtime smoke tests.
- 不会写入原始大文件或无限制派生产物: payload size, raw-content, and
  forbidden-token guards are enforced.
- 连接池: pool and timeout limits are machine-readable.
- 事务边界: migration refs require single transaction and `ON_ERROR_STOP`.
- 约束错误可解释: each required constraint has an owner-facing explanation.

## Raw Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容。
- This phase does not inspect raw filenames, table contents, row values,
  schema details, credentials, private business values, or derived dumps.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus
  或伪造证据.

## Non-Goals
- 不连接 PostgreSQL.
- 不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff.
- 不创建 database、schema、runtime data directory、local service 或连接配置.
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser output
  或 production data artifact.
- 不提交 secrets、API key、数据库密码、DSN with credentials 或云端凭证.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE4`: this run must not produce final schema diff, real migration
  output, recovery test logs, destructive-migration approval, database rollback
  procedure, backup/restore procedure, whole-stage review, or closeout feedback.

## Verification Targets
- Stage030 focused tests validate `build_stage030_scenario_report`, this
  evidence file, batch lock, roadmap, event, and no-upload gate.
- Stage005 governance regression accepts `IDS-STAGE030-P3` as current local
  no-upload state.
- Compatibility tests for STAGE-026 through STAGE-029 accept the later
  STAGE-030 Phase 3 state.
- Full v0.1 discovery, validator, render drift, event uniqueness, and sparse
  semantic diagnostic remain required before commit.

## Rollback
Revert the Phase 3 additions to `check_postgresql_control_plane.py`, this
evidence file, Stage030/Stage005 tests, BATCH021_030 lock, roadmap/events,
compatibility-test updates, validator updates, and rendered owner-file changes.
Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`,
runtime data, reports, outputs, manifests, evidence ledgers, audit logs, indexes,
PostgreSQL data directories, app entries, GitHub state, or Phase 4 artifacts.
