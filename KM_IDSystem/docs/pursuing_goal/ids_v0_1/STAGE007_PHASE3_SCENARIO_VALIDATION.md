# IDS v0.1 STAGE-007 Phase 3 - Scenario Validation

## Identity

- Stage: `STAGE-007`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE007-P3`
- Acceptance ID: `ACC-STAGE-007`
- Stage title: `IDS_DATA_ROOT 检测`
- Recorded at UTC: `2026-07-02T08:03:05Z`

## Goal

Validate the Phase 2 read-only `IDS_DATA_ROOT` detector against removable-drive,
path-change, directory-structure, internal-storage, and safe-mode scenarios.

This phase uses temporary directories and synthetic byte counts only. It does
not start Docker services, install dependencies, create a real `IDS_DATA_ROOT`,
create missing `00-99` directories on an external drive, recursively scan
external-drive contents, open raw material files, import materials, run OCR,
run Embedding, build indexes, write runtime data, or enter Phase 4.

Marker: `STAGE007_PHASE3_SCENARIO_VALIDATION_NO_REAL_DRIVE_NO_PHASE4`.

## Implemented Scenario Helper

Extended `KM_IDSystem/scripts/detect_ids_data_root.py` with:

- `previous_state` handling for reconnected roots;
- `evaluate_storage_guard(...)` for synthetic internal-disk pressure evidence;
- `build_stage007_scenario_report(...)` for deterministic Phase 3 scenario
  validation.

The scenario report schema is `ids.stage007.phase3_scenarios.v1`.

## TDD Evidence

Focused test file:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py`

Red run before implementation:

```text
Ran 7 tests in 0.223s
FAILED (errors=2)
```

Expected failure reasons:

- `detect_ids_data_root()` did not accept `previous_state`;
- `build_stage007_scenario_report` did not exist.

Green run after implementation:

```text
Ran 7 tests in 0.229s
OK
```

## Scenario Coverage

`IDS_DATA_ROOT` scenarios covered:

| Scenario | Expected state | Safety decision |
|---|---|---|
| complete `00-99` structure | `STRUCTURE_COMPLETE` | no safe mode |
| absent configured root | `ROOT_ABSENT` | safe mode |
| structurally complete root after prior absence | `RECONNECTED` | safe mode, revalidation required |
| permission-denied root | `ROOT_PERMISSION_DENIED` | safe mode |
| configured path differs from expected path | `PATH_CHANGED` | safe mode, operator confirmation required |
| configured path is not a directory | `ROOT_NOT_DIRECTORY` | safe mode |
| missing numeric slot | `MISSING_NUMERIC_SLOTS` | safe mode |
| duplicate numeric slot | `DUPLICATE_NUMERIC_SLOT` | safe mode |
| malformed top-level entry | `MALFORMED_TOP_LEVEL_ENTRY` | safe mode |

Internal-storage scenarios covered:

| Scenario | Expected state | Safety decision |
|---|---|---|
| adequate free space | `OK` | no storage safe mode |
| low free space | `BLOCKED` | safe mode |
| high used waterline | `BLOCKED` | safe mode |

Safe mode pauses:

- `bulk_import`;
- `recursive_directory_scanning`;
- `raw_material_cleanup`;
- `ocr`;
- `embedding`;
- `index_rebuild`;
- `batch_report_generation`.

## Important Negative Evidence

The Phase 3 scenarios use only temporary directories under the local test
runtime. They intentionally do not:

- require a real external drive;
- create a real `IDS_DATA_ROOT`;
- create or repair missing external-drive slots;
- recursively inspect `00_ORIGINAL_RAW_DATA`;
- open nested raw files;
- generate manifests, evidence ledgers, audit logs, reports, or indexes;
- start Docker, backend, frontend, OCR, Embedding, or worker services;
- push, open PR, merge, or upload to GitHub.

## Final Validation Results

Fresh Phase 3 validation run in this worktree:

| Check | Result |
|---|---|
| focused STAGE-007 unittest | `Ran 7 tests in 0.279s` / `OK` |
| STAGE-006 regression unittest | `Ran 7 tests in 0.163s` / `OK` |
| scenario report smoke | `overall_valid=True`; states include `STRUCTURE_COMPLETE`, `ROOT_ABSENT`, `RECONNECTED`, `ROOT_PERMISSION_DENIED`, `PATH_CHANGED`, `ROOT_NOT_DIRECTORY`, `MISSING_NUMERIC_SLOTS`, `DUPLICATE_NUMERIC_SLOT`, `MALFORMED_TOP_LEVEL_ENTRY`; storage states include `OK`, `BLOCKED` |
| `py_compile` for `detect_ids_data_root.py` | passed; generated cache file removed |
| `check-render --project KM_IDSystem` | `drift_count=0` |
| STAGE-007 Phase 3 marker, scope, and JSONL check | passed |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE007-P3` commit. This
removes only scenario-report code, focused test additions, Phase 3 evidence,
and governance/rendered-entry updates.

No data cleanup, schema rollback, Docker cleanup, service restart, external
drive cleanup, dependency restoration, report cleanup, or GitHub PR cleanup is
needed because Phase 3 creates no runtime or external-drive artifacts.

## Decision

STAGE-007 Phase 3 is locally complete when focused tests, scenario smoke,
render, marker/scope/JSONL, and diff checks pass. Phase 4 closeout must be a
separate later run.
