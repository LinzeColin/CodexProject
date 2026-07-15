# IDS v0.1 STAGE-031 Entry Contract

## Taskpack Identity
- Stage: `STAGE-031 · Schema 迁移安全`
- Task: `IDS-V0_1-STAGE031-P1`
- Acceptance: `ACC-STAGE-031`
- Version: `v0.1`
- Local code: `D06-S002`
- Domain: `D06 · PostgreSQL 控制面`
- Entrance: `IDS 系统运营入口`
- Pursuing goal: `所有 schema migration 必须有 dry-run、备份、校验和回滚。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-031_Schema迁移安全.md`
- P0 stage file SHA-256:
  `17a91f01a284d4046a0a17f17f02a5be60b2c351b82a91c87c9c75106800be88`

## Preconditions
- `STAGE-021..030` is uploaded to GitHub main and app entries have been reinstalled.
- `STAGE-031` starts the next ten-stage batch lock: `BATCH031_040_UPLOAD_LOCK.yaml`.
- `STAGE-030` already defined a PostgreSQL control-plane contract; this stage narrows the migration-safety gate and does not execute migrations.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary. This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit raw database content.

## Phase 1 Contract
`IDS-V0_1-STAGE031-P1` defines the schema migration safety boundary for later implementation. It records the required dry-run, backup, validation, rollback, recovery smoke, audit, and owner stop-gate fields that every future PostgreSQL schema migration must satisfy before it can be applied.

Phase 1 is a contract-only phase:
- It defines migration-safety inputs and outputs without creating SQL files, migration scripts, runtime databases, or connection configs.
- It confirms PostgreSQL migration records must stay control-plane only and must not contain raw 500GB corpus content, raw database rows, secrets, report binaries, OCR full text, or fabricated business data.
- It defines rollback as mandatory: every future schema migration must include dry-run evidence, backup checkpoint evidence, validation evidence, and rollback/recovery evidence.
- It marks destructive migration as owner-stop-gated, not auto-approved.

## Explicit Non-Goals
- `NO_PHASE2`: do not implement schema, migration scripts, connection loading, runtime migration verification, backup/restore smoke tests, hot-index writes, UI controls, or runnable database behavior.
- `NO_LIVE_MIGRATION`: do not execute migration dry-run, apply, rollback, backup, restore, schema diff, checksum verification, or recovery smoke commands.
- `NO_POSTGRES_CONNECTION`: do not connect to local or remote PostgreSQL and do not create a PostgreSQL database, schema, migration file, connection config, or data directory.
- `NO_RAW_DB_CONTENT`: do not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit `/Users/linzezhang/Downloads/IDS_MetaData` raw metadata database content.
- Do not start backend, frontend, worker, Docker, dependency install, external API calls, GitHub upload, PR, merge, app reinstall, or Phase 2 work.
- Do not write runtime output, database, manifest, evidence ledger, audit log, index, report, PDF, screenshot, JSON output, document/chunk/job/import row, parser output, or production data artifact.
- Do not submit secrets, API key, database password, credential-bearing DSN, or cloud credentials.
- Do not use fake IDS business data, fake database rows, fake source documents, placeholder corpus, or fabricated evidence.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_schema_migration_safety.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
