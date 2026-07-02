# IDS v0.1 STAGE-010 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-010`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE010-P3`
- Acceptance ID: `ACC-STAGE-010`
- Stage title: `本地路径合同`
- Recorded at UTC: `2026-07-02T09:59:47Z`

## Goal

Validate the STAGE-010 local path contract slice across deterministic exception
scenarios without touching real raw material, writing manifests, copying
backups, generating derived output, or scanning external-drive contents
recursively.

Marker: `STAGE010_PHASE3_SCENARIO_VALIDATION_READ_ONLY_NO_PHASE4`.

## Scenario Matrix

Phase 3 adds `build_stage010_scenario_report()` in
`KM_IDSystem/scripts/check_local_path_contract.py`. It composes the Phase 2
`evaluate_local_path_contract()` behavior into a scenario matrix:

| Scenario | Expected state | Proof target |
|---|---|---|
| `online` | `PATH_CONTRACT_OK` | bounded preflight allowed only |
| `offline_root` | `SOURCE_PATH_NOT_READY` | missing external root blocks source/path workflows |
| `reconnected_root` | `SOURCE_PATH_NOT_READY` | reconnected root requires explicit revalidation before resume |
| `permission_denied_root` | `SOURCE_PATH_NOT_READY` | permission-denied root blocks path contract readiness |
| `path_changed` | `SOURCE_PATH_NOT_READY` | configured root mismatch blocks local path contract |
| `missing_source` | `SOURCE_PATH_NOT_READY` | absent source path fails closed without creating it |
| `invalid_source_uri` | `SOURCE_URI_INVALID` | non-`file://` source URI fails before path work |
| `low_free_space` | `PROCESSED_PATH_UNBOUNDED` | internal disk pressure blocks derived output work |
| `planned_output_exceeds_budget` | `PROCESSED_PATH_UNBOUNDED` | declared output that crosses the hard minimum is blocked |

The path-role risk matrix verifies:

| Scenario | Expected state |
|---|---|
| `processed_relative` | `PROCESSED_PATH_UNBOUNDED` |
| `backup_inside_source` | `BACKUP_PATH_UNSAFE` |
| `manifest_bad_extension` | `MANIFEST_PATH_UNSAFE` |
| `report_export_missing` | `REPORT_EXPORT_PATH_UNSAFE` |

The report returns:

- `schema_version=ids.stage010.phase3_scenarios.v1`
- `phase=Phase 3`
- `customer_visible=false`
- `overall_valid=true` only when all expected states, role-risk states,
  safe-mode pauses, and operations-only flags are true.

## TDD Evidence

RED command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py
```

RED result:

- `FAILED (errors=1)`
- expected failure reason:
  `AttributeError: module 'stage010_local_path_contract' has no attribute 'build_stage010_scenario_report'`

GREEN command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py
```

GREEN result:

- `Ran 7 tests in 0.151s`
- `OK`

## Safety Boundaries

The Phase 3 validation uses temporary directories and synthetic byte counts
only. It does not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, cleanup,
  backup, manifest, or report jobs;
- install dependencies or create `.venv`, `node_modules`, `data`, `reports`,
  or `outputs`;
- create real `IDS_DATA_ROOT` or missing `00-99` directories;
- recursively scan external-drive contents;
- open, hash, copy, move, delete, or mutate source material;
- write manifests, copy backups, or generate processed/report output;
- expose machine diagnostics to customer-visible flows;
- push to GitHub, open a PR, merge, or enter Phase 4.

Safe mode must pause:

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

## Validation Plan

Final validation must include:

- Stage010 focused unittest;
- Stage007/008/009 regression unittests;
- direct Stage010 scenario report smoke with `overall_valid=true`;
- Python syntax check for `check_local_path_contract.py`;
- owner render drift check;
- Phase 3 marker/roadmap/batch/event checks;
- changed-scope and whitespace checks;
- semantic governance diagnostic without expanding unrelated sparse projects.

## Final Validation Results

Fresh validation for this phase used the bundled Codex Python runtime.

| Check | Result |
|---|---|
| STAGE-010 focused unittest | `Ran 7 tests in 0.245s` / `OK` |
| STAGE-007/008/009 regression unittests | `Ran 18 tests in 0.579s` / `OK` |
| Python syntax check | `py_compile` exit 0 |
| Direct Stage010 scenario smoke | `schema_version=ids.stage010.phase3_scenarios.v1`, `overall_valid=true`; scenario states include `PATH_CONTRACT_OK`, `SOURCE_PATH_NOT_READY`, `SOURCE_URI_INVALID`, `PROCESSED_PATH_UNBOUNDED`; path role risk states include `BACKUP_PATH_UNSAFE`, `MANIFEST_PATH_UNSAFE`, `REPORT_EXPORT_PATH_UNSAFE` |
| Owner render check | `drift_count=0`, `reference_issue_count=0` |
| Marker / scope / JSONL check | marker, Phase 3 task ID, event ID, batch lock, next gate, completed hours, and changed scope all matched |
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

Rollback Phase 3 by reverting:

- `KM_IDSystem/scripts/check_local_path_contract.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py`
- this evidence file
- the STAGE-010 Phase 3 roadmap, batch-lock, events, and rendered owner-entry
  updates.

No runtime data, generated report, dependency folder, external-drive write,
manifest cleanup, backup cleanup, service restart, or GitHub PR cleanup is
required.
