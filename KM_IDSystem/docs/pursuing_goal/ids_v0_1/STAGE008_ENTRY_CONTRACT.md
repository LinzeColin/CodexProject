# IDS v0.1 STAGE-008 Entry Contract

## Identity

- Stage: `STAGE-008`
- Local code: `D02-S003`
- Title: `可拔插移动硬盘状态机`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-008`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-008_可拔插移动硬盘状态机.md`
- P0 stage file SHA-256:
  `5cd56ca188c4e13215d08b0281a412c877e3e02209b2c00e4f3ff1c943f2d357`

## Pursuing Goal

处理移动硬盘在线、离线、重新接入、路径变化和权限异常。

## Required Reads For STAGE-008

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-008_可拔插移动硬盘状态机.md`
9. STAGE-006 environment baseline evidence, because it defines external-drive
   online, offline, reconnected, permission-denied, path-changed, and storage
   budget behavior.
10. STAGE-007 `IDS_DATA_ROOT` detector evidence, because the state machine must
    compose removable-drive state with explicit root and `00-99` structure
    validation.

## Baseline Boundary

STAGE-008 turns the STAGE-006 environment baseline and STAGE-007 root detector
into a removable-drive state-machine contract. It must decide whether data
workflows stay paused, can resume after revalidation, or must fail closed when
the external drive is offline, reconnected, path-changed, permission-denied, or
structurally invalid.

The Stage does not certify production readiness, does not start services, does
not create `IDS_DATA_ROOT`, does not repair external-drive directories, and does
not scan raw-file contents. It defines the safe transition rules that later
runtime, worker, and UI slices may implement.

The Stage preserves the root-lock policies:

- `IDS_DATA_ROOT` is a 5TB external-drive root and is not stored in GitHub.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- GitHub stores code, schemas, manifest templates, governance contracts, small
  fixtures, and evidence documents only.
- External API policy remains `denied` unless a later stage explicitly changes
  it.

## Phase Boundary

STAGE-008 must be split into phase-limited runs. Do not implement all of
STAGE-008 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm macOS, Docker, `IDS_DATA_ROOT`, internal disk, and external disk
   boundaries for the removable-drive state machine.
2. Define the split between local hot data, external-drive cold data, and
   GitHub metadata.
3. Confirm pause, resume, and safe-mode rules when the external drive is
   removable, offline, reconnected, path-changed, or permission-denied.
4. Define the state and transition contract that Phase 2 may implement.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum read-only state-machine interface for
   environment, path, root, permission, storage-budget, and safe-mode status.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add the minimum runnable checks for offline, reconnected, path-changed,
   permission-denied, low-space, and high-waterline states.

### Phase 3：可拔插移动硬盘状态机专项验证与异常场景

1. Test online, offline, reconnected, permission-error, and path-change
   transitions.
2. Verify internal disk protection still blocks unbounded derived output.
3. Verify safe mode pauses bulk import, OCR, Embedding, indexing, cleanup, and
   batch report generation.

### Phase 4：可拔插移动硬盘状态机交付证据、回滚与中文反馈

1. Record environment-check, path-check, storage-budget, and state-transition
   evidence.
2. Record recoverable and non-recoverable states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Removable-drive failure states, stop conditions, audit records, and rollback
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
- Any action resumes data-moving work after reconnect without explicit
  revalidation.
- Any action writes large files to the internal disk without a defined budget.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-008 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, manifests, evidence
ledgers, audit logs, delivered reports, STAGE-001 naming evidence, STAGE-006
environment-baseline evidence, or STAGE-007 `IDS_DATA_ROOT` detector evidence.
