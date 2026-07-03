# STAGE-027 Phase 3 · 解压文件重新入库场景验证

- Stage: `STAGE-027`
- Task: `IDS-V0_1-STAGE027-P3`
- Acceptance: `ACC-STAGE-027`
- Domain: `D05-S004 · 解压文件重新入库`
- Entrance: `IDS 系统运营入口`
- Status: local scenario validation, no GitHub upload, no app reinstall

## Validation Helper

`KM_IDSystem/scripts/check_reingest_extracted_files.py` now provides `build_stage027_scenario_report(...)`.

The scenario report schema is `ids.stage027.reingest_extracted_files.scenario_validation.v1`.

It validates the Phase 2 `ids.stage027.reingest_extracted_files.v1` wrapper without creating runtime output, import queues, database rows, indexes, or processing jobs.

## Required Scenarios

- `ready_for_import_queue`: safe extracted file reaches `REINGEST_READY_FOR_IMPORT_QUEUE`.
- `duplicate_content_owner_review`: duplicate extracted content reaches `REINGEST_OWNER_REVIEW_REQUIRED`.
- `missing_source_blocked`: missing archive source reaches `REINGEST_BLOCKED` with `REINGEST_SOURCE_MISSING`.
- `raw_metadata_root_blocked`: `/Users/linzezhang/Downloads/IDS_MetaData` path reaches `REINGEST_BLOCKED` with `REINGEST_SOURCE_BLOCKED_RAW_METADATA_ROOT` before raw access.
- `adapter_owner_review`: owner-approved external adapter case reaches `REINGEST_OWNER_REVIEW_REQUIRED` with `REINGEST_FORMAT_REQUIRES_EXTERNAL_ADAPTER`.

## Validation States

- `REINGEST_SCENARIO_VALIDATION_PASSED`
- `REINGEST_SCENARIO_VALIDATED`
- `REINGEST_READY_FOR_IMPORT_QUEUE`
- `REINGEST_OWNER_REVIEW_REQUIRED`
- `REINGEST_BLOCKED`
- `REINGEST_PIPELINE_VALIDATED`
- `REINGEST_NO_PERSISTENCE_VALIDATED`

The required pipeline remains:

- `hash`
- `manifest`
- `dedup`
- `parser`

`actual_jobs_started` remains zero for every pipeline step.

## Persistence Boundary

The scenario report confirms:

- `no_persistence_deltas` are all zero
- no reingest runtime output
- no import queue
- no database write
- no index write
- no document/chunk/job/import rows
- no parser output
- no OCR, Embedding, index, import, backend, frontend, worker, dependency install, or external API job

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary.

This phase must not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit IDS_MetaData raw database content.

Focused tests use process-owned temporary structural archive fixtures only. Those fixtures are not IDS corpus、database rows、business evidence、raw metadata、committed examples 或 user production data.

中文边界：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容。

Fixture 边界：process-owned temporary structural archive fixtures 不是 IDS corpus、database rows、business evidence、raw metadata、committed examples 或 user production data。

Fake IDS business data, fake database rows, fake source documents, and fabricated evidence remain forbidden.

## Validation Targets

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage027_reingest_extracted_files -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage027_phase3_reingest_scenario_validation -q`
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`

## Stop Line

NO_PHASE4

Do not enter Phase 4, do not close out STAGE-027, do not run production re-ingest, do not write runtime outputs, do not push to GitHub, do not create or merge a PR, and do not reinstall app entries in this phase.
