# IDS v0.1 STAGE-032 Phase 3 Scenario Validation

## Scope
- Schema version: `ids.stage032.database_connection_pool.phase3.v1`
- Stage: `STAGE-032 · 数据库连接与连接池基线`
- Task: `IDS-V0_1-STAGE032-P3`
- Acceptance: `ACC-STAGE-032`
- Local code: `D06-S003`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 3 · 数据库连接与连接池基线 专项验证与异常场景`
- Recorded at UTC: `2026-07-03T10:43:08Z`

This phase validates database connection and connection-pool baseline scenarios
from tracked Git contracts only. It uses
`build_stage032_scenario_validation_report` in
`KM_IDSystem/scripts/check_database_connection_pool.py` and the static machine
index at
`KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json`.

It does not connect to PostgreSQL, instantiate pools, create DSNs, execute live
migration dry-run, apply, rollback, backup, restore, schema diff, create a
database, start services, install dependencies, inspect raw metadata, or write
runtime outputs.

## Scenario Coverage

- `migration_dry_run`: verifies Stage030 schema and Stage031 migration-safety
  refs are present, while this phase keeps `execute_migration=false`.
- `repeat_execution`: verifies a stable `connection_pool_contract_id` and no
  runtime pool instantiation, so repeated validation stays idempotent.
- `failure_rollback`: verifies rollback-sensitive transaction guardrails and
  Stage031 migration-safety refs without executing rollback.
- `recovery_smoke`: verifies future safe readiness/healthcheck contracts do not
  write database rows, echo secrets, or touch raw metadata.
- `raw_payload_block`: verifies storage, raw metadata boundary, and real-data
  guardrails block raw files, raw database rows, document bodies, OCR full text,
  vector payloads, report binaries, secrets, fake IDS business data, and
  fabricated evidence.
- `derived_output_limit`: verifies runtime output writing is disabled and
  report/vector payload storage is blocked.
- `connection_pool_boundary`: verifies backend, worker, report-task, and
  retrieval-task profiles have bounded pool sizes, no overflow, bounded
  timeout values, and owner-readable stop reasons.
- `transaction_boundary`: verifies explicit transaction, rollback, idempotency,
  retry/backoff, and non-retryable raw boundary errors.
- `constraint_error_explanations`: verifies credential, pool-size, timeout,
  transaction, retry/backoff, healthcheck, storage, raw metadata boundary, and
  real-data guardrails all have owner-facing explanations.

## Acceptance Mapping

- migration dry-run: upstream Stage030/Stage031 refs are present; this phase
  records why no live dry-run is executed.
- 重复执行: connection-pool strategy validation is static, idempotent, and bound
  to `ids_stage032_connection_pool_static_baseline`.
- 失败回滚: transaction and retry guards require rollback and owner-readable
  stop reasons before any future runnable slice.
- 恢复冒烟: future healthcheck contract is safe and read-only.
- 不会写入原始大文件或无限制派生产物: storage boundary blocks raw files,
  raw database rows, document bodies, OCR full text, vector payloads, report
  binaries, secrets, and runtime output files.
- 连接池: backend、worker、报告任务、检索任务的 pool size 和 timeout 限制均可机器验证。
- 事务边界: every role has explicit transaction boundary and retry/backoff
  behavior.
- 约束错误可解释: each required guardrail has a Chinese owner-facing
  explanation.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only.
This phase does not read, list, hash, open, copy, move, delete, modify, dump,
scan, normalize, or commit content from that location. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容.

不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Non-Goals

- 不连接 PostgreSQL。
- 不实例化 backend、worker、report task 或 retrieval task connection pool。
- 不创建 DSN、credential-bearing config、database、schema、runtime data
  directory、local service 或连接配置。
- 不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff。
- 不写 runtime output、database、manifest、evidence ledger、audit log、index、
  report、PDF、screenshot、JSON output、document/chunk/job/import row、parser
  output 或 production data artifact。
- 不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证。
- 不执行 GitHub upload、PR、merge、app reinstall、batch review 或 upload gate。
- `NO_PHASE4`: this run must not produce final schema diff, real migration
  output, recovery test logs, destructive-migration approval, database rollback
  procedure, backup/restore procedure, whole-stage review, or closeout feedback.

## Verification Targets

- Stage032 focused tests validate `build_stage032_scenario_validation_report`,
  this evidence file, batch lock, roadmap, event, checker output, and no-upload
  gate.
- Stage005 governance regression accepts `IDS-STAGE032-P3` as the current local
  no-upload state.
- Full v0.1 discovery, Stage005 validator, render drift, event uniqueness,
  py_compile, diff checks, and sparse semantic diagnostic remain required before
  commit.

## Rollback

Revert the Phase 3 additions to `check_database_connection_pool.py`, this
evidence file, Stage032/Stage005 tests, `BATCH031_040_UPLOAD_LOCK.yaml`,
roadmap/events, validator updates, compatibility-test updates, and rendered
owner-file changes. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
`00_ORIGINAL_RAW_DATA`, runtime data, reports, outputs, manifests, evidence
ledgers, audit logs, indexes, PostgreSQL data directories, app entries, GitHub
state, or Phase 4 artifacts.
