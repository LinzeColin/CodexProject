# IDS v0.1 STAGE-013 Entry Contract

## Identity

- Stage: `STAGE-013`
- Local code: `D03-S002`
- Title: `文件指纹引擎`
- Version: `v0.1`
- Domain: `D03 · 原始资料保护与文件身份`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-013`
- Parallel: `否`
- Parallel note: `本 Stage 涉及共享契约、状态机、数据库、索引、证据、报告或执行规则，建议单独完成后再进入下游。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-013_文件指纹引擎.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `514e55b51c6031fb9c6eb1c7e14a511334fc00a7f9dfd79c25b53b7e469c9316`

## Pursuing Goal

为每个文件生成 `sha256`、`size`、`mtime`、`extension`、`mime`,
`source_uri`, and `first_seen_at`。

## Required Reads For STAGE-013

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-013_文件指纹引擎.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 original-material read-only contract evidence, because the
    fingerprint engine must inherit source protection, explicit URI,
    idempotency, duplicate handling, and no-mutation rules.

## Stage Boundary

STAGE-013 defines and later implements the file-fingerprint engine that expands
the STAGE-012 identity contract with `extension` and `mime` metadata.

This entry contract does not grant permission to read, list, open, hash, copy,
move, delete, rewrite, normalize, or recursively scan real original materials
or `/Users/linzezhang/Downloads/IDS_MetaData` content.

The fingerprint engine must preserve these rules:

- `source_uri` must identify an explicit local source selected by user-approved
  future logic, not a guessed or recursively discovered path.
- `sha256` must represent exact file bytes only when a later authorized phase
  performs a bounded read-only fingerprint operation.
- `size` and `mtime` are metadata observed at the same fingerprint time.
- `extension` is a normalized metadata field derived from the filename suffix,
  not a trusted content type.
- `mime` is best-effort metadata that may be inferred from extension or a
  future safe detector; Phase 1 defines the contract only.
- `first_seen_at` must be a real UTC observation time from the future
  fingerprint workflow, not fabricated historical evidence.
- Repeated fingerprinting must be idempotent and must not duplicate documents,
  chunks, jobs, manifests, evidence facts, audit events, or reports.

## Phase Boundary

STAGE-013 must be split into phase-limited runs. Do not implement all of
STAGE-013 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define original-material protection, file identity, hash, manifest,
   idempotency, and duplicate-recognition rules for the fingerprint engine.
2. Confirm `00_ORIGINAL_RAW_DATA` defaults to read-only and no-move,
   no-delete, no-overwrite behavior.
3. Define `source_uri`, `sha256`, `size`, `mtime`, `extension`, `mime`, and
   `first_seen_at` fields.

### Phase 2：实现、接入与最小可运行切片

1. Implement a minimum bounded file fingerprinting slice.
2. Ensure repeated scans/fingerprints do not duplicate or pollute persistence.
3. Put abnormal files into explicit states instead of silently skipping them.

### Phase 3：文件指纹引擎专项验证与异常场景

1. Validate same-file/same-hash, same-name/different-hash, and
   same-hash/different-path cases.
2. Validate repeated import does not create duplicate document, chunk, or job
   records.
3. Validate original-material hash stability and no mutation.

### Phase 4：文件指纹引擎交付证据、回滚与中文反馈

1. Deliver manifest examples, duplicate detection reports, and original-file
   protection proof.
2. Record conflicts, duplicates, and unsupported files found.
3. Provide rollback steps that never delete original materials.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- File fingerprint failure states, stop conditions, audit records, and
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
  documents, placeholder corpora, or fabricated evidence.
- A schema or persistence change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, and batch-gated.

## Rollback

Rollback STAGE-013 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, manifests,
evidence ledgers, audit logs, delivered reports, STAGE-012 identity evidence,
or STAGE-011 safe-mode evidence.
