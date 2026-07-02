# IDS v0.1 STAGE-014 Entry Contract

## Identity

- Stage: `STAGE-014`
- Local code: `D03-S003`
- Title: `Manifest 生成`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-014`
- Parallel: `否`
- Parallel note: `本 Stage 涉及共享契约、状态机、数据库、索引、证据、报告或执行规则，建议单独完成后再进入下游。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-014_Manifest生成.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `ede58960f10bc0b4537f222ca93859ed0c32060be44ade4ce105525bbe7392ad`

## Pursuing Goal

生成可重建、可审计、可对比的 manifest。

## Required Reads For STAGE-014

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-014_Manifest生成.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 and STAGE-013 evidence, because Manifest generation must inherit
    original-material read-only identity, file-fingerprint, duplicate, conflict,
    and no-mutation rules.

## Stage Boundary

STAGE-014 defines and later implements a manifest generation path. The manifest
is a metadata record that can be rebuilt, audited, and compared; it is not a
copy of raw source payload content.

This entry contract does not grant permission to read, list, open, hash, copy,
move, delete, rewrite, normalize, recursively scan, or dump real original
materials or `/Users/linzezhang/Downloads/IDS_MetaData` content.

Manifest generation must preserve these rules:

- original files remain read-only and are never moved, deleted, overwritten, or
  deduplicated in place;
- `source_uri` must identify a future user-approved explicit source, not a
  guessed or recursively discovered path;
- `sha256` must be inherited from a bounded read-only fingerprint operation;
- `file_size`, `mtime`, and `first_seen_at` are metadata observed from real
  future evidence, not fabricated fields;
- repeated manifest generation must be idempotent and must not duplicate
  documents, chunks, jobs, evidence facts, audit events, reports, or manifest
  rows;
- same-name/different-hash and same-hash/different-path cases must preserve
  provenance and become explicit duplicate/conflict states.

## Phase Boundary

STAGE-014 must be split into phase-limited runs. Do not implement all of
STAGE-014 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, and duplicate-recognition rules.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`
   fields.

### Phase 2：实现、接入与最小可运行切片

1. Implement a minimum file scanning, fingerprint generation, manifest record,
   or duplicate detection slice.
2. Ensure repeated scans do not duplicate or pollute the database.
3. Put abnormal files into explicit states instead of silently skipping them.

### Phase 3：Manifest 生成 专项验证与异常场景

1. Validate same-file/same-hash, same-name/different-hash, and
   same-hash/different-path cases.
2. Validate repeated import does not create duplicate document, chunk, or job
   records.
3. Validate original-material hash stability and no mutation.

### Phase 4：Manifest 生成交付证据、回滚与中文反馈

1. Deliver manifest examples, duplicate detection reports, and original-file
   protection proof.
2. Record conflicts, duplicates, and unsupported files found.
3. Provide rollback steps that never delete original materials.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Manifest failure states, stop conditions, audit records, and rollback paths
  are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, open, dump,
  hash, copy, or mutate original source materials or
  `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action creates unbounded manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads, or
  generated reports.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, and batch-gated.

## Rollback

Rollback STAGE-014 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, delivered reports, STAGE-012 identity
evidence, STAGE-013 fingerprint evidence, or STAGE-011 safe-mode evidence.
