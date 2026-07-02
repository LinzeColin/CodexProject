# IDS v0.1 STAGE-017 Entry Contract

## Identity

- Stage: `STAGE-017`
- Local code: `D03-S006`
- Title: `原始资料回归测试`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-017`
- Parallel: `是`
- Parallel note: `可与 STAGE-024 的压缩包威胁模型、STAGE-152 的黄金测试集准备并行；至少在 STAGE-037 前完成。`
- Estimated time: `6-14 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-017_原始资料回归测试.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `29d9e298d0a79367405cf7c513dbabec0f9d2fcf15f3dac8719c0cd82fe56954`

## Pursuing Goal

验证重复扫描、断点续扫、移动硬盘离线恢复不会污染原始数据或重复登记。

## Required Reads For STAGE-017

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-017_原始资料回归测试.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 through STAGE-016 evidence, because the regression test must
    inherit original-material read-only identity, fingerprint, manifest,
    duplicate-detection, and import-idempotency boundaries.

## Stage Boundary

STAGE-017 defines and later verifies regression behavior for original-material
handling. It covers repeated scan, resumable scan after an interrupted run, and
offline/reconnected removable-drive recovery. The stage must prove these flows
do not mutate original source materials and do not create duplicate document,
chunk, job, index, manifest, import, duplicate, evidence, audit, or report
records.

The stage inherits these non-negotiable rules:

- original files and `00_ORIGINAL_RAW_DATA` remain read-only and are never
  moved, deleted, overwritten, compacted, deduplicated in place, or normalized;
- `/Users/linzezhang/Downloads/IDS_MetaData` is recorded only as a local
  boundary path and must not be listed, opened, hashed, copied, dumped,
  scanned, modified, deleted, moved, or committed;
- real user-approved data is required for future IDS corpus or database-backed
  behavior, and fake business data or fabricated evidence is forbidden;
- `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at` remain the
  minimum source identity fields;
- repeated observations must compare against stable identity and idempotency
  keys before any future persistence write is allowed;
- same hash at different paths preserves separate provenance;
- same basename with different hashes remains a conflict/version candidate;
- removable-drive offline recovery must fail closed until a reconnected source
  is explicitly revalidated by bounded metadata identity.

## Phase Boundary

STAGE-017 must be split into phase-limited runs. Do not implement all of
STAGE-017 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, duplicate recognition, repeated-scan, resume, and offline-drive
   recovery rules.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`
   fields for regression-test decisions.

### Phase 2：实现、接入与最小可运行切片

1. Implement a minimum regression-test slice on bounded explicit metadata
   inputs only.
2. Ensure repeated scan and resume attempts do not duplicate or pollute
   database rows, document rows, chunk rows, jobs, indexes, import records, or
   manifests.
3. Put missing, blocked, offline, drifted, unsupported, and duplicate inputs
   into explicit states instead of silently skipping them.

### Phase 3：原始资料回归测试 专项验证与异常场景

1. Validate same-file/same-hash repeated scan, same-name/different-hash,
   same-hash/different-path, interrupted resume, offline drive, reconnected
   drive revalidation, and unsupported input states.
2. Validate repeated import does not create duplicate document, chunk, job,
   index, manifest, import, duplicate, evidence, audit, or report records.
3. Validate original-material hash stability and no mutation.

### Phase 4：原始资料回归测试 交付证据、回滚与中文反馈

1. Deliver manifest examples, duplicate-detection reports, resume/offline
   recovery summaries, and original-file protection proof.
2. Record conflicts, duplicates, unsupported inputs, blocked states, and
   owner-facing interpretation.
3. Provide rollback steps that never delete, move, overwrite, or rewrite
   original materials.

## Acceptance Summary

- The regression-test capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Repeated-scan, resume, offline-drive, duplicate, conflict, drift, unsupported,
  audit, stop, and rollback states are clear.
- Original materials, manifests, evidence ledgers, audit logs, indexes,
  delivered reports, and raw metadata boundaries are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, open, dump,
  hash, copy, or mutate original source materials or
  `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action creates unbounded manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  generated reports, document rows, chunk rows, job rows, import rows, or
  duplicate ledgers.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, app entries are reinstalled, and the batch gate allows upload.

## Rollback

Rollback STAGE-017 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, indexes, delivered reports,
STAGE-012 identity evidence, STAGE-013 fingerprint evidence, STAGE-014
manifest evidence, STAGE-015 duplicate-detection evidence, or STAGE-016
import-idempotency evidence.
