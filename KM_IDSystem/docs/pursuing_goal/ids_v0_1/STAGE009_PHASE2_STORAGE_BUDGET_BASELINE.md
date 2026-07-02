# IDS v0.1 STAGE-009 Phase 2 Storage Budget Baseline

## Identity

- Stage: `STAGE-009`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE009-P2`
- Acceptance ID: `ACC-STAGE-009`
- Stage title: `存储预算基线`
- Recorded at UTC: `2026-07-02T09:10:22Z`

## Goal

Implement the smallest read-only storage-budget slice allowed by Phase 1:

- classify internal storage budget as `BUDGET_OK`, `BUDGET_WARN`,
  `BUDGET_BLOCKED_LOW_FREE`, `BUDGET_BLOCKED_HIGH_WATERLINE`, or
  `BUDGET_UNKNOWN`;
- compose STAGE-008 removable-drive state as `EXTERNAL_ROOT_NOT_READY` when
  a cold-data job requires `IDS_DATA_ROOT`;
- block `UNBOUNDED_OUTPUT_RISK` before OCR, Embedding, index rebuild,
  cleanup, or batch report generation can create derived output;
- expose machine diagnostics only through `IDS 系统运营入口`;
- keep the customer flow hidden from storage-machine details.

Marker: `STAGE009_PHASE2_STORAGE_BUDGET_BASELINE_READ_ONLY_NO_PHASE3`.

## Implemented Slice

| Artifact | Purpose |
|---|---|
| `KM_IDSystem/scripts/check_storage_budget.py` | Read-only Stage 009 storage-budget preflight and JSON CLI. |
| `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py` | Unit tests for OK/WARN/BLOCKED/UNKNOWN, unbounded output, external-root readiness, and CLI JSON contract. |

The script reuses:

- `KM_IDSystem/scripts/detect_ids_data_root.py` for internal storage guard
  classification;
- `KM_IDSystem/scripts/check_removable_drive_state.py` for top-level-only
  removable-drive state checks.

It does not start Docker, backend, frontend, workers, OCR, Embedding, indexing,
cleanup, or report generation.

## State Contract

| State | Trigger | Safe mode |
|---|---|---|
| `BUDGET_OK` | Free space is above warning threshold and used percent is below high-waterline. | no |
| `BUDGET_WARN` | Free space is above hard minimum but below warning threshold, without crossing the high-waterline. | no; large jobs require review |
| `BUDGET_BLOCKED_LOW_FREE` | Free space is below hard minimum. | yes |
| `BUDGET_BLOCKED_HIGH_WATERLINE` | Used percent is at or above configured high-waterline. | yes |
| `BUDGET_UNKNOWN` | Internal storage cannot be classified from provided checks and fallback is disabled. | yes |
| `EXTERNAL_ROOT_NOT_READY` | A cold-data job requires `IDS_DATA_ROOT`, but STAGE-008 does not return `ONLINE_VALIDATED`. | yes |
| `UNBOUNDED_OUTPUT_RISK` | A derived-output job has no declared output budget or would cross the hard minimum after planned output. | yes |

Default thresholds remain:

- `internal_min_free_gib`: `100`
- `internal_warn_free_gib`: `200`
- `internal_max_used_percent`: `85`
- `external_cold_root_nominal_tb`: `5`
- `internal_budget_label_gb`: `800`

## TDD Evidence

RED command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py
```

RED result:

- `FAILED (failures=4)`
- expected failure reason: missing
  `KM_IDSystem/scripts/check_storage_budget.py`

GREEN command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py
```

GREEN result:

- `Ran 4 tests in 0.076s`
- `OK`

## Safety Boundaries

The Phase 2 implementation returns these guard fields as true:

- `does_not_start_services`
- `does_not_create_ids_data_root`
- `does_not_scan_recursively`
- `does_not_scan_external_drive_contents`
- `does_not_generate_outputs`
- `does_not_write_runtime_data`

Safe mode pauses:

- `bulk_import`
- `recursive_directory_scanning`
- `raw_material_cleanup`
- `ocr`
- `embedding`
- `index_rebuild`
- `batch_report_generation`

## Manual CLI Smoke

Bounded preflight command:

```bash
python3 -B KM_IDSystem/scripts/check_storage_budget.py \
  --internal-total-gib 1000 \
  --internal-free-gib 300 \
  --planned-output-gib 20 \
  --job-kind bounded_preflight \
  --no-require-external-root
```

Expected result: `state=BUDGET_OK`, `safe_mode=false`,
`customer_visible=false`, and all no-write/no-scan/no-output flags true.

Fresh observed result:

- `state`: `BUDGET_OK`
- `safe_mode`: `false`
- `customer_visible`: `false`
- `bounded_preflight_only`: `true`
- `does_not_create_ids_data_root`: `true`
- `does_not_scan_external_drive_contents`: `true`
- `does_not_generate_outputs`: `true`
- `does_not_write_runtime_data`: `true`

## Final Validation Results

| Check | Result |
|---|---|
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py` | `Ran 4 tests`, `OK` |
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py` | `Ran 7 tests`, `OK` |
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py` | `Ran 6 tests`, `OK` |
| Stage 009 CLI smoke | `state=BUDGET_OK`, no-write/no-scan/no-output flags true |
| `check-render --project KM_IDSystem` | `drift_count=0`, `reference_issue_count=0` |
| STAGE-009 Phase 2 marker, roadmap, batch lock, and JSONL check | all expected markers found |
| `changed-scope` | selected only `KM_IDSystem`, unknown changed files empty |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

## Out Of Scope

Phase 2 does not:

- validate all exception scenarios for Phase 3;
- create or repair external-drive `00-99` directories;
- inspect real raw material files;
- recursively scan external-drive contents;
- write local data, reports, outputs, indexes, OCR outputs, or embeddings;
- expose storage-machine diagnostics in customer-visible flows;
- push to GitHub, open a PR, or merge to `main`.

## Rollback

Rollback Phase 2 by reverting:

- `KM_IDSystem/scripts/check_storage_budget.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py`
- this evidence file
- the STAGE-009 Phase 2 roadmap, batch-lock, events, and rendered owner-entry updates.

No runtime data, generated report, dependency folder, external-drive write, or
service cleanup is required.
