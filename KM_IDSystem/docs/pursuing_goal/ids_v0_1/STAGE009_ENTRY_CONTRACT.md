# IDS v0.1 STAGE-009 Entry Contract

## Identity

- Stage: `STAGE-009`
- Local code: `D02-S004`
- Title: `存储预算基线`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-009`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-009_存储预算基线.md`
- P0 stage file SHA-256:
  `490671d6372dd185fa829ce4a7ea05d25b6ae311feb92a986571cbdb2a567099`

## Pursuing Goal

建立 800GB 内置盘与 5TB 移动硬盘的存储预算，防止任务写满本机。

## Required Reads For STAGE-009

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-009_存储预算基线.md`
9. STAGE-006 environment baseline evidence, because it defines internal
   storage guard defaults and operations-only machine diagnostics.
10. STAGE-007 and STAGE-008 storage/root evidence, because storage budget
    enforcement must not create, scan, or mutate `IDS_DATA_ROOT`.

## Baseline Boundary

STAGE-009 turns the earlier macOS/storage checks into a storage-budget
contract. It must distinguish the local hot-data budget on the internal disk,
the cold raw-material budget on the external 5TB `IDS_DATA_ROOT`, and the small
GitHub metadata/code budget.

The Stage does not certify production readiness, does not start services, does
not create `IDS_DATA_ROOT`, does not scan raw-file contents, and does not
create derived artifacts. It defines the budget and stop rules that later
runtime, worker, report, OCR, Embedding, and index slices may use.

The Stage preserves the root-lock policies:

- `IDS_DATA_ROOT` is a 5TB external-drive root and is not stored in GitHub.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- GitHub stores code, schemas, manifest templates, governance contracts, small
  fixtures, and evidence documents only.
- External API policy remains `denied` unless a later stage explicitly changes
  it.

## Phase Boundary

STAGE-009 must be split into phase-limited runs. Do not implement all of
STAGE-009 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm macOS, Docker, `IDS_DATA_ROOT`, internal disk, external disk, and
   existing storage-guard evidence.
2. Define the split between internal hot data, external-drive cold data, and
   GitHub metadata for storage-budget enforcement.
3. Confirm storage-budget states, waterlines, pause rules, and safe-mode
   behavior before implementing a new budget interface.
4. Define the budget contract that Phase 2 may implement.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum read-only storage-budget interface for
   internal disk, external root, derived outputs, and safe-mode status.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add minimum runnable checks for OK, warning, blocked, unknown, and
   unbounded-output-risk states.

### Phase 3：存储预算基线专项验证与异常场景

1. Test adequate space, warning, low-free-space, high-waterline, and unknown
   storage scenarios.
2. Verify internal disk protection blocks unbounded derived output.
3. Verify safe mode pauses bulk import, OCR, Embedding, indexing, cleanup, and
   batch report generation when the storage budget is blocked.

### Phase 4：存储预算基线交付证据、回滚与中文反馈

1. Record environment-check, path-check, storage-budget, and waterline evidence.
2. Record recoverable and non-recoverable budget states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Storage-budget failure states, stop conditions, audit records, and rollback
  paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, enumerate recursively, or mutate
  original source materials.
- Any action creates a guessed `IDS_DATA_ROOT` or creates missing `00-99`
  directories without owner authorization.
- Any action creates unbounded reports, indexes, embeddings, OCR outputs,
  caches, or runtime files on the internal disk.
- Any action resumes data-moving work after a storage block without explicit
  revalidation.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-009 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, manifests, evidence
ledgers, audit logs, delivered reports, STAGE-006 environment-baseline
evidence, STAGE-007 `IDS_DATA_ROOT` detector evidence, or STAGE-008 removable
drive state-machine evidence.
