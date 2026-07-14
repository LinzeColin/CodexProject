# IDS v0.1 STAGE-033 Phase 2 Database Size Guard Slice

## Scope
- Schema version: `ids.stage033.database_size_guard.phase2.v1`
- Stage: `STAGE-033 · 数据库体积护栏`
- Task: `IDS-V0_1-STAGE033-P2`
- Acceptance: `ACC-STAGE-033`
- Local code: `D06-S004`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 静态数据库体积护栏切片`
- Recorded at UTC: `2026-07-03T11:42:03Z`

This phase implements a static, machine-readable database size guard slice. It
does not connect to PostgreSQL, create a live database/schema/migration,
create a DSN or credential-bearing connection config, run size-statistics
queries, execute VACUUM/reindex/cleanup/backup/restore, start services, install
dependencies, write runtime outputs, or inspect raw metadata content.

## Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md` |
| Stage file SHA-256 | `454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777` |
| Prior phase | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE1_SCOPE_BOUNDARY.md` |
| Stage 030 schema dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql` |
| Stage 031 migration-safety dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json` |
| Stage 032 connection-pool dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json` |
| Static checker | `KM_IDSystem/scripts/check_database_size_guard.py` |

The taskpack source was already bound in Phase 1. This phase records tracked
policy and validation artifacts only; it does not extract the taskpack into the
worktree and does not inspect `/Users/linzezhang/Downloads/IDS_MetaData`.

## Implemented Static Slice

- `DATABASE_SIZE_GUARD_STATIC_SLICE`: a Git-tracked JSON index defines database
  storage scope, blocked payload classes, policy thresholds, table/index/row
  bounds, cleanup stop gates, connection-pool budget dependency, quality
  constraints, rollback verification, raw-data boundary, and real-data-only
  policy.
- `schema_change_plan`: records a static schema/migration/config contract for
  Phase 2. It names the future migration identity and tracked constraints, but
  `sql_file_created=false`, `migration_executed=false`,
  `connection_config_created=false`, `recovery_smoke_executed=false`, and
  `live_schema_diff_executed=false`.
- `database_size_budget_guard`: records policy thresholds, not measured runtime
  facts. The 800 GiB internal disk is the protection boundary; warning and hard
  stop thresholds are static owner-facing guardrails, not a database-size
  measurement.
- `check_database_size_guard.py`: validates the tracked index and prints a JSON
  report to stdout only. It does not persist reports, create output files, read
  the raw metadata root, query PostgreSQL, or run cleanup.

## Guardrails

- PostgreSQL 只存控制面、状态和热索引.
- PostgreSQL 不存 500GB 原始文件.
- PostgreSQL 不存 OCR 全文.
- PostgreSQL 不存无限制派生产物.
- 保护 800GB 内置盘.
- Raw content guard: raw metadata database content, raw rows, source file bodies,
  protected-root payloads, and archive bodies are blocked from PostgreSQL.
- Large artifact guard: report binaries, PDF bodies, ZIP/archive bodies, media
  blobs, large vector payloads, and unbounded JSON dumps are blocked.
- Derived artifact guard: PostgreSQL may store path-only refs, manifest refs,
  evidence refs, audit refs, report refs, source refs, bounded hot-index
  metadata, and re-creatable state refs only.
- Table/index/payload guard: table budgets, index-bloat thresholds, row payload
  size caps, and no raw payload column policy are recorded as static
  constraints for later runnable stages.
- Cleanup guard: cleanup remains `dry_run_only`; auto-delete, VACUUM, reindex,
  backup, restore, and post-cleanup verification are not executed in this
  phase. Any deletion requires a later owner stop gate.
- Connection-pool guard: this size guard depends on the STAGE-032 aggregate pool
  limit and does not increase pool size or overflow.
- Quality guard: real data only. 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` is recorded as a path-only,
read-only real database source boundary. This phase does not read, list, hash,
open, copy, move, delete, modify, dump, scan, normalize, or commit any content
from that location. `NO_RAW_DB_CONTENT` remains active.

## Explicit Non-Goals

- `NO_POSTGRES_CONNECTION`: no local or remote PostgreSQL connection is opened.
- `NO_LIVE_MIGRATION`: no migration dry-run, apply, rollback, backup, restore,
  schema diff, checksum verification, recovery smoke, VACUUM, reindex, cleanup,
  or size-statistics command is executed.
- `NO_SIZE_GUARD_RUNTIME`: no table scan, `pg_total_relation_size` query,
  index-bloat query, cleanup job, retention deletion job, database monitor, or
  disk monitor is instantiated.
- `NO_RAW_DB_CONTENT`: no raw metadata database content or raw 500GB corpus
  content is read, listed, hashed, opened, copied, moved, deleted, modified,
  dumped, scanned, normalized, or committed.
- No runtime output, database, manifest, evidence ledger, audit log, report,
  PDF, screenshot, JSON output file, document/chunk/job/import row, parser
  output, PostgreSQL statistics output, cleanup output, or production data
  artifact is generated.
- No GitHub upload, PR, merge, app reinstall, batch review, upload gate, or
  Phase 3 work is performed.

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE2_DATABASE_SIZE_GUARD_SLICE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json`
- `KM_IDSystem/scripts/check_database_size_guard.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## Rollback

Revert only `IDS-V0_1-STAGE033-P2` evidence, the static database-size guard
index, the static checker, focused tests, Stage005 validator/test updates,
`BATCH031_040_UPLOAD_LOCK.yaml`, roadmap/event updates, compatibility-test
updates, and rendered owner-file changes. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, runtime
data, reports, outputs, manifests, evidence ledgers, audit logs, app entries,
GitHub state, PostgreSQL data directories, size-statistics outputs, cleanup
outputs, or Phase 3 artifacts.
