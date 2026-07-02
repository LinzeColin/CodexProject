# IDS v0.1 STAGE-002 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-002`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE002-P1`
- Acceptance ID: `ACC-STAGE-002`
- Stage title: `新建 ProductMetaDatabase`
- Recorded at UTC: `2026-07-02T05:03:30Z`

## Goal

Confirm the engineering boundary for creating `ProductMetaDatabase` before any
schema, database, migration, UI, worker, or runtime implementation is added.

This phase intentionally creates a contract only. It does not create the
metadata database implementation and does not move, copy, index, or summarize
raw materials.

## ProductMetaDatabase Definition

`ProductMetaDatabase` is the IDS v0.1 product metadata control plane. Its
future implementation may contain small Git-trackable contracts for:

- product schema definitions;
- manifest templates;
- governance and taskpack execution rules;
- taskpack-derived stage/input metadata;
- validation fixtures that are explicitly synthetic or tiny.

It must not contain:

- 500GB raw source materials;
- `00_ORIGINAL_RAW_DATA`;
- customer files, proprietary source documents, or owner-only evidence;
- secrets, API keys, database passwords, cloud credentials, or tokens;
- runtime SQLite/log/PDF/report output;
- dependency folders, generated app bundles, or local caches.

## Allowed Future Paths

Phase 2 may create a small repository-managed metadata area if needed. The
preferred future path is:

- `KM_IDSystem/product_meta_database/`

Allowed subareas for a minimal implementation slice:

- `schemas/` for product metadata schemas;
- `manifest_templates/` for manifest templates;
- `governance_rules/` for small deterministic governance rules;
- `taskpack_inputs/` for taskpack-derived metadata contracts;
- `README.md` for the local operator contract.

Backend/frontend integration is out of Phase 1. If a later phase needs code,
it must justify the narrow path before editing:

- `KM_IDSystem/backend/app/...`
- `KM_IDSystem/backend/tests/...`
- `KM_IDSystem/frontend/...`
- `KM_IDSystem/scripts/...`

## Forbidden Paths

The following are forbidden for STAGE-002 Phase 1 and remain forbidden unless a
later phase explicitly authorizes a narrow fixture or generated contract:

- `KM_IDSystem/data/`
- `KM_IDSystem/reports/`
- `KM_IDSystem/outputs/`
- `KM_IDSystem/frontend/node_modules/`
- `KM_IDSystem/.venv/`
- any `00_ORIGINAL_RAW_DATA` path;
- any external-drive raw data root;
- unrelated CodexProject directories such as Alpha, PFI, EEI, KMFA, Memory
  Atlas, Serenity, or historical finance metadata project checkouts covered
  by STAGE-003 `FinanceMetaDatabase` migration.

## Affected File Groups

Phase 1 may update only governance and durable planning artifacts:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- rendered Chinese entry files generated from governance:
  - `KM_IDSystem/功能清单.md`
  - `KM_IDSystem/开发记录.md`
  - `KM_IDSystem/模型参数文件.md`

Phase 1 must not modify active runtime code, app bundle assets, local services,
sample data, backend API behavior, model router behavior, or frontend UI.

## Inputs And Outputs

Inputs:

- P0 taskpack stage file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-002_新建ProductMetaDatabase.md`
- local stage execution index:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
- root lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
- current batch upload lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`

Outputs:

- a Stage 002 entry contract;
- this Phase 1 scope boundary;
- roadmap/batch-lock/event updates showing only Phase 1 completion;
- rendered Chinese owner entry updates after canonical render.

## Legacy Name Policy

New ProductMetaDatabase surfaces must use `IDS / Industrial Data System` and
`ProductMetaDatabase` as the active product/subsystem names.

Legacy names such as `Wuhan Kaiming OpMe`, `OpMe`, `OpMe_System`,
`opme-system`, or the old Chinese display name may remain only in migration
notes, historical evidence, compatibility identifiers, rollback instructions,
or explicit legacy asset paths. They must not be introduced as new UI, report,
schema, manifest, or formal document display names.

## Future Phase 2 Minimum Slice

Phase 2 should prefer a tiny, static, Git-trackable metadata skeleton over a
runtime database. A valid Phase 2 slice can be limited to:

- directory and README for `KM_IDSystem/product_meta_database/`;
- a minimal product metadata schema;
- a minimal manifest template;
- one deterministic validation script or test that proves the contract can be
  parsed without raw data or secrets.

Do not introduce schema migration, PostgreSQL, long-running workers, file
ingestion, external APIs, or UI routes in Phase 2 unless the implementation
contract is revised by a later phase.

## Validation Plan

Phase 1 validation is evidence-based and does not start services:

- confirm this boundary file and the entry contract exist;
- confirm roadmap and batch lock point to `IDS-STAGE002-P1`;
- parse `events.jsonl`;
- run `check-render --project KM_IDSystem`;
- verify changed scope remains under `KM_IDSystem/` and excludes runtime output
  and dependency directories;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects to satisfy it.

## Validation Evidence

Fresh local validation for this phase recorded:

- Stage 002 taskpack SHA-256 check: `stage002_taskpack_sha_ok`;
- marker and JSONL check: `stage002_phase1_marker_jsonl_ok events=14`;
- `check-render --project KM_IDSystem`: `drift_count=0`;
- changed-scope and `git diff --check`: `changed_scope_ok`;
- no `KM_IDSystem/product_meta_database/` implementation directory was created
  during Phase 1;
- full semantic governance validate remains blocked by the known sparse
  worktree omissions: 28 errors for missing root governance schemas,
  workflows/hooks, governance tests, skill/config files, and unrelated
  registered project directories.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE002-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, report cleanup, service restart, or dependency restoration.

## Decision

STAGE-002 Phase 1 is allowed to complete when this contract, the entry
contract, roadmap, batch lock, event log, and rendered Chinese entries are in
sync. The next run may enter STAGE-002 Phase 2, but the `STAGE-001..010` batch
still must not be pushed until all 10 stages are complete, reviewed, and
repaired.
