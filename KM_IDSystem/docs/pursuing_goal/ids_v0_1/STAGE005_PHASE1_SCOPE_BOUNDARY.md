# IDS v0.1 STAGE-005 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-005`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE005-P1`
- Acceptance ID: `ACC-STAGE-005`
- Stage title: `仓库治理回归验证`
- Recorded at UTC: `2026-07-02T06:39:05Z`

## Goal

Confirm the boundary for repository governance regression validation before
adding a validator, changing scripts, modifying runtime code, or starting a
broader scan.

This phase creates a contract only. It does not implement the regression
validator, does not modify runtime code, and does not enter Phase 2.

## Regression Surface

STAGE-005 will check whether STAGE-001 through STAGE-004 left the repository
governance surface coherent and runnable.

| Surface | Tracked files | Phase 1 treatment |
|---|---:|---|
| `README.md` | 1 | Check owner-facing product identity, runbook, validation, rollback, and legacy-alias explanations. |
| `docs/HANDOFF.md` | 1 | Check continuity, delivery standard, GitHub rule, and local untracked-file policy. |
| `docs/governance/` | 16 | Check roadmap, event logs, project governance, registries, and rendered-entry source facts. |
| `docs/pursuing_goal/ids_v0_1/` | 32 | Check root lock, stage index, batch upload lock, stage contracts, validators, tests, and evidence chain. |
| `scripts/` | 9 | Check launcher, install, stop, smoke-test, icon, and report-generation path references without changing behavior in Phase 1. |
| `backend/tests/` | 4 | Check focused regression tests are still present and named paths remain resolvable. |
| `backend/app/` | 13 | Check product identity, route, config, model-router, reporting, and persistence references only as scan targets. |
| `frontend/` | 11 | Check customer-visible product identity and route/static references only as scan targets. |
| `app_bundle/` | 3 | Check macOS entry resource references only as scan targets. |
| `product_meta_database/` | 7 | Check accepted ProductMetaDatabase contract references only as scan targets. |

The baseline tracked-file count under `KM_IDSystem/` is 113.

## Allowed Future Paths

Phase 2 may update only the narrow files needed for a repeatable governance
regression validator or evidence slice:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE005_*`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- rendered Chinese owner entries generated from governance:
  - `KM_IDSystem/功能清单.md`
  - `KM_IDSystem/开发记录.md`
  - `KM_IDSystem/模型参数文件.md`

If Phase 2 finds a real broken README, script, test, or path reference, it must
record the exact path and propose a narrow implementation contract before
editing runtime or launcher files.

## Forbidden Paths

The following remain forbidden for STAGE-005 unless a later phase explicitly
authorizes a narrow fixture or generated contract:

- `KM_IDSystem/data/`
- `KM_IDSystem/reports/`
- `KM_IDSystem/outputs/`
- `KM_IDSystem/frontend/node_modules/`
- `KM_IDSystem/.venv/`
- any `00_ORIGINAL_RAW_DATA` path;
- any external-drive raw data root;
- unrelated CodexProject directories such as Alpha, PFI, EEI, KMFA, Memory
  Atlas, Serenity, or historical external project checkouts.

## Inputs And Outputs

Inputs:

- P0 taskpack stage file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-005_仓库治理回归验证.md`
- local stage execution index:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
- root lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
- current batch upload lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- completed local evidence for STAGE-001 through STAGE-004.

Outputs:

- a Stage 005 entry contract;
- this Phase 1 scope boundary;
- roadmap/batch-lock/event updates showing only Phase 1 completion;
- rendered Chinese owner entry updates after canonical render.

## Legacy Alias Policy

New UI, reports, generated titles, schemas, manifests, and formal
documentation must continue using `IDS / Industrial Data System`.

Old names may remain only in:

- migration notes;
- historical evidence;
- compatibility identifiers;
- tests that assert legacy names are blocked or classified;
- rollback instructions;
- explicit legacy asset/report/path explanations;
- source/company context that is not a product display name.

`ProductMetaDatabase` and `FinanceMetaDatabase` are accepted current names and
must not be treated as old-name debt during this regression validation.

## Future Phase 2 Minimum Slice

Phase 2 should create a focused governance regression validator before changing
README, scripts, tests, runtime code, or generated owner entries manually. A
valid Phase 2 slice can be limited to:

- a deterministic validator under the STAGE-005 pursuing-goal path;
- focused unittest coverage for required file presence, event JSONL parsing,
  stage-chain references, batch-upload lock, no tracked runtime-output files,
  and accepted-name preservation;
- a report that separates sparse-worktree governance omissions from real
  `KM_IDSystem/` regression failures.

Do not introduce database migrations, UI routes, file movement, external APIs,
long-running scans, raw-data ingestion, dependency installation, GitHub push,
or broad cleanup in Phase 2.

## Validation Plan

Phase 1 validation is evidence-based and does not start services:

- confirm this boundary file and the entry contract exist;
- confirm the P0 STAGE-005 taskpack SHA-256;
- confirm roadmap and batch lock point to `IDS-STAGE005-P1`;
- parse `events.jsonl`;
- run `check-render --project KM_IDSystem`;
- verify changed scope remains under allowed governance and rendered owner
  paths;
- run `git diff --check`;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects to satisfy it.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE005-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, report cleanup, service restart, dependency restoration,
runtime file restore, GitHub PR cleanup, or stage evidence deletion outside
STAGE-005.

## Decision

STAGE-005 Phase 1 is allowed to complete when this boundary, the entry
contract, roadmap, batch lock, event log, and rendered Chinese entries are in
sync. The next run may enter STAGE-005 Phase 2, but the `STAGE-001..010` batch
still must not be pushed until all 10 stages are complete, reviewed, and
repaired.
