# IDS v0.1 STAGE-018 Phase 2 Preflight Slice

- task_id: `IDS-V0_1-STAGE018-P2`
- acceptance_id: `ACC-STAGE-018`
- stage: `STAGE-018`
- phase: `Phase 2`
- evidence_time_utc: `2026-07-02T20:06:52Z`
- marker: `STAGE018_PHASE2_PREFLIGHT_SLICE_NO_PHASE3_NO_GITHUB_UPLOAD`

## Goal

Implement a metadata-only import preflight scanner slice that can estimate file count, total size, format mix, archive candidates, scanned-document candidates, OCR workload, Embedding workload, risk items, cost classes, and priority hints before any batch import.

This phase creates a human-reviewable product entrance result only. It does not authorize production import, OCR, Embedding, index building, report writing, database writes, or manifest persistence.

## Implemented Surface

- `KM_IDSystem/scripts/check_import_preflight.py`
- `evaluate_import_preflight(source_uris=[...], prechecked_at=..., drive_state=..., available_space_bytes=...)`
- CLI: `python3 KM_IDSystem/scripts/check_import_preflight.py --source-uri file:///approved/local/path --prechecked-at ...`
- Focused tests: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage018_import_preflight.py`

## Output Contract

The output schema is `ids.stage018.import_preflight.v1`. The report is designed for `人类产品入口 + IDS 系统运营入口` and includes:

- `file_count_estimate`
- `total_size_bytes_estimate`
- `format_counts`
- `archive_candidate_count`
- `scanned_document_candidate_count`
- `estimated_ocr_units`
- `estimated_embedding_units`
- `risk_items`
- `cost_items`
- `priority_hint`
- `confirmation_required`
- `confirmation_status`

The report also emits zero write deltas for documents, chunks, jobs, indexes, manifests, reports, audit, evidence, import records, and databases.

## States

- `PREFLIGHT_READY`: explicit local source is accessible and no review risks were detected.
- `PREFLIGHT_REVIEW_REQUIRED`: source metadata is accessible, but archive, scanned-document, large-batch, unsupported-format, or space risks need owner review.
- `PREFLIGHT_SOURCE_BLOCKED`: source URI is invalid, remote, absent, unreadable, or points to the local raw metadata root.
- `PREFLIGHT_DRIVE_OFFLINE`: removable or source drive is offline, disconnected, missing, or unavailable.
- `PREFLIGHT_NOT_CONFIGURED`: no source URI was supplied.

## No-Side-Effect Boundary

Phase 2 sets and tests these no-side-effect flags:

- `does_not_scan_recursively`
- `does_not_parse_body_text`
- `does_not_start_ocr`
- `does_not_create_embeddings`
- `does_not_build_index`
- `does_not_start_import`
- `does_not_write_manifest_files`
- `does_not_write_database`
- `does_not_create_documents_chunks_jobs`
- `does_not_read_raw_metadata`
- `does_not_call_external_apis`

The implementation only evaluates explicit local `file://` file or directory roots. Directory handling is immediate-child metadata only and does not recurse.

## Real Data Boundary

Focused tests copy tracked governance documents already in this repository as real source evidence. Temporary `.zip` and `.png` files are structural test-harness candidates used only to exercise extension, size, archive, and scanned-document classification. They are not IDS business records, database rows, source corpus, analytics inputs, or customer evidence.

The phase does not read, list, hash, open, copy, move, delete, modify, dump, scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content. That local path remains recorded only as a read-only raw database boundary.

## TDD Evidence

- Stage018 RED: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage018_import_preflight` initially failed with 5 tests, 4 failures, and 1 error because `KM_IDSystem/scripts/check_import_preflight.py` did not exist.
- Stage018 GREEN: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage018_import_preflight` passed 5 tests after the metadata-only preflight helper was implemented.
- Stage005 RED: Stage005 governance regression failed with 37 tests and 4 failures because `IDS-V0_1-STAGE018-P2` was not yet accepted by the governance state machine and the new Stage018 script/test paths were not allowed.
- Stage005 intermediate RED: Stage005 governance regression then failed with 37 tests and 1 failure because the Phase2 evidence file and required event were still missing.

## Validation Results

- Stage018 focused GREEN: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage018_import_preflight` passed 5 tests.
- Stage005 governance GREEN: `python3 -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression` passed 37 tests.
- Stage005 validator: `python3 KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py` returned `valid=true`, `issues=[]`, `missing_required_files=[]`, `missing_event_ids=[]`, `event_json_errors=[]`, `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 discover: `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q` passed 124 tests.
- `py_compile` passed for `check_import_preflight.py` and `validate_stage005_governance_regression.py`.
- `events.jsonl` JSON parse returned `events_jsonl_ok`.
- `render --project KM_IDSystem --write` updated three owner files; `check-render --project KM_IDSystem` returned `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- The old underscored v0.1 task-id variant scan returned no hits.
- New Phase2 files did not introduce legacy pre-rename project path spellings.
- `validate --project KM_IDSystem --semantic` remains diagnostic-only with 29 known sparse root-governance or unrelated registered-project missing paths and no `KM_IDSystem` semantic error.

## Rollback

Revert `check_import_preflight.py`, `test_stage018_import_preflight.py`, this evidence file, Stage005 validator/test updates, batch-lock updates, roadmap/event updates, and rendered owner files only. Do not touch original raw data, `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases, manifests, evidence ledgers, audit logs, indexes, reports, app entries, GitHub state, or Phase 3 work.
