# IDS v0.1 STAGE-030 Entry Contract

## Identity
- Stage: `STAGE-030 · PostgreSQL 控制面启动`
- Task: `IDS-V0_1-STAGE030-P1`
- Acceptance: `ACC-STAGE-030`
- Local code: `D06-S001`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D06 · PostgreSQL 控制面`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-030_PostgreSQL控制面启动.md`

## Pursuing Goal
建立 metadata、job、document、chunk、evidence、audit、index version 的
PostgreSQL 控制面。

STAGE-030 starts the database-control-plane contract only. PostgreSQL control
plane records metadata, workflow state, hot index pointers, evidence references,
audit records, index version state, migration state, and recovery checkpoints.
PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件、原始数据库内容、生产
文档正文、压缩包正文、OCR 全文、向量大体积 payload、报告二进制或 secrets。

## Phase 1 Scope
Phase 1 defines schema, migration, connection, storage boundary, and recovery
requirements before any implementation. It records:

- PostgreSQL 控制面的 metadata、job、document、chunk、evidence、audit、
  index version table contract.
- Migration must support dry-run, repeatability checks, explicit rollback, and
  verification before use.
- Connection settings must be references only; secrets, API key, database
  password, DSN with credentials, or cloud credentials must not enter Git.
- Storage boundary: PostgreSQL can store path-only source refs, IDs, status,
  small scalar metadata, evidence refs, hot index pointers, and version state.
- Raw content boundary: PostgreSQL must not store raw files, raw database dumps,
  raw table rows, raw filenames from `/Users/linzezhang/Downloads/IDS_MetaData`,
  or fabricated data.
- Recovery boundary: future backup/restore smoke tests must prove migration
  rollback and metadata recovery without touching original raw data.

## Protected Materials
- `PROTECTED_IDS_METADATA_RAW_ROOT`: `/Users/linzezhang/Downloads/IDS_MetaData`.
- `PROTECTED_ORIGINAL_RAW_DATA`: `00_ORIGINAL_RAW_DATA` and any owner-provided
  raw material store.
- `PROTECTED_RAW_FILE_CONTENT`: original files, extracted files, archive bodies,
  OCR text, production document bodies, database dumps, row values, and reports.
- `PROTECTED_SECRETS`: API keys, database passwords, DSNs with credentials, cloud
  credentials, and plaintext secret config.
- `PROTECTED_RUNTIME_OUTPUT`: runtime SQLite files, PostgreSQL data directory,
  reports, outputs, evidence ledgers, audit logs, indexes, caches, and import
  queues unless a later stage explicitly authorizes a tracked, sanitized
  artifact.

## Non-Goals
- 不创建 PostgreSQL database、schema、migration 文件或连接配置.
- 不连接本机或远端 PostgreSQL.
- 不执行 migration、dry-run、rollback、backup 或 restore.
- 不写 runtime database、PostgreSQL data directory、manifest、evidence ledger、
  audit log、index、document/chunk/job/import row、report、output、cache 或 JSON
  output.
- 不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不提交 secrets、API key、数据库密码或云端凭证.
- 不移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.
- 不启动 backend、frontend、worker、PostgreSQL、Docker、dependency install、
  external API job、GitHub upload、PR、merge 或 app reinstall.
- 不进入 Phase 2.

## Raw Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` is recorded as a path-only read-only real database source boundary for GitHub-tracked governance.
- Raw database content remains outside GitHub and outside this Phase 1 run.
- Path-only reference is allowed; recursive listing, schema introspection,
  database opening, table reads, row reads, hashing, copying, dumping,
  normalizing, compacting, or modifying raw content is forbidden.
- Real data only: future runtime corpus, database-backed content, reports,
  indexes, manifests, and committed examples must use real user-approved data;
  不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据.

## Stop Gate
- Current gate: `IDS-STAGE030-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement schema, migrations, connection
  loading, PostgreSQL runtime behavior, backup/restore tests, data imports, hot
  index writes, or raw database access.
- `NO_RAW_DB_CONTENT`: PostgreSQL control plane may reference raw data by
  approved path or source id later, but must not store raw content.
