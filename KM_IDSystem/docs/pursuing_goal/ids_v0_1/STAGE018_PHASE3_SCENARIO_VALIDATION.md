# IDS v0.1 STAGE-018 Phase 3 Scenario Validation

- task_id: `IDS-V0_1-STAGE018-P3`
- acceptance_id: `ACC-STAGE-018`
- stage: `STAGE-018`
- phase: `Phase 3`
- evidence_time_utc: `2026-07-02T20:18:10Z`
- marker: `STAGE018_PHASE3_SCENARIO_VALIDATION_NO_PHASE4_NO_GITHUB_UPLOAD`

## Goal

Validate the metadata-only import preflight scanner against abnormal and owner-decision scenarios before any closeout evidence is prepared.

This phase remains a scenario validation slice. It does not create production preflight reports, screenshots, runtime outputs, persisted manifests, databases, evidence ledgers, audit logs, indexes, imports, OCR jobs, Embedding jobs, or document/chunk/job rows.

## Scenario Coverage

The focused tests validate:

- `empty_directory`: explicit local empty directory returns `PREFLIGHT_READY` with zero counts.
- `small_directory`: explicit local small directory returns `PREFLIGHT_READY`.
- `large_directory`: 101 copied repository governance documents trigger `PREFLIGHT_LARGE_BATCH` and a split batch plan.
- `offline_drive`: offline drive state fails closed before source metadata evaluation.
- `archive_present`: local archive candidate triggers `PREFLIGHT_ARCHIVE_PRESENT`.
- `insufficient_space`: available-space lower than estimated input bytes triggers `PREFLIGHT_INSUFFICIENT_SPACE`.

The test harness uses tracked repository governance documents as real local source evidence. Temporary structural files are used only for extension/risk classification and are not IDS business data, customer records, database rows, or source corpus.

## Owner Decision Validation

`build_operator_decision_plan(...)` validates owner-facing actions without persistence:

- Save: report is JSON-serializable and requires an owner-selected path; the helper does not persist it.
- Cancel: cancel contract leaves document/chunk/job/index/import/manifest/evidence/audit/report/database deltas at zero.
- Split: large or owner-selected batches can be split into deterministic metadata batches.
- Skip high risk: archive, scanned-document, or unsupported-format candidates can be excluded from the kept-file plan.

## Processing Guard

The scenario report records:

- `actual_parse_jobs_started = 0`
- `actual_ocr_jobs_started = 0`
- `actual_embedding_jobs_started = 0`
- `actual_index_jobs_started = 0`
- `actual_import_jobs_started = 0`

It also carries the Stage018 no-side-effect flags for no recursive scan, no body parsing, no OCR, no Embedding, no index build, no import, no manifest/database/document/chunk/job writes, no raw metadata reads, and no external API calls.

## Raw Data Boundary

This phase does not read, list, hash, open, copy, move, delete, modify, dump, scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content. The raw metadata path remains a recorded local read-only boundary and is blocked before metadata evaluation.

## TDD Evidence

- Stage018 Phase3 RED: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage018_import_preflight` failed with 8 tests and 3 errors because `build_stage018_scenario_report` and `build_operator_decision_plan` did not exist.
- Stage018 Phase3 GREEN: the same command passed 8 tests after adding metadata-only scenario validation helpers.
- Stage005 Phase3 RED: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression` failed with 38 tests and 1 failure because `IDS-V0_1-STAGE018-P3` was not yet accepted by the governance state machine.
- Stage005 intermediate RED: the same command failed with 38 tests and 1 failure because this evidence file and the required Phase3 event were missing.

## Validation Results

- Stage018 focused GREEN: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage018_import_preflight` passed 8 tests.
- Stage005 governance GREEN: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression` passed 38 tests.
- Stage005 validator: `python3 KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py` returned `valid=true`, `issues=[]`, `missing_required_files=[]`, `missing_event_ids=[]`, `event_json_errors=[]`, `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 discover: `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q` passed 128 tests.
- `py_compile` passed for `check_import_preflight.py` and `validate_stage005_governance_regression.py`.
- `events.jsonl` JSON parse returned `events_jsonl_ok`.
- `render --project KM_IDSystem --write` updated three owner files; `check-render --project KM_IDSystem` returned `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- The old underscored v0.1 task-id variant scan returned no hits.
- New Phase3 files did not introduce legacy pre-rename project path spellings.
- `validate --project KM_IDSystem --semantic` remains diagnostic-only with 29 known sparse root-governance or unrelated registered-project missing paths and no `KM_IDSystem` semantic error.

## Rollback

Revert the Phase3 scenario helper additions in `check_import_preflight.py`, Stage018 focused test additions, this evidence file, Stage005 validator/test updates, batch-lock updates, roadmap/event updates, and rendered owner files only. Do not touch original raw data, `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases, manifests, evidence ledgers, audit logs, indexes, reports, app entries, GitHub state, or Phase 4 work.
