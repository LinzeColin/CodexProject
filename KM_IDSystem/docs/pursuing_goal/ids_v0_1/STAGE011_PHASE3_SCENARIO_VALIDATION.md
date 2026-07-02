# IDS v0.1 STAGE-011 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-011`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE011-P3`
- Acceptance ID: `ACC-STAGE-011`
- Stage title: `安全模式基线`
- Recorded at UTC: `2026-07-02T11:38:42Z`

## Goal

Validate the STAGE-011 safe-mode baseline against deterministic local
scenarios for removable-drive lifecycle, internal storage protection, local
path blocking, index failure, external API budget exhaustion, paused workflows,
and no-side-effect guardrails.

This phase adds scenario validation only. It does not start services, install
dependencies, create runtime data, read raw metadata content, call external
APIs, generate reports, run OCR, run Embedding, build indexes, copy backups,
write manifests, push to GitHub, or enter Phase 4.

Marker: `STAGE011_PHASE3_SCENARIO_VALIDATION_NO_PHASE4_NO_GITHUB_UPLOAD`.

## Implemented Slice

Updated read-only script:

- `KM_IDSystem/scripts/check_safe_mode_baseline.py`

Updated focused test:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py`

The script now exposes:

- `build_stage011_scenario_report(...)`

The scenario report composes the Phase 2 `evaluate_safe_mode_baseline(...)`
interface and caller-owned paths. It does not create missing roots, write output
paths, inspect provider accounts, call APIs, or read source file content.

## Scenario Matrix

| Scenario | Expected state |
|---|---|
| `clear` | `SAFE_MODE_CLEAR` |
| `drive_offline` | `SAFE_MODE_DRIVE_OFFLINE` |
| `drive_reconnected` | `SAFE_MODE_REVALIDATION_REQUIRED` |
| `permission_denied` | `SAFE_MODE_PERMISSION_DENIED` |
| `path_changed` | `SAFE_MODE_REVALIDATION_REQUIRED` |
| `storage_low_free` | `SAFE_MODE_STORAGE_BLOCKED` |
| `unbounded_output_missing_cap` | `SAFE_MODE_STORAGE_BLOCKED` |
| `path_blocked` | `SAFE_MODE_PATH_BLOCKED` |
| `index_failed` | `SAFE_MODE_INDEX_FAILED` |
| `api_budget_exceeded` | `SAFE_MODE_API_BUDGET_EXCEEDED` |

The `storage_low_free` scenario also fixes the STAGE-011 mapping for the
upstream removable-drive `STORAGE_BLOCKED` state so that storage pressure is not
misclassified as a generic path block.

## Pause Coverage

The scenario report verifies that safe mode pauses:

- `bulk_import`
- `recursive_directory_scanning`
- `raw_material_cleanup`
- `ocr`
- `embedding`
- `index_rebuild`
- `backup_copy`
- `manifest_generation`
- `report_export`
- `batch_report_generation`
- `external_api_calls`

Every scenario keeps `auto_resume=false` and `bounded_preflight_only=true`.

## No-Side-Effect Guardrails

Every scenario report keeps these flags true:

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

STAGE-011 Phase 3 RED run:

- command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py -q`
- result: `Ran 5 tests ... FAILED (errors=1)`
- expected reason: `build_stage011_scenario_report` did not exist.

STAGE-011 Phase 3 GREEN run:

- command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py -q`
- result: `Ran 5 tests ... OK`

Governance validator RED run:

- command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- result: `Ran 10 tests ... FAILED (failures=1)`
- expected reason: the STAGE-005 governance regression validator did not yet
  recognize `IDS-V0_1-STAGE011-P3` as a valid later-stage current state.

Governance validator GREEN run:

- command: bundled Python `-B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- result: `Ran 10 tests ... OK`
- validator report: `valid=true`, `issue_count=0`,
  `unexpected_changed_paths=[]`

Final validation:

- full v0.1 unittest discover: `Ran 50 tests ... OK`
- D02 regression set for STAGE-006 through STAGE-011: `Ran 37 tests ... OK`
- scenario smoke: `overall_valid=true`, output paths not created, offline root
  not created, no raw metadata read, no external API call, no output generated
- `py_compile`: OK
- `check-render --project KM_IDSystem`: `drift_count=0`
- `git diff --check`: OK
- semantic validate diagnostic: return code `1`, with 29 known sparse/root or
  registered-project missing-path diagnostics and 0 `KM_IDSystem` semantic
  errors

## Raw Data Boundary

This phase did not list, open, hash, copy, move, delete, modify, dump, or scan
`/Users/linzezhang/Downloads/IDS_MetaData`.

The focused scenario test uses temporary structural directories for
`IDS_DATA_ROOT` lifecycle checks and the existing test file path as a local
read-only `file://` source path. It does not create fake IDS business data,
fake database rows, fake source documents, fabricated evidence, reports,
indexes, manifests, OCR output, Embedding output, backups, or runtime data.

## Forbidden Phase 3 Actions Confirmed

Phase 3 did not:

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

## Phase 4 Entry

Phase 4 may record final STAGE-011 delivery evidence, recoverable and
non-recoverable safe-mode states, rollback steps, default configuration notes,
and Chinese owner feedback. It must keep all raw-data, no-side-effect, and
no-upload guardrails intact until the STAGE-011..020 batch is complete,
reviewed, and repaired.

## Rollback

Revert the Phase 3 commit. Because this slice is read-only scenario code,
tests, and governance evidence, rollback does not require data cleanup,
dependency cleanup, service restart, raw metadata repair, external-drive
cleanup, report cleanup, or API quota cleanup.
