# IDS v0.1 STAGE-010 Phase 2 Local Path Contract Slice

## Identity

- Stage: `STAGE-010`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE010-P2`
- Acceptance ID: `ACC-STAGE-010`
- Stage title: `本地路径合同`
- Recorded at UTC: `2026-07-02T09:53:27Z`

## Goal

Implement the smallest read-only local path contract slice allowed by Phase 1:

- normalize and classify `file:// source_uri`;
- classify source path readiness without opening, hashing, copying, moving, or
  recursively scanning source material;
- classify `processed path`, `backup path`, `manifest path`, and report export
  path roles before any write can happen;
- compose STAGE-007 `IDS_DATA_ROOT`, STAGE-008 removable-drive state, and
  STAGE-009 storage-budget evidence;
- expose machine-side diagnostics only through `IDS 系统运营入口`;
- keep customer-facing flows hidden from local machine details.

Marker: `STAGE010_PHASE2_LOCAL_PATH_CONTRACT_READ_ONLY_NO_PHASE3`.

## Implemented Slice

| Artifact | Purpose |
|---|---|
| `KM_IDSystem/scripts/check_local_path_contract.py` | Read-only Stage 010 local path contract preflight and JSON CLI. |
| `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py` | Focused tests for source URI, source readiness, processed/backup/manifest/report roles, storage budget, removable-drive readiness, and CLI JSON contract. |

The script reuses:

- `KM_IDSystem/scripts/check_storage_budget.py` for internal disk, planned
  output, and external-root budget states;
- through STAGE-009, `KM_IDSystem/scripts/check_removable_drive_state.py` and
  `KM_IDSystem/scripts/detect_ids_data_root.py` for removable-drive and
  top-level-only root readiness.

It does not start Docker, backend, frontend, workers, OCR, Embedding, indexing,
cleanup, backup, manifest generation, or report export.

## State Contract

| State | Trigger | Safe mode |
|---|---|---|
| `PATH_CONTRACT_OK` | Source URI is a normalized local `file://` URI, source path is readable, output roles are declared safely, and root/storage budget prerequisites are clear. | no |
| `SOURCE_URI_INVALID` | Source URI is missing, not `file://`, remote, pathless, or not normalized to an absolute local path. | yes |
| `SOURCE_PATH_NOT_READY` | Source path is absent/unreadable or the required removable-drive/root state is not ready. | yes |
| `PROCESSED_PATH_UNBOUNDED` | Processed path is missing/relative/inside unsafe roots, or storage budget blocks derived output. | yes |
| `BACKUP_PATH_UNSAFE` | Backup path is missing/relative/inside source or `IDS_DATA_ROOT`, or would duplicate raw material into an unsafe location. | yes |
| `MANIFEST_PATH_UNSAFE` | Manifest path is missing/relative/inside unsafe roots, or is not a small `.json`/`.jsonl` metadata file. | yes |
| `REPORT_EXPORT_PATH_UNSAFE` | Report export path is missing/relative/inside unsafe roots, or cannot be bounded before export. | yes |
| `PATH_CONTRACT_UNKNOWN` | Path readiness cannot be classified from available inputs. | yes |

Storage states from STAGE-009 are mapped into path-contract states rather than
starting any data-moving workflow. `EXTERNAL_ROOT_NOT_READY` maps to
`SOURCE_PATH_NOT_READY`; budget-blocked or unbounded-output states map to
`PROCESSED_PATH_UNBOUNDED`.

## TDD Evidence

Focused test file:

`KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py`

RED command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py
```

RED result:

- `FAILED (failures=6)`
- expected failure reason: missing
  `KM_IDSystem/scripts/check_local_path_contract.py`

GREEN command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py
```

GREEN result:

- `Ran 6 tests in 0.086s`
- `OK`

## Safety Boundaries

The Phase 2 implementation returns these guard fields as true:

- `does_not_start_services`
- `does_not_create_ids_data_root`
- `does_not_scan_recursively`
- `does_not_scan_external_drive_contents`
- `does_not_open_source_files`
- `does_not_hash_source_files`
- `does_not_generate_outputs`
- `does_not_write_runtime_data`
- `does_not_write_manifests`
- `does_not_copy_backups`

Safe mode pauses:

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

## Manual CLI Smoke

Bounded preflight command:

```bash
python3 -B KM_IDSystem/scripts/check_local_path_contract.py \
  --source-uri file:///tmp/ids-stage010-source.csv \
  --processed-path /tmp/ids-stage010-derived/processed \
  --backup-path /tmp/ids-stage010-backups/raw-backup \
  --manifest-path /tmp/ids-stage010-metadata/manifest.json \
  --report-export-path /tmp/ids-stage010-exports/report.pdf \
  --internal-total-gib 1000 \
  --internal-free-gib 300 \
  --planned-output-gib 20 \
  --no-require-external-root
```

The focused tests run an equivalent CLI smoke against a temporary source file.
Expected result: `state=PATH_CONTRACT_OK`, `safe_mode=false`,
`customer_visible=false`, `bounded_preflight_only=true`, and all no-write,
no-scan, no-output, no-manifest, and no-backup flags true.

## Validation Plan

Fresh Phase 2 validation should include:

- focused STAGE-010 unittest;
- STAGE-007/008/009 regression unittests;
- Stage 010 CLI smoke;
- Python syntax check for the new script;
- `check-render --project KM_IDSystem`;
- STAGE-010 Phase 2 marker, roadmap, batch lock, and JSONL check;
- changed-scope check;
- `git diff --check`;
- semantic governance validate as a sparse-worktree diagnostic only.

## Final Validation Results

Fresh validation for this phase used the bundled Codex Python runtime.

| Check | Result |
|---|---|
| STAGE-010 focused unittest | `Ran 6 tests in 0.093s` / `OK` |
| STAGE-007/008/009 regression unittests | `Ran 18 tests in 0.461s` / `OK` |
| Python syntax check | `py_compile` exit 0 |
| Stage 010 CLI smoke | `state=PATH_CONTRACT_OK`, `storage_budget_state=BUDGET_OK`, `safe_mode=false`, no derived paths created |
| Owner render check | `drift_count=0`, `reference_issue_count=0` |
| Marker / scope / JSONL check | marker, Phase 2 task ID, event ID, batch lock, next gate, completed hours, and changed scope all matched |
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

## Out Of Scope

Phase 2 does not:

- validate the full online/offline/reconnected/permission/path-changed matrix
  reserved for Phase 3;
- create or repair external-drive `00-99` directories;
- inspect or hash real raw material files;
- recursively scan external-drive contents;
- create processed, backup, manifest, report, runtime, OCR, Embedding, or index
  outputs;
- expose local path-machine diagnostics in customer-visible flows;
- push to GitHub, open a PR, merge, or enter Phase 3.

## Rollback

Rollback Phase 2 by reverting:

- `KM_IDSystem/scripts/check_local_path_contract.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py`
- this evidence file
- the STAGE-010 Phase 2 roadmap, batch-lock, events, and rendered owner-entry
  updates.

No runtime data, generated report, dependency folder, external-drive write,
manifest cleanup, backup cleanup, service restart, or GitHub PR cleanup is
required because Phase 2 creates no runtime or external-drive artifacts.

## Decision

STAGE-010 Phase 2 is locally complete when the focused unittest, regression
tests, CLI smoke, syntax check, owner render check, marker/scope/JSONL check,
and diff check pass. Phase 3 may validate the broader exception matrix only in
a later run.
