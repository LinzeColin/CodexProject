# IDS v0.1 STAGE-015 Entry Contract

## Identity

- Stage: `STAGE-015`
- Local code: `D03-S004`
- Title: `重复文件检测`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-015`
- Parallel: `否`
- Parallel note: `本 Stage 涉及共享契约、状态机、数据库、索引、证据、报告或执行规则，建议单独完成后再进入下游。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-015_重复文件检测.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `5c2f7e743862db9ae6bfdc0dd876335398322a8d6881fc052bbc7d48337f3be1`

## Pursuing Goal

识别同 hash 不同路径、同名不同 hash、重复批量导入和版本冲突。

## Required Reads For STAGE-015

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-015_重复文件检测.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012, STAGE-013, and STAGE-014 evidence, because duplicate-file
    detection must inherit original-material read-only identity,
    file-fingerprint, manifest, idempotency, conflict, and no-mutation rules.

## Stage Boundary

STAGE-015 defines and later implements duplicate-file detection. It compares
bounded metadata and fingerprint facts; it is not a content scanner and does
not require reading raw source payloads in Phase 1.

Duplicate-file detection must preserve these rules:

- original files remain read-only and are never moved, deleted, overwritten, or
  deduplicated in place;
- duplicate detection uses explicit `source_uri`, `sha256`, `file_size`,
  `mtime`, `first_seen_at`, and manifest/fingerprint evidence from prior
  bounded stages;
- same hash at different paths is duplicate content with preserved provenance,
  not an instruction to delete or merge files;
- same basename with different hashes is a version/conflict candidate, not an
  overwrite;
- repeated batch import must not create duplicate document rows, chunk rows,
  job rows, evidence ledger facts, audit events, reports, manifests, or
  duplicate-detection facts;
- no fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence may be used.

## Phase Boundary

STAGE-015 must be split into phase-limited runs. Do not implement all of
STAGE-015 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, and duplicate-recognition rules.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`
   fields for duplicate comparisons.

### Phase 2：实现、接入与最小可运行切片

1. Implement a minimum duplicate detection slice on bounded explicit inputs.
2. Ensure repeated scans or batch imports do not duplicate or pollute the
   database.
3. Put abnormal files into explicit states instead of silently skipping them.

### Phase 3：重复文件检测 专项验证与异常场景

1. Validate same-file/same-hash, same-name/different-hash, same-hash/
   different-path, repeated batch import, and version-conflict cases.
2. Validate repeated import does not create duplicate document, chunk, or job
   records.
3. Validate original-material hash stability and no mutation.

### Phase 4：重复文件检测交付证据、回滚与中文反馈

1. Deliver duplicate detection examples and original-file protection proof.
2. Record conflicts, duplicates, unsupported inputs, and owner-facing
   interpretation.
3. Provide rollback steps that never delete original materials.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Duplicate detection failure states, stop conditions, audit records, and
  rollback paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, open, dump,
  hash, copy, or mutate original source materials or
  `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action creates unbounded duplicate ledgers, manifests, evidence ledgers,
  audit logs, indexes, embeddings, OCR outputs, runtime databases, backup
  payloads, or generated reports.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, and batch-gated.

## Rollback

Rollback STAGE-015 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, delivered reports, STAGE-012 identity
evidence, STAGE-013 fingerprint evidence, or STAGE-014 manifest evidence.
