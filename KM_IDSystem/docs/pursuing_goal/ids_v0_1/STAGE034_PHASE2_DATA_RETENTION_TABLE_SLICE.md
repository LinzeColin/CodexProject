# IDS v0.1 STAGE-034 Phase 2 Data Retention Table Slice

## Scope
- Schema version: `ids.stage034.data_retention_table.phase2.v1`
- Stage: `STAGE-034 · 数据保留表`
- Task: `IDS-V0_1-STAGE034-P2`
- Acceptance: `ACC-STAGE-034`
- Local code: `D06-S005`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 2 · 静态数据保留表切片`
- Recorded at UTC: `2026-07-04T00:38:19Z`

This phase implements a static, machine-readable data retention table slice. It
does not connect to PostgreSQL, create a live database/schema/migration, create
a DSN or credential-bearing connection config, run retention cleanup, execute
deletion, compact logs, evict caches, rebuild old indexes, prune report
snapshots, start services, install dependencies, write runtime outputs, or
inspect raw metadata content.

## Source Binding

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md` |
| Stage file SHA-256 | `af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d` |
| Prior phase | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE1_SCOPE_BOUNDARY.md` |
| Stage 030 schema dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql` |
| Stage 031 migration-safety dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json` |
| Stage 032 connection-pool dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_connection_pool/stage032_connection_pool_index.json` |
| Stage 033 database-size dependency | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/database_size_guard/stage033_database_size_guard_index.json` |
| Machine index | `KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json` |
| Static checker | `KM_IDSystem/scripts/check_data_retention_table.py` |

The taskpack source was read directly from the user-provided v0.1 taskpack zip
in Phase 1. This phase records tracked policy and validation artifacts only; it
does not extract the taskpack into the worktree and does not inspect
`/Users/linzezhang/Downloads/IDS_MetaData`.

## Implemented Static Slice

- `DATA_RETENTION_TABLE_STATIC_SLICE`: a Git-tracked JSON index defines the
  retention subject class enum, TTL policy, owner hold policy, cleanup dry-run
  requirement, deletion stop gate, audit evidence requirement, rollback/restore
  requirement, PostgreSQL storage scope, database-size guard dependency,
  connection-pool budget dependency, raw metadata boundary, and real-data-only
  policy.
- `schema_change_plan`: records a static schema/migration/config contract for
  Phase 2. It names the future migration identity and tracked constraints, but
  `sql_file_created=false`, `migration_executed=false`,
  `connection_config_created=false`, `recovery_smoke_executed=false`, and
  `live_schema_diff_executed=false`.
- `retention_subjects`: records the five allowed retention classes:
  `temporary_file`（临时文件）, `cache`（缓存）, `old_index`（旧索引）,
  `log`（日志）, and `report_snapshot`（报告快照）. Every subject requires TTL,
  owner hold policy, cleanup mode, deletion gate, audit evidence, and
  rollback/restore requirements, and every subject has `stores_raw_content=false`.
- `check_data_retention_table.py`: validates the tracked index and prints a JSON
  report to stdout only. It does not persist reports, create output files, read
  the raw metadata root, query PostgreSQL, or run cleanup/deletion.

## Guardrails

- `retention_subject_class_guard`: data retention table only covers 临时文件,
  缓存, 旧索引, 日志, and 报告快照; unknown or raw-payload subjects are blocked.
- `ttl_policy_guard`: every retention subject must define TTL, keep-until,
  warning window, and owner-readable expiration reason. Runtime expiry scans are
  not allowed in this phase.
- `owner_hold_guard`: manual hold and compliance hold block cleanup, deletion,
  compaction, cache eviction, old-index rebuild, and report snapshot pruning.
- `cleanup_dry_run_guard`: cleanup defaults to `dry_run_only`; an owner impact
  report and no-delete proof are required before future destructive action.
- `deletion_stop_gate_guard`: deletion, retention cleanup, log compaction, cache
  eviction, old-index rebuild, and report snapshot pruning are blocked until a
  later owner stop gate explicitly authorizes them.
- `audit_evidence_guard`: every future retention state transition must include
  event ref, evidence ref, fact level, and Chinese owner reason.
- `rollback_restore_guard`: future cleanup or deletion must have rollback,
  restore, backup, and post-cleanup verification evidence.
- `postgres_storage_scope_guard`: PostgreSQL may store bounded retention-policy
  metadata and refs only; it must not store raw files, raw database rows,
  document bodies, OCR full text, vector payloads, report binaries, raw log
  bodies, or unbounded derived artifacts.
- `database_size_guard_dependency`: this stage depends on STAGE-033 and must not
  override raw/large/OCR payload blocks or run size queries.
- `connection_pool_budget_guard`: this stage depends on STAGE-032 and does not
  increase pool size or overflow.
- `real_data_only_guard`: 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、
  placeholder corpus 或伪造证据.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` is recorded as a path-only,
read-only real database source boundary. This phase does not read, list, hash,
open, copy, move, delete, modify, dump, scan, normalize, or commit any content
from that location. `NO_RAW_DB_CONTENT` remains active.

## Explicit Non-Goals

- `NO_POSTGRES_CONNECTION`: no local or remote PostgreSQL connection is opened.
- `NO_LIVE_MIGRATION`: no migration dry-run, apply, rollback, backup, restore,
  schema diff, checksum verification, recovery smoke, cleanup, deletion,
  retention scan, log compaction, cache eviction, old-index rebuild, report
  snapshot pruning, or PostgreSQL command is executed.
- `NO_RAW_DB_CONTENT`: no raw metadata database content, raw rows, raw filenames
  from protected roots, report binaries, raw logs, raw OCR text, or raw 500GB
  corpus content is read, listed, hashed, opened, copied, moved, deleted,
  modified, dumped, scanned, normalized, or committed.
- No runtime output, database, manifest, evidence ledger, audit log, report,
  PDF, screenshot, JSON output file, document/chunk/job/import row, parser
  output, retention output, cleanup output, deletion output, log-compaction
  output, cache-eviction output, index-rebuild output, report-snapshot output,
  or production data artifact is generated.
- No GitHub upload, PR, merge, app reinstall, batch review, upload gate, or
  Phase 3 work is performed.

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE2_DATA_RETENTION_TABLE_SLICE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/data_retention_table/stage034_data_retention_table_index.json`
- `KM_IDSystem/scripts/check_data_retention_table.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_data_retention_table.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`

## Rollback

Revert only `IDS-V0_1-STAGE034-P2` evidence, the static data-retention table
index, the static checker, focused tests, Stage005 validator/test updates,
`BATCH031_040_UPLOAD_LOCK.yaml`, roadmap/event updates, compatibility-test
updates, and rendered owner-file changes. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, `00_ORIGINAL_RAW_DATA`, runtime
data, reports, outputs, manifests, evidence ledgers, audit logs, indexes, app
entries, GitHub state, PostgreSQL data directories, retention outputs, cleanup
outputs, deletion outputs, log-compaction outputs, cache-eviction outputs,
index-rebuild outputs, report-snapshot outputs, or Phase 3 artifacts.
