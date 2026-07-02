# IDS v0.1 STAGE-008 Phase 3 - Scenario Validation

## Identity

- Stage: `STAGE-008`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE008-P3`
- Acceptance ID: `ACC-STAGE-008`
- Stage title: `可拔插移动硬盘状态机`
- Recorded at UTC: `2026-07-02T08:44:40Z`

## Goal

Validate the Phase 2 read-only removable-drive state machine against online,
offline, reconnected, permission-denied, path-changed, structure-invalid,
internal-storage, and safe-mode pause scenarios.

This phase uses temporary directories and synthetic byte counts only. It does
not start Docker services, install dependencies, create a real `IDS_DATA_ROOT`,
create missing `00-99` directories on an external drive, recursively scan
external-drive contents, open raw material files, import materials, run OCR,
run Embedding, build indexes, write runtime data, or enter Phase 4.

Marker: `STAGE008_PHASE3_SCENARIO_VALIDATION_NO_REAL_DRIVE_NO_PHASE4`.

## Implemented Scenario Helper

Extended `KM_IDSystem/scripts/check_removable_drive_state.py` with:

- `build_stage008_scenario_report(...)` for deterministic Phase 3 scenario
  validation;
- an operations-only scenario schema
  `ids.stage008.phase3_scenarios.v1`;
- explicit `overall_valid` evidence for drive transitions, storage guards, and
  safe-mode pause coverage.

The helper composes the Phase 2 `evaluate_removable_drive_state(...)` function
and does not create directories, start services, scan external-drive contents,
or resume any data-moving workflow.

## TDD Evidence

Focused test file:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py`

Red run before implementation:

```text
Ran 6 tests in 0.154s
FAILED (errors=1)
```

Expected failure reason:

```text
AttributeError: module 'stage008_removable_drive_state' has no attribute 'build_stage008_scenario_report'
```

Green run after implementation:

```text
Ran 6 tests in 0.155s
OK
```

## Scenario Coverage

Removable-drive lifecycle scenarios covered:

| Scenario | Expected STAGE-008 state | Safety decision |
|---|---|---|
| complete `00-99` structure with OK storage | `ONLINE_VALIDATED` | no safe mode, no auto resume |
| configured root absent | `OFFLINE` | safe mode |
| complete root after prior offline state | `RECONNECTED_NEEDS_REVALIDATION` | safe mode, revalidation required |
| permission probe fails | `PERMISSION_DENIED` | safe mode |
| configured path differs from expected path | `PATH_CHANGED` | safe mode, operator confirmation required |
| missing numeric slot | `STRUCTURE_INVALID` | safe mode |

Internal-storage scenarios covered:

| Scenario | Expected STAGE-008 state | Safety decision |
|---|---|---|
| free space above warning threshold | `ONLINE_VALIDATED` | storage does not force safe mode |
| free space below hard minimum | `STORAGE_BLOCKED` | safe mode |
| used percent crosses high-waterline threshold | `STORAGE_BLOCKED` | safe mode |

Safe-mode pause list verified:

- `bulk_import`;
- `recursive_directory_scanning`;
- `raw_material_cleanup`;
- `ocr`;
- `embedding`;
- `index_rebuild`;
- `batch_report_generation`.

## Important Negative Evidence

The Phase 3 scenarios intentionally do not:

- require a real external drive;
- create a real `IDS_DATA_ROOT`;
- create or repair missing external-drive slots;
- recursively inspect `00_ORIGINAL_RAW_DATA`;
- open nested raw files;
- generate manifests, evidence ledgers, audit logs, reports, or indexes;
- start Docker, backend, frontend, OCR, Embedding, or worker services;
- automatically resume import, OCR, Embedding, indexing, cleanup, or report
  generation;
- push, open PR, merge, or upload to GitHub.

## Validation Plan

Fresh Phase 3 validation should include:

- focused STAGE-008 unittest;
- STAGE-007 detector regression unittest;
- STAGE-006 environment baseline regression unittest;
- scenario report smoke for `build_stage008_scenario_report(...)`;
- CLI smoke for `check_removable_drive_state.py`;
- `py_compile` for `check_removable_drive_state.py`;
- `check-render --project KM_IDSystem`;
- STAGE-008 Phase 3 marker, scope, and JSONL check;
- `git diff --check`;
- semantic governance validate as a sparse-worktree diagnostic only.

## Final Validation Results

Fresh Phase 3 validation run in this worktree:

| Check | Result |
|---|---|
| focused STAGE-008 unittest | `Ran 6 tests in 0.197s` / `OK` |
| STAGE-007 detector regression unittest | `Ran 7 tests in 0.254s` / `OK` |
| STAGE-006 environment regression unittest | `Ran 7 tests in 0.163s` / `OK` |
| CLI smoke | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false` |
| scenario report smoke | `overall_valid=true`; drive states include `ONLINE_VALIDATED`, `OFFLINE`, `RECONNECTED_NEEDS_REVALIDATION`, `PERMISSION_DENIED`, `PATH_CHANGED`, `STRUCTURE_INVALID`; storage states include `ONLINE_VALIDATED`, `STORAGE_BLOCKED` |
| Python syntax check | `py_compile` exit 0; generated cache file removed |
| Owner render check | `drift_count=0`, `reference_issue_count=0` |
| STAGE-008 Phase 3 marker, scope, and JSONL check | passed |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE008-P3` commit. This
removes only scenario-report code, focused test additions, Phase 3 evidence,
and governance/rendered-entry updates.

No data cleanup, schema rollback, Docker cleanup, service restart, external
drive cleanup, dependency restoration, report cleanup, or GitHub PR cleanup is
needed because Phase 3 creates no runtime or external-drive artifacts.

## Decision

STAGE-008 Phase 3 is locally complete when focused tests, scenario smoke,
render, marker/scope/JSONL, and diff checks pass. Phase 4 closeout must be a
separate later run.
