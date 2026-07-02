# IDS v0.1 STAGE-016 Entry Contract

## Identity

- Stage: `STAGE-016`
- Local code: `D03-S005`
- Title: `导入幂等键`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-016`
- Parallel: `否`
- Parallel note: `本 Stage 涉及共享契约、状态机、数据库、索引、证据、报告或执行规则，建议单独完成后再进入下游。`
- Estimated time: `6-14 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-016_导入幂等键.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `0abc5ed195217226b96c41ff1064d07dfea01beead173a07ab313d68f4bb28f4`

## Pursuing Goal

确保同一文件或同一批次重复导入不会重复污染 documents/chunks/index。

## Required Reads For STAGE-016

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-016_导入幂等键.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 through STAGE-015 evidence, because import idempotency must
    inherit original-material read-only identity, fingerprint, manifest, and
    duplicate-detection boundaries.

## Stage Boundary

STAGE-016 defines and later implements import idempotency keys. The purpose is
to prevent repeated import attempts from creating duplicate document rows,
chunk rows, indexing jobs, or index entries for the same approved source file
or same approved batch.

Import idempotency must preserve these rules:

- original files remain read-only and are never moved, deleted, overwritten, or
  deduplicated in place;
- idempotency keys must be derived from bounded source identity, fingerprint,
  manifest, and batch evidence, not from raw payload dumps;
- `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at` remain
  required file-identity fields, but a new observation timestamp must not by
  itself create a new document identity for an already-seen file;
- same hash at different paths may share content identity while preserving
  separate provenance;
- same basename with different hashes remains a conflict/version candidate, not
  an overwrite;
- repeated single-file import and repeated batch import must have zero
  document, chunk, job, index, manifest, evidence-ledger, audit-log, and report
  pollution unless a later explicit gate authorizes a controlled update;
- no fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence may be used.

## Phase Boundary

STAGE-016 must be split into phase-limited runs. Do not implement all of
STAGE-016 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, and duplicate-recognition rules.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`
   fields for import-idempotency decisions.

### Phase 2：实现、接入与最小可运行切片

1. Implement a minimum import-idempotency slice on bounded explicit inputs.
2. Ensure repeated scan/import attempts do not duplicate or pollute the
   database, document rows, chunk rows, jobs, or indexes.
3. Put abnormal files into explicit states instead of silently skipping them.

### Phase 3：导入幂等键 专项验证与异常场景

1. Validate same-file/same-hash, same-name/different-hash, same-hash/
   different-path, repeated single-file import, repeated batch import, and
   version-conflict cases.
2. Validate repeated import does not create duplicate document, chunk, or job
   records.
3. Validate original-material hash stability and no mutation.

### Phase 4：导入幂等键 交付证据、回滚与中文反馈

1. Deliver manifest/idempotency-key examples and original-file protection
   proof.
2. Record conflicts, duplicates, unsupported inputs, and owner-facing
   interpretation.
3. Provide rollback steps that never delete original materials.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Import-idempotency failure states, stop conditions, audit records, and
  rollback paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, indexes, and
  delivered reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, open, dump,
  hash, copy, or mutate original source materials or
  `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action creates unbounded manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  generated reports, document rows, chunk rows, or job rows.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, and batch-gated.

## Rollback

Rollback STAGE-016 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, indexes, delivered reports,
STAGE-012 identity evidence, STAGE-013 fingerprint evidence, STAGE-014
manifest evidence, or STAGE-015 duplicate-detection evidence.
