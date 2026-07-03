# IDS v0.1 STAGE-027 Phase 1 Scope Boundary

## Scope
- Stage: `STAGE-027 · 解压文件重新入库`
- Task: `IDS-V0_1-STAGE027-P1`
- Acceptance: `ACC-STAGE-027`
- Local code: `D05-S004`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Recorded at UTC: `2026-07-03T07:46:28Z`

This phase defines the future extracted-file re-ingest contract. It does not
read extracted file content, compute hashes, copy files, create import jobs,
write runtime output, or start any downstream processing.

## Contract Fields
- `reingest_job_id`: stable id for one future extracted-file re-ingest evaluation.
- `reingest_batch_id`: stable id grouping extracted files from one owner-approved archive manifest.
- `extracted_file_ref`: immutable reference to one extracted file from a safe extraction result.
- `extracted_file_uri`: path-only URI for a future owner-approved extracted file; Phase 1 does not open it.
- `archive_manifest_ref`: immutable reference to the STAGE-026 archive manifest that listed the extracted file.
- `original_archive_ref`: immutable reference to the original archive; original archive content remains untouched.
- `safe_extraction_ref`: immutable reference to the STAGE-025 safe extraction result that produced the extracted-file candidate.
- `reingest_source_state`: state of the extracted-file source reference before any downstream work.
- `reingest_idempotency_key`: future key combining original archive identity, archive manifest identity, extracted relative path, and extracted-file hash observation.
- `reingest_duplicate_policy`: future duplicate routing policy before parser or import queue handoff.
- `reingest_owner_decision_state`: owner-visible decision state for the future re-ingest candidate.
- `reingest_required_pipeline`: fixed pipeline order `hash`, `manifest`, `dedup`, `parser`.
- `reingest_import_queue_ref`: future import queue reference; Phase 1 does not create it.

## Owner And System States
- `REINGEST_DRAFT`: re-ingest boundary exists but source refs, manifest refs, idempotency policy, and owner approval are incomplete.
- `REINGEST_BLOCKED`: raw-root path, missing file, unsafe source, ambiguous manifest, original-archive overwrite risk, or unsupported owner decision blocks the candidate.
- `REINGEST_OWNER_REVIEW_REQUIRED`: source, duplicate, parser, priority, or preflight state requires owner review before any future pipeline step.
- `REINGEST_READY_FOR_HASH`: owner-approved extracted-file reference can enter a future hash observation gate.
- `REINGEST_READY_FOR_MANIFEST`: future hash observation is complete and the file can enter manifest update.
- `REINGEST_READY_FOR_DEDUP`: future manifest update is complete and duplicate detection can run.
- `REINGEST_READY_FOR_PARSER`: future dedup result permits parser handoff.
- `REINGEST_READY_FOR_IMPORT_QUEUE`: future parser/preflight result permits import queue evaluation.

## Re-Ingest Pipeline Rules
- STAGE-025 safe extraction may only provide `safe_extraction_ref`; it does not authorize import.
- STAGE-026 archive manifest must provide `archive_manifest_ref`, `original_archive_ref`, and extracted-entry identity before re-ingest.
- STAGE-016 import idempotency rules must apply before import queue writes.
- STAGE-018 import preflight rules must apply before parser/import handoff.
- STAGE-021 owner confirmation must remain required when a candidate is blocked, duplicated, high-risk, missing, or ambiguous.
- STAGE-022 data priority queue may influence future processing order but cannot bypass hash, manifest, dedup, or parser.
- STAGE-023 preflight scenario coverage must remain compatible with re-ingest cases.
- Future extracted files must enter `hash` first, then `manifest`, then `dedup`, then `parser`; they cannot enter index, import, OCR, Embedding, report, or database writes directly from extraction staging.
- Future re-ingest must be idempotent across repeated archive extraction, repeated manifest generation, and repeated owner confirmation.

## Boundary
- 不执行重新入库.
- 不读取真实 extracted file 内容.
- 不打开、hash 或复制真实 extracted file.
- 不创建或修改 extracted file、staging file、manifest、import queue、runtime report、database、evidence ledger、audit log、index、parser output、screenshot、PDF 或 JSON output.
- 不写 reingest runtime output.
- 不创建 document/chunk/job/index/import row.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入.
- 不覆盖、移动、删除、清理原始压缩包或事实源.
- 不将 archive manifest、safe extraction output 或 Phase 1 contract 当成生产导入授权.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE2`: do not implement re-ingest runtime output, extracted file reading, hash/manifest/dedup/parser execution, import queue writes, document/chunk/job/index/import rows, OCR, Embedding, index, report, or production import behavior in this run.

## Rollback
Revert this Phase 1 entry contract, scope boundary, focused tests, BATCH021_030
lock update, Stage005 validator/test updates, roadmap/event updates, and rendered
owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`,
runtime data, reports, outputs, extracted files, staging files, persisted
manifests, evidence ledgers, audit logs, indexes, app entries, GitHub state, or
Phase 2 artifacts.
