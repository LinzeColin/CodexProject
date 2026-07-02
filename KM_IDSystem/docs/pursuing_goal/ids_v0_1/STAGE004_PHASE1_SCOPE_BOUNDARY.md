# IDS v0.1 STAGE-004 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-004`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE004-P1`
- Acceptance ID: `ACC-STAGE-004`
- Stage title: `旧名称引用扫描`
- Recorded at UTC: `2026-07-02T06:10:47Z`

## Goal

Confirm the boundary for scanning old names before any replacement,
validator implementation, runtime integration, UI change, or cleanup action is
performed.

This phase intentionally creates a contract only. It does not remove or
rewrite legacy references and does not modify active runtime files.

## Scan Families

STAGE-004 will classify these legacy-name families:

| Family | Examples | Phase 1 treatment |
|---|---|---|
| Legacy product display names | `Wuhan Kaiming OpMe`, `武汉开明智能工业运维助手` | Allowed only in migration, history, tests, rollback, or explicit legacy alias context. |
| Legacy path or slug aliases | `OpMe_System`, `opme-system`, `wuhan-kaiming-assistant`, `wuhan_kaiming` | Allowed only for compatibility paths, migration notes, tests, or stale-path warnings. |
| Word-boundary `OpMe` aliases | `OpMe`, `OPME`, `opme` | Must be classified carefully so ordinary substrings are not false positives. |
| Legacy company/source wording | `Wuhan Kaiming`, `武汉开明` | Allowed only where it describes company/source context, not new product display identity. |
| Legacy asset/report identifiers | `OpMeIcon`, `OpMe_structure_report` | Allowed as compatibility file names until an explicit asset/report rename stage changes them. |
| Standalone finance old name | standalone `MetaDatabase` | Allowed only in STAGE-003 migration, validation, taskpack source, or rollback context. |

The scan must not treat `ProductMetaDatabase` as old-name debt. It is an
accepted STAGE-002 subsystem. The scan must not treat `FinanceMetaDatabase`
as old-name debt. It is the accepted STAGE-003 canonical finance metadata
name.

## Baseline Reference Scan

Before creating STAGE-004 Phase 1 artifacts, Phase 1 scanned tracked text
files under `KM_IDSystem/` only. Runtime output, dependency, cache, reports,
and data folders were excluded.

| Metric | Result |
|---|---:|
| tracked text files scanned | 101 |
| total old-name family hits | 900 |
| unique tracked paths with hits | 44 |
| runtime-family hit refs | 39 |

Pattern counts:

| Pattern family | Hits |
|---|---:|
| `Wuhan Kaiming OpMe` | 16 |
| `武汉开明智能工业运维助手` | 5 |
| `wuhan-kaiming-assistant` | 3 |
| `OpMe_System` | 6 |
| `opme-system` | 6 |
| word-boundary `OpMe`/`OPME`/`opme` | 755 |
| `wuhan_kaiming` | 6 |
| `Wuhan Kaiming` | 17 |
| `武汉开明` | 12 |
| `OpMeIcon` | 13 |
| `OpMe_structure_report` | 5 |
| standalone `MetaDatabase` | 56 |

Baseline affected groups:

- active runtime context:
  `backend/app/core/config.py`, `backend/app/services/model_router.py`,
  `backend/tests/`, `scripts/build_app_bundle.sh`,
  `scripts/generate_app_icon.py`;
- active owner docs:
  `README.md`, `docs/HANDOFF.md`, `CHANGELOG.md`;
- governance and historical evidence:
  `docs/governance/**`, `docs/OpMe_structure_report.md`,
  `docs/CLEANUP_REPORT_2026-06-13.md`,
  `docs/pursuing_goal/ids_v0_1/STAGE0*`, `STAGE001*`, `STAGE002*`,
  `STAGE003*`, and execution index files.

These baseline hits are not all defects. Phase 2 and Phase 3 must classify
each allowed context before proposing a replacement.

## Allowed Future Paths

Phase 2 may update only the narrow files needed for a scan contract, scan
tool, or classification report:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_*`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- rendered Chinese owner entries generated from governance:
  - `KM_IDSystem/功能清单.md`
  - `KM_IDSystem/开发记录.md`
  - `KM_IDSystem/模型参数文件.md`

If Phase 2 finds an active display-name defect in runtime code, it must record
the exact path and propose a narrow implementation contract before editing:

- `KM_IDSystem/backend/...`
- `KM_IDSystem/frontend/...`
- `KM_IDSystem/scripts/...`
- `KM_IDSystem/app_bundle/...`

## Forbidden Paths

The following remain forbidden for STAGE-004 unless a later phase explicitly
authorizes a narrow fixture or generated contract:

- `KM_IDSystem/data/`
- `KM_IDSystem/reports/`
- `KM_IDSystem/outputs/`
- `KM_IDSystem/frontend/node_modules/`
- `KM_IDSystem/.venv/`
- `KM_IDSystem/product_meta_database/` when the only reason is a false
  positive on `ProductMetaDatabase`;
- any `00_ORIGINAL_RAW_DATA` path;
- any external-drive raw data root;
- unrelated CodexProject directories such as Alpha, PFI, EEI, KMFA, Memory
  Atlas, Serenity, or historical external project checkouts.

## Inputs And Outputs

Inputs:

- P0 taskpack stage file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-004_旧名称引用扫描.md`
- local stage execution index:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
- root lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
- current batch upload lock:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`

Outputs:

- a Stage 004 entry contract;
- this Phase 1 scope boundary;
- roadmap/batch-lock/event updates showing only Phase 1 completion;
- rendered Chinese owner entry updates after canonical render.

## Legacy Name Policy

New UI, reports, generated titles, schemas, manifests, and formal
documentation must use `IDS / Industrial Data System` for the product name.

Old names may remain only in:

- migration notes;
- historical evidence;
- compatibility identifiers;
- tests that assert legacy names are blocked or classified;
- rollback instructions;
- explicit legacy asset/report path explanations;
- source/company context that is not a product display name.

## Future Phase 2 Minimum Slice

Phase 2 should create a focused scan validator before making any replacement.
A valid Phase 2 slice can be limited to:

- a deterministic old-name scan script under the STAGE-004 pursuing-goal path;
- unit coverage for false positives such as `ProductMetaDatabase`;
- a classification report that separates allowed legacy context from active
  display-name debt;
- roadmap/events/batch lock and rendered Chinese entry updates.

Do not introduce database migrations, UI routes, file movement, external APIs,
long-running scans, raw-data ingestion, or broad cleanup in Phase 2.

## Validation Plan

Phase 1 validation is evidence-based and does not start services:

- confirm this boundary file and the entry contract exist;
- confirm the P0 STAGE-004 taskpack SHA-256;
- confirm roadmap and batch lock point to `IDS-STAGE004-P1`;
- parse `events.jsonl`;
- run `check-render --project KM_IDSystem`;
- verify changed scope remains under allowed governance and rendered owner
  paths;
- run full semantic validate only as a known sparse-worktree diagnostic and do
  not expand unrelated projects to satisfy it.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE004-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, report cleanup, service restart, dependency restoration,
runtime file restore, or legacy-name replacement reversal.

## Decision

STAGE-004 Phase 1 is allowed to complete when this boundary, the entry
contract, roadmap, batch lock, event log, and rendered Chinese entries are in
sync. The next run may enter STAGE-004 Phase 2, but the `STAGE-001..010` batch
still must not be pushed until all 10 stages are complete, reviewed, and
repaired.
