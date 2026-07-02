# IDS v0.1 STAGE-006 Phase 2 Environment Baseline Slice

## Identity

- Stage: `STAGE-006`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE006-P2`
- Acceptance ID: `ACC-STAGE-006`
- Stage title: `macOS M2 Max Docker 基线`
- Recorded at UTC: `2026-07-02T07:21:58Z`

## Goal

Implement the minimum read-only environment, path-state, state-enum, and
storage-budget slice required by STAGE-006 without starting services, installing
dependencies, writing runtime data, or touching external `IDS_DATA_ROOT`
contents.

## Implemented Slice

Phase 2 adds:

- `KM_IDSystem/scripts/check_environment_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py`

The script is a pure standard-library operations diagnostic. It exposes:

- `evaluate_ids_data_root(...)`
- `evaluate_storage_budget(...)`
- `build_report(...)`
- CLI JSON output for IDS operations use.

It intentionally does not create directories, does not start Docker, does not
start backend/frontend services, does not install dependencies, and does not
scan external-drive contents.

## State Contract

`IDS_DATA_ROOT` states implemented in the slice:

| State | Safe mode | Meaning |
|---|---|---|
| `NOT_CONFIGURED` | yes | no configured `IDS_DATA_ROOT` value |
| `OFFLINE` | yes | configured path is absent |
| `ONLINE` | no | configured path is present and readable |
| `RECONNECTED` | yes | path is present after a non-online prior state and needs revalidation |
| `PERMISSION_DENIED` | yes | path exists but is not readable/searchable |
| `PATH_CHANGED` | yes | configured path differs from expected path |
| `UNKNOWN` | yes | state cannot be classified safely |

Safe mode pauses:

- `bulk_import`
- `ocr`
- `embedding`
- `index_rebuild`
- `batch_report_generation`
- `raw_material_cleanup`

## Storage Budget Contract

The internal-storage checker returns:

- `OK` when free space and used-percent are within budget;
- `WARN` when free space is below warning threshold but above hard minimum;
- `BLOCKED` when free space is below hard minimum or used-percent exceeds the
  high-waterline threshold;
- `UNKNOWN` when bytes are invalid or unavailable.

Default thresholds in the script:

- minimum free space: `100 GiB`
- warning free space: `200 GiB`
- maximum used percent: `85`

These are local guardrails for the STAGE-006 slice. Later stages may tune them
through explicit model/parameter governance; Phase 2 does not claim production
capacity planning.

## TDD Evidence

Red test before implementation:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
- Result: 5 expected failures because
  `KM_IDSystem/scripts/check_environment_baseline.py` was missing.

Green tests after implementation:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
- Result: `Ran 5 tests`, `OK`.

Script smoke:

- Command:
  `Codex bundled python -B KM_IDSystem/scripts/check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300`
- Result:
  - `entrance="IDS 系统运营入口"`
  - `customer_visible=false`
  - `ids_data_root.state="NOT_CONFIGURED"`
  - `ids_data_root.safe_mode=true`
  - `internal_storage.state="OK"`
  - `does_not_start_services=true`
  - `does_not_create_ids_data_root=true`
  - Docker CLI and Compose version probes returned available on this machine.

Compile check:

- Command:
  `Codex bundled python -B -m py_compile KM_IDSystem/scripts/check_environment_baseline.py`
- Result: pass.

## Boundary Decisions

- The slice is an IDS operations diagnostic, not a customer-facing UI surface.
- Missing `IDS_DATA_ROOT` fails closed into safe mode and does not create a
  guessed large-data directory inside the repo.
- `PATH_CHANGED`, `RECONNECTED`, and `UNKNOWN` require operator confirmation or
  revalidation before data-moving work can resume.
- Docker version probes are allowed because they do not start Docker Desktop,
  build images, create containers, or touch runtime data.
- No backend route, frontend route, app bundle display name, service launcher
  behavior, schema migration, external API, raw-material copy, generated data,
  report output, dependency folder, GitHub push, PR, or merge was added.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE006-P2` commit. Because
Phase 2 creates only a standard-library diagnostic script, focused unittest,
and governance evidence, rollback does not require data cleanup, schema
rollback, Docker cleanup, service restart, dependency restoration, report
cleanup, runtime file restore, external-drive cleanup, or GitHub PR cleanup.

## Decision

STAGE-006 Phase 2 is locally satisfied when the focused unittest, script smoke,
compile check, rendered owner files, batch lock, roadmap, and event log all
point to `IDS-V0_1-STAGE006-P2`. The next run may enter STAGE-006 Phase 3 for
scenario validation, but the `STAGE-001..010` batch upload remains locked.
