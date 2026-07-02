# IDS v0.1 STAGE-017 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-017`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE017-P3`
- Acceptance ID: `ACC-STAGE-017`
- Stage title: `原始资料回归测试`
- Recorded at UTC: `2026-07-02T19:33:14Z`

## Goal

Validate original-material regression scenarios for same-file/same-hash,
same-name/different-hash, same-hash/different-path, matching resume checkpoint,
offline drive, checkpoint hash drift, duplicate import no-persistence, and
original hash stability.

Marker: `STAGE017_PHASE3_SCENARIO_VALIDATION_NO_PHASE4_NO_GITHUB_UPLOAD`.

## Implemented Validation Surface

The existing Phase 2 helper now exposes:

- `build_stage017_scenario_report(...)`

The scenario report returns:

- `schema_version: ids.stage017.original_regression_scenarios.v1`
- `stage: STAGE-017`
- `phase: Phase 3`
- `acceptance_id: ACC-STAGE-017`
- `overall_valid`
- `scenarios`
- no-side-effect flags inherited from Phase 2

The report does not embed raw file payloads, raw metadata database content,
business records, table rows, generated reports, runtime outputs, credentials,
or derived dumps.

## Scenario Coverage

| Scenario | Expected state | Validation meaning |
|---|---|---|
| `same_file_same_hash` | `REGRESSION_REPEAT_SCAN` | repeated scan of the same explicit file collapses to one identity and one duplicate input |
| `same_name_different_hash` | `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | same basename with different content is a conflict/version candidate, not an overwrite |
| `same_hash_different_path` | `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | same content at different paths preserves provenance and blocks duplicate registration |
| `matching_resume_checkpoint` | `REGRESSION_RESUME_PENDING` | matching metadata checkpoint and resume token can continue later without persistence writes |
| `offline_drive` | `REGRESSION_DRIVE_OFFLINE` | offline drive fails closed before source identity evaluation |
| `checkpoint_hash_drift` | `REGRESSION_HASH_DRIFT` | checkpoint/source mismatch becomes explicit drift, not silent continuation |
| `duplicate_import_no_persistence` | `REGRESSION_REPEAT_SCAN` | repeated import keeps all persistence deltas at zero |
| `original_hash_stable` | `REGRESSION_HASH_STABLE` | before/after SHA-256 and size for the explicit source remain unchanged |

## No-Persistence Proof

The `duplicate_import_no_persistence` scenario asserts these deltas are `0`:

- `document_delta`
- `chunk_delta`
- `job_delta`
- `index_delta`
- `import_write_delta`
- `manifest_write_delta`
- `duplicate_write_delta`
- `evidence_write_delta`
- `audit_write_delta`
- `report_write_delta`
- `database_write_delta`

The scenario report also keeps these flags true:

- `does_not_scan_recursively`
- `does_not_move_originals`
- `does_not_delete_originals`
- `does_not_overwrite_originals`
- `does_not_write_manifest_files`
- `does_not_write_database`
- `does_not_write_index`
- `does_not_create_documents_chunks_jobs`
- `does_not_read_raw_metadata`
- `does_not_call_external_apis`

## Real-Data Boundary

The focused tests use tracked governance documents as real repository source
evidence. Same-name/different-hash and same-hash/different-path cases use
temporary process-owned copies only to create structural filename/path
conditions. Those copies are not committed, are not IDS business corpus, and
are not presented as business evidence.

No fake IDS business data, fake database rows, fake source documents,
placeholder corpora, or fabricated evidence are used.

## Raw Metadata Boundary

Phase 3 did not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit `/Users/linzezhang/Downloads/IDS_MetaData` content. Raw metadata
paths remain blocked by Stage 013 through Stage 017 tests before any source
identity or regression read.

## Validation Results

Final validation completed in this Phase 3 run:

- Focused Stage017 RED failed as expected with `Ran 9 tests ... FAILED
  (errors=1)` because `build_stage017_scenario_report` did not exist.
- Focused Stage017 GREEN passed 9 tests after adding the scenario report.
- Stage005 RED failed as expected with `Ran 34 tests ... FAILED
  (failures=1)` because `IDS-V0_1-STAGE017-P3` was not yet accepted by the
  governance state machine.
- Stage005 intermediate RED failed as expected with `Ran 34 tests ... FAILED
  (failures=1)` because this Phase 3 evidence file was missing as required
  evidence.
- Stage005 GREEN passed 34 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 116 tests.
- `py_compile` passed for `check_original_regression.py` and the Stage005
  validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- Legacy path/name scan found only existing historical migration-policy,
  stale-path, do-not-revive, or scanner-rule references; this Phase 3 document
  does not add new legacy path literals.
- semantic validate remains diagnostic-only with 29 known sparse root-governance
  or registered-project missing paths and no new `KM_IDSystem` semantic error.
- Phase 3 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No service start, dependency install, production scanner, manifest/database/
  index/import writer, document/chunk/job creation, runtime output, external
  API call, GitHub upload, PR, merge, app reinstall, or Phase 4 work was
  performed.

## Stop Conditions Preserved

Stop immediately if a future change would:

- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit raw
  metadata database content;
- scan directories or discover files from an unbounded root;
- write runtime database rows, manifests, indexes, import records, evidence
  ledgers, audit logs, reports, outputs, caches, document rows, chunk rows, or
  job rows;
- use fake IDS business data or fabricated evidence;
- enter Phase 4 closeout in the same run;
- push to GitHub before the STAGE-011..020 batch gate allows upload.

## Rollback

Revert the Stage017 scenario-report helper changes, focused test additions,
this evidence file, Stage005 validator/test updates, batch-lock, roadmap/event,
and rendered owner files only. Do not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, persisted manifests, evidence
ledgers, audit logs, indexes, delivered reports, runtime data, app entries,
GitHub state, or Phase 4.
