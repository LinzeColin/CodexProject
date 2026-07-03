# STAGE-027 Phase 2 · 解压文件重新入库最小实现

- Stage: `STAGE-027`
- Task: `IDS-V0_1-STAGE027-P2`
- Acceptance: `ACC-STAGE-027`
- Domain: `D05-S004 · 解压文件重新入库`
- Entrance: `IDS 系统运营入口`
- Status: local implementation slice, no GitHub upload, no app reinstall

## Implementation

`KM_IDSystem/scripts/check_reingest_extracted_files.py` provides `build_reingest_extracted_files(...)`.

The helper composes existing v0.1 gates only:

1. `STAGE-026` archive manifest via `build_archive_manifest(...)`.
2. `STAGE-016` import idempotency via `evaluate_import_idempotency(...)`.
3. An in-memory `ids.stage027.reingest_extracted_files.v1` report.

It maps `safe_extracted_entries` to re-ingest records with:

- `archive_manifest_ref`
- `original_archive_ref`
- `safe_extraction_ref`
- `extracted_file_uri`
- `extracted_file_sha256`
- `import_idempotency_key`
- `reingest_idempotency_key`
- `reingest_duplicate_policy`
- `reingest_owner_decision_state`
- `pipeline_stage_states`

## Decision States

- `REINGEST_READY_FOR_IMPORT_QUEUE`: the extracted file has passed hash observation, manifest handoff, dedup handoff, and parser handoff preconditions in the in-memory plan.
- `REINGEST_OWNER_REVIEW_REQUIRED`: duplicate content or key conflict must be reviewed by the owner before any later import queue can be created.
- `REINGEST_BLOCKED`: missing source, raw-root source, rejected input, or no safe extracted entries blocks re-ingest.

The required pipeline remains:

- `hash`
- `manifest`
- `dedup`
- `parser`

## Persistence Boundary

This phase does not create or modify:

- reingest runtime output
- import queue
- database rows
- index rows
- document/chunk/job/import rows
- runtime reports
- evidence ledgers
- audit logs
- production parser output

The returned `no_persistence_deltas` are all zero, and `actual_jobs_started` is zero for `hash`, `manifest`, `dedup`, and `parser`.

## Raw Data Boundary

`/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary.

This phase does not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit IDS_MetaData raw database content.

Focused tests use process-owned temporary structural ZIP fixtures only. Those fixtures are not IDS corpus, database rows, business evidence, raw metadata, committed examples, or user production data.

Fake IDS business data, fake database rows, fake source documents, and fabricated evidence remain forbidden.

## Validation Targets

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage027_reingest_extracted_files -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage027_phase2_reingest_extracted_files_slice -q`
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`

## Stop Line

NO_PHASE3

Do not enter Phase 3, do not run production re-ingest, do not write runtime outputs, do not push to GitHub, do not create or merge a PR, and do not reinstall app entries in this phase.
