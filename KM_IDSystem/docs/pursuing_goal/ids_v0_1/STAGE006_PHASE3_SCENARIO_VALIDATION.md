# IDS v0.1 STAGE-006 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-006`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE006-P3`
- Acceptance ID: `ACC-STAGE-006`
- Stage title: `macOS M2 Max Docker 基线`
- Recorded at UTC: `2026-07-02T07:28:35Z`

## Goal

Validate the STAGE-006 minimum slice across external-drive online/offline,
reconnect, permission-denied, path-change, internal-storage waterline, and safe
mode pause scenarios without touching real `IDS_DATA_ROOT` contents.

## Scope

Phase 3 validates the Phase 2 script:

- `KM_IDSystem/scripts/check_environment_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py`

No Docker service, backend service, frontend service, dependency install,
runtime data directory, report output, generated output, real external-drive
scan, GitHub push, PR, or merge is performed.

## TDD Evidence

Red test before implementation:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
- Result: 2 expected errors because
  `build_phase3_scenario_report` did not exist.

Green tests after implementation:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
- Result: `Ran 7 tests`, `OK`.

Compile check:

- Command:
  `Codex bundled python -B -m py_compile KM_IDSystem/scripts/check_environment_baseline.py`
- Result: pass.

## Scenario Coverage

Phase 3 adds `build_phase3_scenario_report(...)` to produce a deterministic
scenario matrix from caller-provided temporary paths and byte counts.

External-drive scenarios covered:

| Scenario | Expected state | Expected safety |
|---|---|---|
| configured path exists and is readable | `ONLINE` | no safe mode |
| configured path is absent | `OFFLINE` | safe mode |
| path is present after previous offline state | `RECONNECTED` | safe mode, revalidation required |
| path exists but permission probe fails | `PERMISSION_DENIED` | safe mode |
| configured path differs from expected path | `PATH_CHANGED` | safe mode, operator confirmation required |

Internal-storage scenarios covered:

| Scenario | Expected state | Expected safety |
|---|---|---|
| free space above warning threshold | `OK` | no safe mode |
| free space below hard minimum | `BLOCKED` | safe mode |
| used percent crosses high-waterline threshold | `BLOCKED` | safe mode |

Safe mode pause list verified:

- `bulk_import`
- `ocr`
- `embedding`
- `index_rebuild`
- `batch_report_generation`
- `raw_material_cleanup`

## Validation Boundary

The permission-denied scenario is simulated with a path-specific test patch
against `os.access`; the test still uses real temporary paths for online,
offline, reconnected, and path-change cases. This avoids changing local
permissions on a real external drive and keeps the validation repeatable.

The scenario report asserts:

- `customer_visible=false`;
- `does_not_start_services=true`;
- `does_not_create_ids_data_root=true`;
- `does_not_scan_external_drive_contents=true`;
- `overall_valid=true`.

## Boundary Decisions

- The Phase 3 validation is operations-only and does not create a customer
  workflow surface.
- Real `IDS_DATA_ROOT` is not required for this phase.
- Online/offline/reconnect/path-change behavior is validated with temporary
  paths and synthetic byte budgets.
- Safe mode remains fail-closed for data-moving work.
- Internal-storage thresholds remain the Phase 2 defaults:
  minimum free `100 GiB`, warning free `200 GiB`, max used percent `85`.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE006-P3` commit. Because
Phase 3 changes only a validation helper, tests, and evidence/governance files,
rollback does not require Docker cleanup, data cleanup, external-drive cleanup,
dependency restoration, schema rollback, service restart, report cleanup, or
GitHub PR cleanup.

## Decision

STAGE-006 Phase 3 passes with deterministic coverage for online, offline,
reconnected, permission-denied, path-changed, low-free-space, high-waterline,
and safe-mode pause scenarios. The next run may enter STAGE-006 Phase 4 for
closeout evidence and rollback summary, but the STAGE-001..010 batch upload
remains locked.
