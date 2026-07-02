# IDS v0.1 STAGE-008 Phase 2 - Removable Drive State Machine Slice

## Identity

- Stage: `STAGE-008`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE008-P2`
- Acceptance ID: `ACC-STAGE-008`
- Stage title: `可拔插移动硬盘状态机`
- Recorded at UTC: `2026-07-02T08:37:42Z`

## Goal

Implement the minimum read-only removable-drive lifecycle state machine defined
by Phase 1.

This phase does not start Docker services, install dependencies, create
`IDS_DATA_ROOT`, create missing `00-99` directories, recursively scan external
drive contents, import raw materials, run OCR, run Embedding, build indexes,
write runtime data, or enter Phase 3.

Marker: `STAGE008_PHASE2_READ_ONLY_STATE_MACHINE_NO_AUTO_RESUME_NO_PHASE3`.

## Implemented Slice

Added `KM_IDSystem/scripts/check_removable_drive_state.py`.

The state machine composes:

- STAGE-007 `detect_ids_data_root(...)` root and `00-99` structure states;
- STAGE-007 `evaluate_storage_guard(...)` internal-disk pressure states;
- STAGE-008 lifecycle transition rules from Phase 1.

It returns schema version `ids.stage008.removable_drive_state.v1` and always
records:

- `stage=STAGE-008`;
- `acceptance_id=ACC-STAGE-008`;
- `entrance=IDS 系统运营入口`;
- `customer_visible=false`;
- `auto_resume=false`;
- `does_not_start_services=true`;
- `does_not_create_ids_data_root=true`;
- `does_not_scan_recursively=true`;
- `does_not_scan_external_drive_contents=true`.

## State Mapping

| Source evidence | STAGE-008 state | Resume allowed |
|---|---|---:|
| no configured `IDS_DATA_ROOT` | `NOT_CONFIGURED` | no |
| absent configured root | `OFFLINE` | no |
| structurally complete root after prior offline/not configured/unknown | `RECONNECTED_NEEDS_REVALIDATION` | no |
| configured path differs from expected path | `PATH_CHANGED` | no |
| root permission check fails | `PERMISSION_DENIED` | no |
| not-directory, missing slot, duplicate slot, or malformed entry | `STRUCTURE_INVALID` | no |
| internal storage is `BLOCKED` or `UNKNOWN` | `STORAGE_BLOCKED` | no |
| root structure is complete and storage is not blocked | `ONLINE_VALIDATED` | yes, bounded preflight only |

Even when `resume_allowed=true`, `auto_resume=false`; later stages must still
explicitly start bounded preflight or data-moving work.

## TDD Evidence

Focused test file:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py`

Red run before implementation:

```text
Ran 5 tests in 0.021s
FAILED (failures=5)
```

Expected failure reason: `KM_IDSystem/scripts/check_removable_drive_state.py`
did not exist.

Green run after implementation and CLI import-path fix:

```text
Ran 5 tests in 0.119s
OK
```

The tests cover:

- unconfigured and absent roots enter safe mode and do not create directories;
- reconnected complete roots require explicit revalidation before resume;
- validated roots can enter `ONLINE_VALIDATED` without auto import;
- path-changed, permission-denied, structure-invalid, and storage-blocked
  states map into the STAGE-008 lifecycle states;
- CLI JSON remains operations-only and not customer-visible.

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
- automatically resume bulk import, OCR, Embedding, indexing, cleanup, or
  report generation after reconnect;
- copy real raw materials into Git;
- add secrets, API keys, database passwords, or cloud credentials;
- expose machine diagnostics to the customer flow;
- push, open PR, merge, or upload to GitHub.

## Validation Plan

Fresh Phase 2 validation should include:

- focused STAGE-008 unittest;
- STAGE-007 detector regression unittest;
- STAGE-006 environment baseline regression unittest;
- CLI smoke for `check_removable_drive_state.py`;
- `py_compile` for `check_removable_drive_state.py`;
- `check-render --project KM_IDSystem`;
- STAGE-008 Phase 2 marker, scope, and JSONL check;
- `git diff --check`;
- semantic governance validate as a sparse-worktree diagnostic only.

## Final Validation Results

Fresh validation for this phase used the bundled Codex Python runtime.

| Check | Result |
|---|---|
| STAGE-008 focused unittest | `Ran 5 tests in 0.165s` / `OK` |
| STAGE-007 detector regression unittest | `Ran 7 tests in 0.257s` / `OK` |
| STAGE-006 environment regression unittest | `Ran 7 tests in 0.279s` / `OK` |
| CLI smoke | `state=NOT_CONFIGURED`, `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true` |
| Python syntax check | `py_compile` exit 0 |
| Owner render check | `drift_count=0`, `reference_issue_count=0` |
| Marker / scope / JSONL check | marker, Phase 2 task ID, event ID, batch lock, next gate, and completed hours found |
| Whitespace diff check | `git diff --check` exit 0 |

Semantic governance validation remains a sparse-worktree diagnostic:

```text
projects checked: KM_IDSystem
errors: 28
warnings: 0
```

The 28 errors are the known sparse checkout conflicts: missing root governance
schema/CI/hook files and registered sibling project paths that are intentionally
not expanded in this single-project worktree.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE008-P2` commit. This
removes only the read-only state machine, focused tests, Phase 2 evidence, and
governance/rendered-entry updates.

No data cleanup, schema rollback, Docker cleanup, service restart, external
drive cleanup, dependency restoration, report cleanup, or GitHub PR cleanup is
needed because Phase 2 creates no runtime or external-drive artifacts.

## Decision

STAGE-008 Phase 2 is locally complete when the focused unittest, CLI smoke,
syntax check, owner render check, marker/scope/JSONL check, and diff check pass.
Phase 3 may validate additional edge scenarios only in a later run.
