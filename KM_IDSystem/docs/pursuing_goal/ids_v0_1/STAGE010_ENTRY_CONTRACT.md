# IDS v0.1 STAGE-010 Entry Contract

## Identity

- Stage: `STAGE-010`
- Local code: `D02-S005`
- Title: `本地路径合同`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-010`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `6-14 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-010_本地路径合同.md`
- P0 stage file SHA-256:
  `b459c6cac1b79be5a2904308236be2e41356adadfce9bf6a6f5febd27e3fa0a6`

## Pursuing Goal

定义 `file:// source_uri`、`processed path`、`backup path`、`manifest path`
和报告导出路径规范。

## Required Reads For STAGE-010

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-010_本地路径合同.md`
9. STAGE-007 `IDS_DATA_ROOT` detector evidence, because local path contracts
   must not create, repair, or recursively scan the external root.
10. STAGE-008 removable-drive state evidence, because path contracts must stay
    safe when the drive is offline, reconnected, path-changed, permission
    denied, or structurally invalid.
11. STAGE-009 storage-budget evidence, because processed, backup, manifest,
    and report paths must stay bounded and must not fill the internal disk.

## Baseline Boundary

STAGE-010 defines local path roles and their failure boundaries. It does not
copy source materials, create path directories, generate processed outputs,
write manifests, export reports, start services, or scan external-drive
contents.

The Stage preserves the root-lock policies:

- `IDS_DATA_ROOT` is a 5TB external-drive root and is not stored in GitHub.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- `file:// source_uri` is a reference to existing local source material, not a
  command to copy, move, clean, or hash raw files in this stage.
- GitHub stores code, schemas, manifest templates, governance contracts, small
  fixtures, and evidence documents only.
- Local runtime data, generated reports, derived outputs, and backup payloads
  stay outside Git unless a later stage explicitly allows a small fixture or
  redacted evidence file.

## Phase Boundary

STAGE-010 must be split into phase-limited runs. Do not implement all of
STAGE-010 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm macOS, Docker, `IDS_DATA_ROOT`, internal disk, external drive, and
   prior STAGE-007/008/009 evidence.
2. Define the split between source URI, processed path, backup path, manifest
   path, report export path, internal hot data, external cold data, and GitHub
   metadata.
3. Confirm pause, recovery, and safe-mode rules for removable-drive and storage
   budget states before implementing a path-contract interface.
4. Define the path contract that Phase 2 may implement.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum read-only local path contract interface.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add minimum runnable checks for source URI, processed path, backup path,
   manifest path, report export path, storage, waterline, and offline states.

### Phase 3：本地路径合同专项验证与异常场景

1. Test removable-drive online, offline, reconnected, permission-denied, and
   path-changed local path scenarios.
2. Verify internal disk protection blocks unbounded processed, backup,
   manifest, or report-export output.
3. Verify safe mode pauses bulk import, OCR, Embedding, indexing, cleanup, and
   report export work when local path contract prerequisites are blocked.

### Phase 4：本地路径合同交付证据、回滚与中文反馈

1. Record environment-check, path-check, storage-budget, and local path
   contract evidence.
2. Record recoverable and non-recoverable path states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Path-contract failure states, stop conditions, audit records, and rollback
  paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, or mutate
  original source materials.
- Any action creates guessed processed, backup, manifest, report export, or
  `IDS_DATA_ROOT` directories without a later explicit implementation gate.
- Any action creates unbounded reports, indexes, embeddings, OCR outputs,
  caches, backup payloads, or runtime files on the internal disk.
- Any action resumes data-moving work after a path/storage block without
  explicit revalidation.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-010 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, manifests, evidence
ledgers, audit logs, delivered reports, STAGE-007 `IDS_DATA_ROOT` detector
evidence, STAGE-008 removable-drive state-machine evidence, or STAGE-009
storage-budget evidence.
