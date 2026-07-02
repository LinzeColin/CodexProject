# IDS v0.1 STAGE-003 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-003`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE003-P1`
- Acceptance ID: `ACC-STAGE-003`
- Stage title: `MetaDatabase 更名为 FinanceMetaDatabase`
- Recorded at UTC: `2026-07-02T05:38:34Z`

## Goal

Confirm the boundary for renaming standalone historical `MetaDatabase`
references to `FinanceMetaDatabase` before any implementation, file rename,
schema update, UI change, or runtime integration is performed.

This phase intentionally creates a contract only. It does not perform the
rename implementation and does not modify ProductMetaDatabase artifacts.

## Target Definition

The STAGE-003 target is a standalone legacy subsystem name:

- old name: `MetaDatabase`
- new name: `FinanceMetaDatabase`

The target is not:

- `ProductMetaDatabase`;
- `product_meta_database/`;
- STAGE-002 product metadata contracts;
- a historical external project checkout;
- a raw-material store or external-drive mirror.

`ProductMetaDatabase` remains the accepted STAGE-002 IDS product metadata
control plane. Phase 2 must preserve that name unless a later explicit owner
decision changes the STAGE-002 acceptance contract.

## Baseline Reference Scan

Before creating STAGE-003 Phase 1 artifacts, Phase 1 scanned `KM_IDSystem/`
only, excluding runtime output, dependency, and cache folders. The precise
standalone scan found:

| Metric | Result |
|---|---:|
| standalone `MetaDatabase` or `FinanceMetaDatabase` hits | 5 |
| `ProductMetaDatabase` substring hits | 109 |
| active backend/frontend/script target hits | 0 |

The standalone hits are limited to:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.json`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE1_SCOPE_BOUNDARY.md`

These are planning, migration, or boundary references, not active runtime
identifiers. Phase 2 may update or annotate the STAGE-002 migration references
only if it preserves their historical meaning.

## Allowed Future Paths

Phase 2 may update only the narrow files that actually contain standalone
target references or durable migration context:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_*`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- rendered Chinese owner entries generated from governance:
  - `KM_IDSystem/功能清单.md`
  - `KM_IDSystem/开发记录.md`
  - `KM_IDSystem/模型参数文件.md`

If Phase 2 finds active standalone `MetaDatabase` references in runtime code,
it may propose a smaller implementation contract before editing:

- `KM_IDSystem/backend/...`
- `KM_IDSystem/frontend/...`
- `KM_IDSystem/scripts/...`
- `KM_IDSystem/app_bundle/...`

Phase 2 must not edit those runtime paths merely because `ProductMetaDatabase`
contains the substring `MetaDatabase`.

## Forbidden Paths

The following remain forbidden for STAGE-003 unless a later phase explicitly
authorizes a narrow fixture or generated contract:

- `KM_IDSystem/data/`
- `KM_IDSystem/reports/`
- `KM_IDSystem/outputs/`
- `KM_IDSystem/frontend/node_modules/`
- `KM_IDSystem/.venv/`
- `KM_IDSystem/product_meta_database/` when the only reason is the
  `ProductMetaDatabase` substring;
- any `00_ORIGINAL_RAW_DATA` path;
- any external-drive raw data root;
- unrelated CodexProject directories such as Alpha, PFI, EEI, KMFA, Memory
  Atlas, Serenity, or historical `MetaDatabase` project checkouts.

## Inputs And Outputs

Inputs:

- P0 taskpack stage file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-003_MetaDatabase更名为FinanceMetaDatabase.md`
- local stage execution index:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
- root lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
- current batch upload lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`

Outputs:

- a Stage 003 entry contract;
- this Phase 1 scope boundary;
- roadmap/batch-lock/event updates showing only Phase 1 completion;
- rendered Chinese owner entry updates after canonical render.

## Legacy Name Policy

New formal references should use `FinanceMetaDatabase` for the renamed finance
metadata subsystem.

Standalone `MetaDatabase` may remain only in migration notes, historical
evidence, taskpack source references, rollback instructions, or explicit legacy
alias explanations. `ProductMetaDatabase` is not a legacy alias and remains an
active STAGE-002 subsystem name.

## Future Phase 2 Minimum Slice

Phase 2 should prefer a narrow text/reference migration over runtime changes.
A valid Phase 2 slice can be limited to:

- updating STAGE-002 migration wording so it points to STAGE-003 as the
  FinanceMetaDatabase rename authority;
- adding a small migration note if needed;
- adding a focused scan/contract check that distinguishes standalone
  `MetaDatabase` from `ProductMetaDatabase`;
- updating roadmap/events/batch lock and rendered Chinese entries.

Do not introduce schema migration, database creation, long-running workers,
file ingestion, external APIs, UI routes, or raw-data movement in Phase 2 unless
the implementation contract is revised by a later phase.

## Validation Plan

Phase 1 validation is evidence-based and does not start services:

- confirm this boundary file and the entry contract exist;
- confirm the P0 STAGE-003 taskpack SHA-256;
- confirm roadmap and batch lock point to `IDS-STAGE003-P1`;
- parse `events.jsonl`;
- run `check-render --project KM_IDSystem`;
- verify changed scope remains under `KM_IDSystem/` and excludes runtime output,
  dependency directories, raw materials, and `product_meta_database/` edits;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects to satisfy it.

## Validation Evidence

Fresh local validation for this phase recorded:

- P0 taskpack SHA-256 check: `stage003_taskpack_sha_ok=True`;
- `check-render --project KM_IDSystem`: `drift_count=0`;
- marker, JSONL, and scope check:
  `stage003_phase1_marker_jsonl_scope_ok=True`;
- events JSONL parse: 18 events parsed;
- post-artifact standalone `MetaDatabase`/`FinanceMetaDatabase` hits: 67;
- post-artifact `ProductMetaDatabase` substring hits: 151;
- changed-scope check: only `KM_IDSystem/` paths changed, with no runtime,
  reports, outputs, dependency, raw-data, or `product_meta_database/` edits;
- `git diff --check`: exit 0;
- full semantic governance validate remains blocked by the known sparse
  worktree omissions: 28 errors for missing root governance schemas,
  workflows/hooks, governance tests, skill/config files, and unrelated
  registered project directories.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE003-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, report cleanup, service restart, dependency restoration, or
ProductMetaDatabase changes.

## Decision

STAGE-003 Phase 1 is allowed to complete when this contract, the entry
contract, roadmap, batch lock, event log, and rendered Chinese entries are in
sync. The next run may enter STAGE-003 Phase 2, but the `STAGE-001..010` batch
still must not be pushed until all 10 stages are complete, reviewed, and
repaired.
