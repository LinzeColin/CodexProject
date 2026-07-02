# IDS v0.1 STAGE-011 Phase 2 Safe-Mode Baseline

## Identity

- Stage: `STAGE-011`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE011-P2`
- Acceptance ID: `ACC-STAGE-011`
- Stage title: `安全模式基线`
- Recorded at UTC: `2026-07-02T11:22:17Z`

## Goal

Implement the minimum read-only safe-mode baseline interface for IDS operations.
The interface composes the existing STAGE-006 environment baseline, STAGE-007
`IDS_DATA_ROOT` detector, STAGE-008 removable-drive lifecycle state, STAGE-009
storage budget, and STAGE-010 local path contract into one STAGE-011 safe-mode
classification.

This phase does not start services, create directories, write runtime files,
read raw database content, call external APIs, generate reports, run OCR, run
Embedding, build indexes, copy backups, write manifests, push to GitHub, or
enter Phase 3.

Marker: `STAGE011_PHASE2_SAFE_MODE_BASELINE_IMPLEMENTED_NO_PHASE3_NO_GITHUB_UPLOAD`.

## Implemented Slice

New read-only script:

- `KM_IDSystem/scripts/check_safe_mode_baseline.py`

New focused test:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py`

The script exposes:

- `evaluate_safe_mode_baseline(...)`
- CLI JSON output via `python -B KM_IDSystem/scripts/check_safe_mode_baseline.py ...`

The script accepts explicit local path, storage, indexing, and external API
budget state inputs. It does not inspect provider accounts, call APIs, or infer
quota from external systems.

## State Mapping

| Input condition | STAGE-011 state |
|---|---|
| All path, storage, index, and API-budget inputs are safe | `SAFE_MODE_CLEAR` |
| `IDS_DATA_ROOT` is absent or not configured | `SAFE_MODE_ROOT_NOT_CONFIGURED` |
| Removable drive is offline | `SAFE_MODE_DRIVE_OFFLINE` |
| Reconnected/path-changed state needs a fresh preflight | `SAFE_MODE_REVALIDATION_REQUIRED` |
| Filesystem permission state is denied | `SAFE_MODE_PERMISSION_DENIED` |
| Internal storage is below waterline, unknown, or planned output is unbounded | `SAFE_MODE_STORAGE_BLOCKED` |
| Source URI or processed/backup/manifest/report export path is unsafe | `SAFE_MODE_PATH_BLOCKED` |
| Index state is failed, stale, partial, or unknown | `SAFE_MODE_INDEX_FAILED` |
| External API budget is exceeded, rate-limited, missing, unsafe, or unknown | `SAFE_MODE_API_BUDGET_EXCEEDED` |
| State cannot be classified | `SAFE_MODE_UNKNOWN` |

## Output Contract

The STAGE-011 report includes:

- `schema_version: ids.stage011.safe_mode_baseline.v1`
- `stage: STAGE-011`
- `phase: Phase 2`
- `acceptance_id: ACC-STAGE-011`
- `entrance: IDS 系统运营入口`
- `customer_visible: false`
- `state`
- `safe_mode`
- `auto_resume: false`
- `bounded_preflight_only: true`
- `paused_workflows`
- `operator_actions`
- `requires_operator_confirmation`
- `requires_revalidation`
- `local_path_contract_state`
- `storage_budget_state`
- `removable_drive_state`
- `index_state`
- `api_budget_state`
- embedded STAGE-010 local path contract evidence

## No-Side-Effect Guardrails

Every report must keep these flags true:

- `does_not_start_services`
- `does_not_create_ids_data_root`
- `does_not_scan_recursively`
- `does_not_scan_external_drive_contents`
- `does_not_open_source_files`
- `does_not_hash_source_files`
- `does_not_read_raw_metadata`
- `does_not_generate_outputs`
- `does_not_write_runtime_data`
- `does_not_write_manifests`
- `does_not_copy_backups`
- `does_not_call_external_apis`

## TDD Evidence

RED run before implementation:

- command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py -q`
- result: `Ran 4 tests ... FAILED (failures=4)`
- expected reason: `KM_IDSystem/scripts/check_safe_mode_baseline.py` did not
  exist yet.

GREEN runs after implementation:

- STAGE-011 focused test:
  - command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py -q`
  - result: `Ran 4 tests ... OK`
- D02 regression set:
  - command: bundled Python `-B -m unittest` for STAGE-006, STAGE-007,
    STAGE-008, STAGE-009, STAGE-010, and STAGE-011 tests
  - result: `Ran 36 tests ... OK`

## CLI Smoke Evidence

Command summary:

- `python -B KM_IDSystem/scripts/check_safe_mode_baseline.py`
- `--source-uri file:///Users/linzezhang/Downloads/IDS_MetaData`
- `--ids-data-root ''`
- `--internal-total-gib 1000`
- `--internal-free-gib 300`
- `--planned-output-gib 20`
- `--job-kind bounded_preflight`
- `--index-state OK`
- `--api-budget-state OK`
- `--no-require-external-root`

Result summary:

- `state=SAFE_MODE_CLEAR`
- `safe_mode=false`
- `local_path_contract_state=PATH_CONTRACT_OK`
- `storage_budget_state=BUDGET_OK`
- `does_not_read_raw_metadata=true`
- `does_not_call_external_apis=true`
- `does_not_generate_outputs=true`

This smoke used the existing path-contract preflight. It did not list, open,
hash, copy, move, delete, modify, or dump `/Users/linzezhang/Downloads/IDS_MetaData`.

## Forbidden Phase 2 Actions Confirmed

Phase 2 did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, report,
  backup, manifest, or API jobs;
- install dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, indexes, OCR outputs, embeddings, manifests, or
  runtime databases;
- create, repair, recursively list, scan, move, delete, or mutate
  `IDS_DATA_ROOT`;
- read, hash, dump, copy, move, delete, rename, normalize, or mutate
  `/Users/linzezhang/Downloads/IDS_MetaData`;
- create fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- call external APIs or consume quota;
- push to GitHub.

## Phase 3 Entry

Phase 3 may add scenario coverage for drive online/offline/reconnected,
permission, path change, storage blocked, path blocked, index failed, API
budget exceeded, and safe-mode pause/resume behavior. It must keep all raw-data
and no-side-effect guardrails intact.

## Rollback

Revert the Phase 2 commit. Because this slice is a read-only script, test, and
governance evidence, rollback does not require data cleanup, dependency
cleanup, service restart, raw metadata repair, external-drive cleanup, report
cleanup, or API quota cleanup.
