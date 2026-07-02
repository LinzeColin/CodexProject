# IDS v0.1 STAGE-019 Entry Contract

## Identity

- Stage: `STAGE-019`
- Current Phase 1 Task ID: `IDS-V0_1-STAGE019-P1`
- Local code: `D04-S002`
- Title: `导入风险估算器`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-019`
- Parallel: `是`
- Parallel note: `可与 STAGE-024 的压缩包威胁模型、STAGE-152 的黄金测试集准备并行；至少在 STAGE-037 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-019_导入风险估算器.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `3b5d8fe9c7b542ea1264f2a8a53b4709fa9dcc73fe8eefed4ce1fe4849a39087`

## Pursuing Goal

识别高风险文件、超大文件、可疑压缩包、未知格式和空间不足风险。

## Required Reads For STAGE-019

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-019_导入风险估算器.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 through STAGE-018 evidence, because the risk estimator must
    inherit original-material read-only identity, fingerprint, manifest,
    duplicate, import-idempotency, regression, and preflight boundaries.

## Stage Boundary

STAGE-019 defines and later implements the import risk estimator. It sits after
the metadata-only STAGE-018 preflight scanner and before any owner-approved
batch processing. Its job is to classify proposed import candidates by risk,
cost, and owner decision needs, not to parse, transform, persist, or ingest
them.

The stage must preserve these rules:

- risk estimation may only consume owner-approved metadata summaries or
  explicit future file metadata; Phase 1 does not read source directories;
- Phase 1 defines fields and states only, with no estimator implementation;
- future estimates must identify high-risk files, oversized files, suspicious
  archives, unknown formats, and insufficient-space risk from safe metadata;
- future estimates must separate risk items, cost items, priority suggestions,
  uncertainty, and confirmation status;
- risk estimation must not parse document body text, OCR image content, create
  embeddings, build indexes, write manifests, write databases, create
  document/chunk/job rows, generate reports, or start actual import;
- owner 确认后才进入批量处理; without explicit owner confirmation the only
  allowed next actions are cancel, split batch, skip high-risk candidates, or
  review later;
- original files, raw metadata roots, manifests, evidence ledgers, audit logs,
  indexes, delivered reports, and prior Stage evidence remain untouched.

## Phase Boundary

STAGE-019 must be split into phase-limited runs. Do not implement all of
STAGE-019 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define import-risk-estimator input directory or metadata inputs, output
   summary, risk items, cost items, and confirmation states.
2. Confirm the estimator reads metadata only, does not parse body text, and
   does not modify original files.
3. Define that batch processing starts only after owner confirmation.

### Phase 2：实现、接入与最小可运行切片

1. Implement estimates for file count, format, size, archive candidates,
   scanned-document candidates, expected OCR workload, and expected Embedding
   workload as risk-estimator inputs.
2. Output risk, cost, and priority recommendations.
3. Display the risk-estimator result in the human product entrance.

### Phase 3：导入风险估算器 专项验证与异常场景

1. Validate empty directory, small directory, large directory, disconnected
   removable drive, archive candidate, and insufficient-space examples.
2. Validate result can be saved, canceled, split into batches, and skip
   high-risk files.
3. Validate risk estimation does not start parsing, OCR, Embedding, indexing,
   or actual import.

### Phase 4：导入风险估算器 交付证据、回滚与中文反馈

1. Deliver report examples, risk list, and owner confirmation flow evidence.
2. Record uncertainty in risk estimates.
3. Deliver failure explanations and rollback steps.

## Acceptance Summary

- The import risk estimator capability is runnable, or an executable,
  testable, and rollback-safe engineering contract exists.
- Input, output, risk, cost, priority, confirmation, failure, audit, stop, and
  rollback states are clear.
- Original materials, manifests, evidence ledgers, audit logs, indexes,
  delivered reports, and raw metadata boundaries are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively beyond the
  selected future approved root, parse body text, OCR, embed, index, import, or
  mutate original source materials.
- Any command may read, list, hash, open, copy, move, delete, modify, dump, or
  scan `/Users/linzezhang/Downloads/IDS_MetaData` content.
- Any action creates unbounded manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  generated reports, document rows, chunk rows, job rows, import rows, or
  estimator output files.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema, persistence, or UI change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, app entries are reinstalled, and the batch gate allows upload.

## Rollback

Rollback STAGE-019 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, existing manifests, evidence
ledgers, audit logs, indexes, delivered reports, runtime data, app entries,
GitHub state, or STAGE-012 through STAGE-018 evidence.
