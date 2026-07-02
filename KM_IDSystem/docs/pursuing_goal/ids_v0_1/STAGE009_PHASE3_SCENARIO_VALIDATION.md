# IDS v0.1 STAGE-009 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-009`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE009-P3`
- Acceptance ID: `ACC-STAGE-009`
- Stage title: `存储预算基线`
- Recorded at UTC: `2026-07-02T09:17:57Z`

## Goal

Validate the STAGE-009 storage-budget slice across deterministic exception
scenarios without touching real raw material, generating derived output, or
scanning external-drive contents recursively.

Marker: `STAGE009_PHASE3_SCENARIO_VALIDATION_READ_ONLY_NO_PHASE4`.

## Scenario Matrix

Phase 3 adds `build_stage009_scenario_report()` in
`KM_IDSystem/scripts/check_storage_budget.py`. It composes the Phase 2
`evaluate_storage_budget()` behavior into a scenario matrix:

| Scenario | Expected state | Proof target |
|---|---|---|
| `ok` | `BUDGET_OK` | bounded preflight allowed only |
| `warn` | `BUDGET_WARN` | large jobs require operator review |
| `low_free_space` | `BUDGET_BLOCKED_LOW_FREE` | safe mode blocks derived output |
| `high_waterline` | `BUDGET_BLOCKED_HIGH_WATERLINE` | safe mode blocks high-waterline work |
| `unknown` | `BUDGET_UNKNOWN` | fail closed when storage cannot be classified |
| `external_root_not_ready` | `EXTERNAL_ROOT_NOT_READY` | cold-data jobs stay disabled until `IDS_DATA_ROOT` is validated |
| `unbounded_output_missing_cap` | `UNBOUNDED_OUTPUT_RISK` | derived-output job without declared budget is blocked |
| `planned_output_exceeds_budget` | `UNBOUNDED_OUTPUT_RISK` | declared output that would cross the hard minimum is blocked |

The report returns:

- `schema_version=ids.stage009.phase3_scenarios.v1`
- `phase=Phase 3`
- `customer_visible=false`
- `overall_valid=true` only when all expected states, review rules, safe-mode
  pauses, and operations-only flags are true.

## TDD Evidence

RED command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py
```

RED result:

- `FAILED (errors=1)`
- expected failure reason:
  `AttributeError: module 'stage009_storage_budget' has no attribute 'build_stage009_scenario_report'`

GREEN command:

```bash
python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py
```

GREEN result:

- `Ran 5 tests in 0.099s`
- `OK`

## Safety Boundaries

The Phase 3 validation uses temporary directories and synthetic byte counts
only. It does not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, cleanup,
  or report jobs;
- install dependencies or create `.venv`, `node_modules`, `data`, `reports`,
  or `outputs`;
- create real `IDS_DATA_ROOT` or missing `00-99` directories;
- recursively scan external-drive contents;
- write to external-drive content;
- generate OCR, Embedding, index, report, or cleanup output;
- expose machine diagnostics to customer-visible flows;
- push to GitHub, open a PR, merge, or enter Phase 4.

## Validation Plan

Final validation must include:

- Stage009 focused unittest;
- Stage006 environment/storage regression;
- Stage008 removable-drive regression;
- direct scenario report smoke with `overall_valid=true`;
- owner render drift check;
- Phase 3 marker/roadmap/batch/event checks;
- changed-scope and whitespace checks;
- semantic governance diagnostic without expanding unrelated sparse projects.

## Final Validation Results

| Check | Result |
|---|---|
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py` | `Ran 5 tests`, `OK` |
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py` | `Ran 7 tests`, `OK` |
| `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py` | `Ran 6 tests`, `OK` |
| Direct Stage009 scenario smoke | `schema_version=ids.stage009.phase3_scenarios.v1`, `overall_valid=true`, states include `BUDGET_OK`, `BUDGET_WARN`, `BUDGET_BLOCKED_LOW_FREE`, `BUDGET_BLOCKED_HIGH_WATERLINE`, `BUDGET_UNKNOWN`, `EXTERNAL_ROOT_NOT_READY`, and `UNBOUNDED_OUTPUT_RISK` |
| `check-render --project KM_IDSystem` | `drift_count=0`, `reference_issue_count=0` |
| STAGE-009 Phase 3 marker, roadmap, batch lock, and JSONL check | all expected markers found |
| `changed-scope` | selected only `KM_IDSystem`, unknown changed files empty |
| `git diff --check` | passed |
| semantic governance validate | diagnostic-only failure: 28 known sparse-worktree/root errors for omitted root governance schema/test/hook/workflow files and unrelated registered projects |

## Rollback

Rollback Phase 3 by reverting:

- `KM_IDSystem/scripts/check_storage_budget.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py`
- this evidence file
- the STAGE-009 Phase 3 roadmap, batch-lock, events, and rendered owner-entry updates.

No runtime data, generated report, dependency folder, external-drive write, or
service cleanup is required.
