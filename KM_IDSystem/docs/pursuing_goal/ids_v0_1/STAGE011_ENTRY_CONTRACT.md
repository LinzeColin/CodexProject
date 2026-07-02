# IDS v0.1 STAGE-011 Entry Contract

## Identity

- Stage: `STAGE-011`
- Local code: `D02-S006`
- Title: `安全模式基线`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-011`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `6-14 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-011_安全模式基线.md`
- P0 stage file SHA-256:
  `b4e568ee400a1bcfaa36d51123800fa1dd2d77cb5c24363a01765318b2300473`

## Pursuing Goal

当磁盘不足、移动硬盘离线、索引失败或外部 API 超预算时进入安全模式。

## Required Reads For STAGE-011

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH011_020_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-011_安全模式基线.md`
9. STAGE-006 environment baseline evidence, because safe mode starts from
   local platform, Docker, `IDS_DATA_ROOT`, and internal storage state.
10. STAGE-007 `IDS_DATA_ROOT` detector evidence, because safe mode must not
    create, repair, or recursively scan the external root.
11. STAGE-008 removable-drive state evidence, because safe mode must remain
    paused when the drive is offline, reconnected, path-changed, permission
    denied, or structurally invalid.
12. STAGE-009 storage-budget evidence, because low free space and unbounded
    output risk must block derived jobs before files are generated.
13. STAGE-010 local path contract evidence, because safe mode must respect
    source URI, processed, backup, manifest, and report export boundaries.
14. `IDS_METADATA_RAW_DATA_BOUNDARY.md`, because `/Users/linzezhang/Downloads/IDS_MetaData`
    is a read-only real metadata database source and fake IDS data is
    forbidden.

## Baseline Boundary

STAGE-011 defines when IDS enters safe mode and which workflows pause before
they can move data, generate derived artifacts, call external APIs, or resume
after a transient local-state change.

The stage preserves these root-lock policies:

- `IDS_DATA_ROOT` is an external cold-data root and is not stored in GitHub.
- `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only real metadata
  database source; this stage may reference the path but must not read, scan,
  dump, copy, modify, move, or delete raw database content.
- IDS business data, database-backed content, analytics inputs, reports,
  indexes, manifests, and committed examples must use real user-approved data.
  Fake business data, fake database rows, fake source documents, and fabricated
  evidence are forbidden.
- GitHub stores code, schemas, manifest templates, governance contracts, small
  fixtures, and evidence documents only.
- Local runtime data, generated reports, derived outputs, indexes, OCR output,
  embeddings, and backup payloads stay outside Git unless a later stage
  explicitly approves a small sanitized fixture.

## Phase Boundary

STAGE-011 must be split into phase-limited runs. Do not implement all of
STAGE-011 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm macOS, Docker, `IDS_DATA_ROOT`, internal disk, removable-drive, and
   read-only metadata-root boundaries.
2. Define the responsibility split between local hot data, external cold data,
   GitHub metadata, raw metadata, and safe-mode state.
3. Confirm pause, recovery, resume, and safe-mode rules before implementing
   any safe-mode interface.
4. Define the safe-mode state contract that Phase 2 may implement.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum read-only safe-mode baseline interface.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add minimum runnable checks for path, storage, waterline, offline,
   indexing, and external-API budget states.

### Phase 3：安全模式基线专项验证与异常场景

1. Test removable-drive online, offline, reconnected, permission-denied, and
   path-changed scenarios.
2. Verify internal disk protection blocks unbounded derived artifacts.
3. Verify safe mode pauses bulk import, OCR, Embedding, indexing, cleanup,
   backup, manifest, report export, and external API work.

### Phase 4：安全模式基线交付证据、回滚与中文反馈

1. Record environment-check, path-check, storage-budget, safe-mode, and
   external-API-budget evidence.
2. Record recoverable and non-recoverable safe-mode states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Safe-mode failure states, stop conditions, audit records, and rollback paths
  are clear.
- Original materials, raw metadata, manifests, evidence ledgers, audit logs,
  and delivered reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, open, dump,
  or mutate original source materials or `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action creates unbounded reports, indexes, embeddings, OCR outputs,
  caches, backup payloads, manifests, runtime files, or generated data.
- Any action uses fake IDS business data, fake database rows, fake source
  documents, or fabricated evidence.
- Any action resumes data-moving work after a path, storage, indexing, or API
  budget block without explicit revalidation.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-011..020 are complete, reviewed, repaired,
  and batch-gated.

## Rollback

Rollback STAGE-011 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, `/Users/linzezhang/Downloads/IDS_MetaData`,
manifests, evidence ledgers, audit logs, delivered reports, STAGE-006
environment evidence, STAGE-007 `IDS_DATA_ROOT` detector evidence, STAGE-008
removable-drive evidence, STAGE-009 storage-budget evidence, or STAGE-010
local path contract evidence.
