# IDS v0.1 STAGE-006 Entry Contract

## Identity

- Stage: `STAGE-006`
- Local code: `D02-S001`
- Title: `macOS M2 Max Docker 基线`
- Version: `v0.1`
- Domain: `D02 · 本地运行环境与存储根目录`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-006`
- Parallel: `是`
- Parallel note: `可与 STAGE-001~005 的仓库治理并行；至少在 STAGE-030 前完成。`
- Estimated time: `4-12 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-006_macOSM2MaxDocker基线.md`
- P0 stage file SHA-256:
  `00486235919499e8b0d9a17cc6241167779738bc5fb832d1fad9e547e32acafb`

## Pursuing Goal

建立 macOS + M2 Max + Docker Desktop / Docker Compose 的 IDS v0.1 运行基线。

## Required Reads For STAGE-006

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-006_macOSM2MaxDocker基线.md`

## Baseline Boundary

STAGE-006 establishes the local operating-environment contract for later IDS
runtime, storage-root, and worker stages. It does not ingest real materials and
does not certify production readiness.

The baseline separates three storage responsibilities:

- local hot data: code, configuration, small fixtures, service metadata, and
  bounded runtime state needed for local development and validation;
- external cold data: `IDS_DATA_ROOT` on a 5TB external drive, not committed to
  Git and treated as read-only unless a later stage explicitly authorizes a
  write path;
- GitHub metadata: code, schemas, manifest templates, governance contracts,
  small fixtures, and evidence documents only.

The Stage must preserve the root-lock policies:

- `IDS_DATA_ROOT` is not stored in GitHub;
- original raw data is read-only by default;
- GitHub stores metadata and small fixtures only;
- external API access remains denied unless a later stage explicitly changes
  policy.

## Phase Boundary

STAGE-006 must be split into phase-limited runs. Do not implement all of
STAGE-006 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm the macOS, Docker, `IDS_DATA_ROOT`, internal disk, and external disk
   boundaries.
2. Define the split between local hot data, external-drive cold data, and
   GitHub metadata.
3. Confirm pause, resume, and safe-mode rules when the external drive is
   removable or offline.

### Phase 2：实现、接入与最小可运行切片

1. Implement or record the minimum environment, path-detection, state-enum, and
   storage-budget interfaces.
2. Keep machine-side details in the IDS operations entrance, not the customer
   operator flow.
3. Add the minimum runnable checks for path, free space, waterline, and offline
   state.

### Phase 3：macOS M2 Max Docker 基线专项验证与异常场景

1. Test external drive online, offline, reconnected, permission-error, and
   path-change scenarios.
2. Verify the internal disk is protected from unbounded large derived files.
3. Verify safe mode pauses bulk import, OCR, and Embedding work.

### Phase 4：macOS M2 Max Docker 基线交付证据、回滚与中文反馈

1. Record environment-check, path-check, and storage-budget evidence.
2. Record recoverable and non-recoverable states.
3. Deliver rollback steps and default configuration notes.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Failure states, stop conditions, audit records, and rollback paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- Any command may delete, move, overwrite, or mutate original source materials.
- Any action writes large files to the internal disk without a defined budget.
- Any action writes to an external `IDS_DATA_ROOT` without owner authorization.
- Docker, Compose, path, storage, or permission validation fails for an unknown
  reason.
- Schema migration, data migration, or runtime state creation cannot be rolled
  back.
- The run tries to implement more than the selected phase.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-006 code, schema, configuration, UI, or document changes from
the selected phase only. Do not alter original materials, manifests, evidence
ledgers, audit logs, delivered reports, STAGE-001 naming evidence, STAGE-002
ProductMetaDatabase evidence, STAGE-003 FinanceMetaDatabase evidence,
STAGE-004 legacy-name scan evidence, or STAGE-005 governance-regression
evidence.
