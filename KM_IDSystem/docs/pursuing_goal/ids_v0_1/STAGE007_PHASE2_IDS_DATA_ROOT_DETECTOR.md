# IDS v0.1 STAGE-007 Phase 2 - IDS_DATA_ROOT Detector Slice

## Identity

- Stage: `STAGE-007`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE007-P2`
- Acceptance ID: `ACC-STAGE-007`
- Stage title: `IDS_DATA_ROOT 检测`
- Recorded at UTC: `2026-07-02T07:54:04Z`

## Goal

Implement the minimum read-only `IDS_DATA_ROOT` detector and `00-99`
top-level slot validator defined by Phase 1.

This phase does not start Docker services, install dependencies, create
`IDS_DATA_ROOT`, create missing `00-99` directories, recursively scan external
drive contents, import raw materials, run OCR, run Embedding, build indexes,
write runtime data, or enter Phase 3.

Marker: `STAGE007_PHASE2_READ_ONLY_DETECTOR_NO_RECURSIVE_SCAN_NO_PHASE3`.

## Implemented Slice

Added `KM_IDSystem/scripts/detect_ids_data_root.py`.

The detector provides:

- explicit configured-path handling;
- `expected_path` mismatch detection;
- root absent, root not directory, and root permission-denied states;
- immediate top-level-only `00-99` numeric slot validation;
- missing numeric slot detection;
- duplicate numeric slot detection;
- malformed top-level entry detection;
- `00_ORIGINAL_RAW_DATA` reserved slot presence and read-only policy metadata;
- operations-only JSON output for the IDS operations entrance.

The detector returns schema version
`ids.stage007.ids_data_root_detector.v1` and always records:

- `stage=STAGE-007`;
- `acceptance_id=ACC-STAGE-007`;
- `entrance=IDS 系统运营入口`;
- `customer_visible=false`;
- `does_not_start_services=true`;
- `does_not_create_ids_data_root=true`;
- `does_not_scan_recursively=true`.

## State Contract

Implemented states:

| State | Safe mode | Meaning |
|---|---:|---|
| `NOT_CONFIGURED` | yes | No explicit `IDS_DATA_ROOT` value was provided. |
| `PATH_CHANGED` | yes | Configured path differs from expected path. |
| `ROOT_ABSENT` | yes | Configured root path is absent. |
| `ROOT_NOT_DIRECTORY` | yes | Configured path exists but is not a directory. |
| `ROOT_PERMISSION_DENIED` | yes | Root exists but cannot be read/searched. |
| `MALFORMED_TOP_LEVEL_ENTRY` | yes | Top-level entry is not a valid numeric slot directory. |
| `DUPLICATE_NUMERIC_SLOT` | yes | Numeric slot appears more than once. |
| `MISSING_NUMERIC_SLOTS` | yes | One or more `00-99` slots are missing. |
| `STRUCTURE_COMPLETE` | no | All numeric slots `00` through `99` exist exactly once. |
| `UNKNOWN` | yes | Filesystem check could not be classified. |

Safe mode pauses `bulk_import`, `recursive_directory_scanning`,
`raw_material_cleanup`, `ocr`, `embedding`, `index_rebuild`, and
`batch_report_generation`.

## TDD Evidence

Focused test file:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py`

Red run before implementation:

```text
Ran 5 tests in 0.021s
FAILED (failures=5)
```

Expected failure reason: `KM_IDSystem/scripts/detect_ids_data_root.py` did not
exist.

Green run after implementation:

```text
Ran 5 tests in 0.123s
OK
```

The tests cover:

- unconfigured root fails closed without creating a guessed directory;
- complete `00-99` structure is accepted without recursive scan;
- missing numeric slot enters safe mode;
- duplicate numeric slot enters safe mode;
- malformed top-level entry enters safe mode;
- root path that is not a directory enters safe mode;
- permission-denied root enters safe mode;
- CLI JSON remains operations-only and not customer-visible.

## Final Validation Evidence

Fresh Phase 2 validation in this run:

- TDD red run before implementation returned `Ran 5 tests` and
  `FAILED (failures=5)` because `detect_ids_data_root.py` did not exist.
- Focused green run:
  `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py -q`
  returned `Ran 5 tests`, `OK`.
- STAGE-006 regression run:
  `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
  returned `Ran 7 tests`, `OK`.
- CLI smoke:
  `python -B KM_IDSystem/scripts/detect_ids_data_root.py --ids-data-root ''`
  returned `stage=STAGE-007`, `acceptance_id=ACC-STAGE-007`,
  `customer_visible=false`, `state=NOT_CONFIGURED`, `safe_mode=true`,
  `does_not_create_ids_data_root=true`, and
  `does_not_scan_recursively=true`.
- `python -B -m py_compile KM_IDSystem/scripts/detect_ids_data_root.py`
  passed; the generated detector pyc was removed after verification.
- `python -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`.
- STAGE-007 Phase 2 marker, scope, and JSONL check returned
  `stage007_phase2_marker_jsonl_scope_ok=True`.
- `git diff --check` passed.
- `python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned the known 28 sparse-worktree/root-governance/unrelated-project
  errors and no STAGE-007 product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Boundaries Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, or report
  jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, or
  runtime databases;
- create `IDS_DATA_ROOT`;
- create missing `00-99` directories;
- recursively scan external-drive contents;
- open raw material files;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- expose machine diagnostics to the customer flow;
- push, open PR, merge, or upload to GitHub.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE007-P2` commit. This
removes only the read-only detector, focused tests, Phase 2 evidence, and
governance/rendered-entry updates.

No data cleanup, schema rollback, Docker cleanup, service restart, external
drive cleanup, dependency restoration, report cleanup, or GitHub PR cleanup is
needed because Phase 2 creates no runtime or external-drive artifacts.

## Decision

STAGE-007 Phase 2 is locally complete when the focused unittest, CLI smoke,
syntax check, owner render check, marker/scope/JSONL check, and diff check pass.
Phase 3 may validate additional edge scenarios only in a later run.
