# IDS v0.1 STAGE-012 Entry Contract

## Identity

- Stage: `STAGE-012`
- Local code: `D03-S001`
- Title: `原始资料只读合同`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-012`
- Parallel: `否`
- Parallel note: `本 Stage 涉及共享契约、状态机、数据库、索引、证据、报告或执行规则，建议单独完成后再进入下游。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-012_原始资料只读合同.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `44da923322e01a69b4050b7aa3f2596994e11124cda51e4a470832c472174dc8`

## Pursuing Goal

确保 `00_ORIGINAL_RAW_DATA` 内原始文件默认不移动、不删除、不覆盖。

## Required Reads For STAGE-012

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-012_原始资料只读合同.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-010 local path contract evidence, because `source_uri`,
    processed path, backup path, manifest path, and report export path must
    remain separated before original-material identity work starts.
11. STAGE-011 safe-mode evidence, because every raw-material read-only or
    manifest workflow must fail closed before side effects.

## Stage Boundary

STAGE-012 defines the original-material protection and file-identity contract
that later phases may implement. It does not grant permission to read, list,
open, hash, copy, move, delete, rewrite, or normalize real original materials
or `/Users/linzezhang/Downloads/IDS_MetaData` content.

The stage preserves these root-lock policies:

- `00_ORIGINAL_RAW_DATA` is a source-of-truth raw-material area. Default
  behavior is read-only and non-mutating.
- Original files must not be moved, deleted, overwritten, normalized,
  renamed, compacted, de-duplicated in place, or repaired by Codex.
- File identity metadata may include `source_uri`, `sha256`, `file_size`,
  `mtime`, and `first_seen_at` only when a later authorized phase explicitly
  performs a read-only scan over user-approved real data or a tiny structural
  fixture that is not presented as business data.
- Manifests must store metadata and evidence pointers, not raw payloads,
  secrets, local database dumps, or fabricated rows.
- Duplicate detection must be idempotent. Repeating a scan must not create
  duplicate documents, chunks, jobs, manifests, or audit facts.
- Fake IDS business data, fake database rows, fake source documents, and
  fabricated evidence remain forbidden.

## Phase Boundary

STAGE-012 must be split into phase-limited runs. Do not implement all of
STAGE-012 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, and duplicate-recognition rules.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`
   fields.

### Phase 2：实现、接入与最小可运行切片

1. Implement the minimum read-only file scan, fingerprint generation, manifest
   record, or duplicate detection slice.
2. Ensure repeated scans do not duplicate or pollute persistence.
3. Put abnormal files into explicit states instead of silently skipping them.

### Phase 3：原始资料只读合同专项验证与异常场景

1. Validate same file and same hash, same name and different hash, same hash
   and different path.
2. Validate repeated import does not create duplicate document, chunk, or job
   records.
3. Validate original-material hash stability and no mutation.

### Phase 4：原始资料只读合同交付证据、回滚与中文反馈

1. Deliver manifest examples, duplicate detection reports, and original-file
   protection proof.
2. Record conflicts, duplicates, and unsupported files found.
3. Provide rollback steps that never delete original materials.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Original-material failure states, stop conditions, audit records, and
  rollback paths are clear.
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
  documents, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, and batch-gated.

## Rollback

Rollback STAGE-012 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, manifests,
evidence ledgers, audit logs, delivered reports, STAGE-010 path-contract
evidence, or STAGE-011 safe-mode evidence.
