# IDS v0.1 STAGE-018 Entry Contract

## Identity

- Stage: `STAGE-018`
- Local code: `D04-S001`
- Title: `导入预检扫描器`
- Version: `v0.1`
- Domain: `D04 · 导入预检与数据优先级`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-018`
- Parallel: `是`
- Parallel note: `可与 STAGE-024 的压缩包威胁模型、STAGE-152 的黄金测试集准备并行；至少在 STAGE-037 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-018_导入预检扫描器.md`
- P0 taskpack zip SHA-256:
  `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- P0 stage file SHA-256:
  `30ff34c2ac598a1b8a69d719af2781dbe4fa4b2314957ba2715c434f9a499ba8`

## Pursuing Goal

批量导入前估算文件数量、体积、格式、压缩包、扫描件和处理工作量。

## Required Reads For STAGE-018

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-018_导入预检扫描器.md`
9. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because
   `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
   database source and fake IDS data is forbidden.
10. STAGE-012 through STAGE-017 evidence, because import preflight must inherit
    original-material read-only identity, fingerprint, manifest, duplicate,
    import-idempotency, and regression-test boundaries.

## Stage Boundary

STAGE-018 defines and later implements the import preflight scanner. The stage
exists before actual batch import, parsing, OCR, Embedding, indexing, or report
generation. Its purpose is to estimate the shape and effort of a proposed
import so a human owner can decide whether to continue, split, postpone, skip,
or cancel.

The stage must preserve these rules:

- preflight may only use user-approved input roots or explicit file sets;
- Phase 1 defines metadata fields and states only, with no scanner
  implementation;
- future preflight must read only safe filesystem metadata and source identity
  facts needed for counts, size, format class, archive indicators, scanned-file
  indicators, and workload estimates;
- preflight must not parse document body text, OCR image content, create
  embeddings, build indexes, write manifests, write databases, create
  document/chunk/job rows, generate reports, or start actual import;
- preflight output must separate risk items, cost items, priority suggestions,
  and owner confirmation status;
- no batch processing may start until an explicit owner confirmation state is
  present;
- original files, raw metadata roots, manifests, evidence ledgers, audit logs,
  indexes, delivered reports, and prior Stage evidence remain untouched.

## Phase Boundary

STAGE-018 must be split into phase-limited runs. Do not implement all of
STAGE-018 in one run.

### Phase 1：范围、输入输出与边界确认

1. Define import preflight input directory, output summary, risk items, cost
   items, and confirmation states.
2. Confirm preflight reads metadata only, does not parse body text, and does
   not modify original files.
3. Define that batch processing starts only after owner confirmation.

### Phase 2：实现、接入与最小可运行切片

1. Implement file count, format, size, archive, scanned-document, estimated OCR
   work, and estimated Embedding work calculation.
2. Output risk, cost, and priority recommendations.
3. Display the preflight result in the human product entrance.

### Phase 3：导入预检扫描器 专项验证与异常场景

1. Validate empty directory, small directory, large directory, disconnected
   removable drive, archive candidate, and insufficient space examples.
2. Validate preflight result can be saved, canceled, split into batches, and
   skip high-risk files.
3. Validate preflight does not start parsing, OCR, Embedding, indexing, or
   actual import.

### Phase 4：导入预检扫描器 交付证据、回滚与中文反馈

1. Deliver preflight report examples, risk list, and owner confirmation flow
   evidence.
2. Record uncertainty in preflight estimates.
3. Deliver failure explanations and rollback steps.

## Acceptance Summary

- The import preflight scanner capability is runnable, or an executable,
  testable, and rollback-safe engineering contract exists.
- Input, output, risk, cost, priority, confirmation, failure, audit, stop, and
  rollback states are clear.
- Original materials, manifests, evidence ledgers, audit logs, indexes,
  delivered reports, and raw metadata boundaries are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively beyond the
  selected future preflight root, parse body text, OCR, embed, index, import,
  or mutate original source materials.
- Any command may read, list, open, dump, hash, copy, move, delete, modify, or
  scan `/Users/linzezhang/Downloads/IDS_MetaData` content.
- Any action creates unbounded manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  generated reports, document rows, chunk rows, job rows, import rows,
  duplicate ledgers, or scanner output.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, placeholder corpora, or fabricated evidence.
- A schema, persistence, or UI change cannot be rolled back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed,
  repaired, app entries are reinstalled, and the batch gate allows upload.

## Rollback

Rollback STAGE-018 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials,
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, indexes, delivered reports, or
STAGE-012 through STAGE-017 evidence.
