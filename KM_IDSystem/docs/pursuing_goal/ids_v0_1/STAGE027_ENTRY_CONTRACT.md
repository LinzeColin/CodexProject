# IDS v0.1 STAGE-027 Entry Contract

## Identity
- Stage: `STAGE-027 · 解压文件重新入库`
- Task: `IDS-V0_1-STAGE027-P1`
- Acceptance: `ACC-STAGE-027`
- Local code: `D05-S004`
- Entrance: `IDS 系统运营入口`
- Capability domain: `D05 · 自动解压与压缩包安全`
- Taskpack path: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-027_解压文件重新入库.md`

## Pursuing Goal
安全解压后的文件不能直接进入索引、导入或业务数据库。STAGE-027 defines
the future re-ingest entry contract that routes extracted files back through
`hash`, `manifest`, `dedup`, and `parser` gates before any import queue or index
work can start.

## Phase 1 Scope
Phase 1 defines the extracted-file re-ingest boundary only. It records:
- `STAGE-025` safe extraction output may become a future source reference.
- `STAGE-026` archive manifest output must identify the extracted-file list and original archive reference.
- Extracted file references must be path-only and owner-approved until a future gated run.
- Re-ingest must be idempotent and duplicate-aware before parser/import handoff.
- Re-ingest states must remain owner-visible and block unsafe, missing, ambiguous, duplicate, or raw-root paths.
- Every future extracted file must re-enter `hash`, `manifest`, `dedup`, and `parser` before import queue, indexing, OCR, Embedding, or reporting.

## Relationship To Earlier Stages
STAGE-016 defines import idempotency. STAGE-018 defines import preflight.
STAGE-021 through STAGE-023 define owner confirmation, data priority, and
preflight scenario coverage. STAGE-025 defines the safe extraction engine.
STAGE-026 defines the archive manifest. STAGE-027 binds those results into a
future re-ingest entry contract without executing the pipeline.

## Non-Goals
- 不执行重新入库.
- 不读取真实 extracted file 内容.
- 不打开、hash 或复制真实 extracted file.
- 不写 reingest runtime output.
- 不创建 reingest staging, manifest, import queue, document/chunk/job/index/import row, evidence ledger, audit log, report, database, screenshot, PDF, or JSON output.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不覆盖、移动、删除、清理原始压缩包或事实源.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- 不进入 Phase 2.

## Raw Data Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得提交真实原始资料、secrets、API key、数据库密码或云端凭证.
- 不得移动、删除、覆盖 `00_ORIGINAL_RAW_DATA`.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.

## Stop Gate
- Current gate: `IDS-STAGE027-P2-GATE`
- Current status: `phase1_scope_boundary_defined`
- `NO_PHASE2`: this run must not implement re-ingest runtime output, extracted file reading, hash/manifest/dedup/parser execution, import queue writes, document/chunk/job/index/import rows, OCR, Embedding, index, report, or production import behavior.
