# IDS v0.1 STAGE-007 Entry Contract

## Identity

- Stage: `STAGE-007`
- Local code: `D02-S002`
- Title: `IDS_DATA_ROOT 检测`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-007`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-007_IDS_DATA_ROOT检测.md`
- P0 stage file SHA-256:
  `1bdbb53699df9dffd53c88d74ac6ec1385852a4bebccdb0e780cc47f537bd458`

## Pursuing Goal

识别移动硬盘中的 `IDS_DATA_ROOT`，并验证 `00-99` 目录结构完整。

## Required Reads For STAGE-007

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-007_IDS_DATA_ROOT检测.md`
9. STAGE-006 environment baseline evidence, because STAGE-007 builds on the
   read-only `IDS_DATA_ROOT` state model and safe-mode rules.

## Baseline Boundary

STAGE-007 narrows the STAGE-006 environment baseline into a storage-root
detection contract. It must identify whether `IDS_DATA_ROOT` is explicitly
configured, present, readable, and structurally valid before any import,
parse, OCR, Embedding, indexing, cleanup, or report batch may touch external
materials.

The Stage does not certify production readiness, does not create the root, and
does not scan file contents. It validates the top-level root structure only.

The Stage preserves the root-lock policies:

- `IDS_DATA_ROOT` is a 5TB external-drive root and is not stored in GitHub.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- GitHub stores code, schemas, manifest templates, governance contracts, small
  fixtures, and evidence documents only.
- External API policy remains `denied` unless a later stage explicitly changes
  it.

## Phase Boundary

STAGE-007 must be split into phase-limited runs. Do not implement all of
STAGE-007 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm macOS, Docker, `IDS_DATA_ROOT`, internal disk, and external disk
   boundaries for this storage-root detector.
2. Define the split between local hot data, external-drive cold data, and
   GitHub metadata.
3. Confirm pause, resume, and safe-mode rules when the external drive is
   removable or offline.
4. Define what `00-99` directory structure completeness means for Phase 2.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum read-only `IDS_DATA_ROOT` detection and
   structure-validation interface.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add the minimum runnable checks for configured path, root readability,
   numeric slot completeness, missing slot, duplicate slot, and raw-data
   protection state.

### Phase 3：IDS_DATA_ROOT 检测专项验证与异常场景

1. Test external drive online, offline, reconnected, permission-error, path
   change, missing numeric slots, duplicate numeric slots, and invalid raw-data
   root scenarios.
2. Verify internal disk protection still blocks unbounded derived output.
3. Verify safe mode pauses bulk import, OCR, Embedding, indexing, and cleanup.

### Phase 4：IDS_DATA_ROOT 检测交付证据、回滚与中文反馈

1. Record environment-check, path-check, and directory-structure validation
   evidence.
2. Record recoverable and non-recoverable states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- `IDS_DATA_ROOT` failure states, stop conditions, audit records, and rollback
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
- Any action writes large files to the internal disk without a defined budget.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-007 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, manifests, evidence
ledgers, audit logs, delivered reports, STAGE-001 naming evidence, STAGE-002
ProductMetaDatabase evidence, STAGE-003 FinanceMetaDatabase evidence,
STAGE-004 legacy-name scan evidence, STAGE-005 governance-regression evidence,
or STAGE-006 environment-baseline evidence.
