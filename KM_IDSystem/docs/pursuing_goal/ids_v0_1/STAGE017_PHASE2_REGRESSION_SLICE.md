# IDS v0.1 STAGE-017 Phase 2 Regression Slice

## Identity

- Stage: `STAGE-017`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE017-P2`
- Acceptance ID: `ACC-STAGE-017`
- Stage title: `原始资料回归测试`
- Recorded at UTC: `2026-07-02T19:23:34Z`

## Goal

Implement a minimum metadata-only regression preflight for original-material
handling on bounded explicit inputs. The slice verifies repeated scan, resume
checkpoint, offline-drive, hash-drift, and blocked-source behavior without
directory scanning, raw metadata reads, or persistence writes.

Marker: `STAGE017_PHASE2_REGRESSION_SLICE_METADATA_ONLY_NO_PHASE3`.

## Implementation

New helper:

- `KM_IDSystem/scripts/check_original_regression.py`

Focused tests:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage017_original_regression.py`

The helper exposes:

- Python API:
  `evaluate_original_material_regression(...)`
- CLI:
  `python KM_IDSystem/scripts/check_original_regression.py --source-uri file:///...`

The helper delegates file identity, manifest identity, duplicate recognition,
and import idempotency to the completed Stage 013 through Stage 016
metadata-only preflight stack. It then maps those results into Stage 017
regression states and adds resume/offline-drive regression controls.

## Input Boundary

Allowed Phase 2 inputs:

- explicit local `file://` source URIs;
- metadata-only `resume_checkpoint` dictionaries created by this helper;
- scalar timestamps such as `first_seen_at` and `scan_checked_at`;
- scalar `drive_state` values such as `online` or `offline`.

Forbidden Phase 2 inputs:

- directory discovery;
- recursive scan roots;
- raw metadata database roots;
- real business corpus dumps;
- database row exports;
- secrets, credentials, or cloud tokens;
- generated runtime manifests, reports, outputs, or caches.

## Output Contract

The helper returns a JSON-serializable report with these core fields:

| Field | Meaning |
|---|---|
| `schema_version` | `ids.stage017.original_regression.v1` |
| `overall_state` | Stage 017 regression state |
| `regression_records` | metadata-only records derived from explicit source identity |
| `rejected_inputs` | explicit failure states with reason text |
| `checkpoint_candidates` | metadata-only resume checkpoint candidates |
| `checkpoint_comparison` | resume/checkpoint mismatch details |
| `duplicate_registration_blocked_count` | repeated or duplicate registration attempts blocked before writes |
| `hash_drift_count` | checkpoint/source identity drift count |
| `document_delta` through `database_write_delta` | always `0` in this Phase 2 slice |

No raw file payload, raw metadata database content, business record, table row,
or generated runtime artifact is embedded in the report.

## State Mapping

| Source condition | Stage 017 state |
|---|---|
| explicit file identity is ready | `REGRESSION_READY` |
| repeated same file input | `REGRESSION_REPEAT_SCAN` |
| same-hash/different-path or same-name/different-hash import conflict | `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` |
| missing, unsafe, non-local, or raw metadata source | `REGRESSION_SOURCE_BLOCKED` |
| no source URI | `REGRESSION_NOT_CONFIGURED` |
| resume requested without checkpoint | `REGRESSION_CHECKPOINT_MISSING` |
| matching checkpoint and resume token | `REGRESSION_RESUME_PENDING` |
| offline or disconnected drive state | `REGRESSION_DRIVE_OFFLINE` |
| checkpoint/source identity mismatch | `REGRESSION_HASH_DRIFT` |
| proposed persistence/report/audit/index write outside gate | `REGRESSION_WRITE_BLOCKED` |
| incomplete classification | `REGRESSION_UNKNOWN` |

## No-Pollution Guarantees

The Phase 2 report keeps these deltas at `0`:

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

The helper also records these no-side-effect flags as true:

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

## Covered Phase 2 Behaviors

Focused tests cover:

1. Explicit `file://` source creates one metadata-only regression record.
2. Repeated scan of the same file becomes `REGRESSION_REPEAT_SCAN` and blocks
   duplicate registration with zero write deltas.
3. Resume with a matching checkpoint becomes `REGRESSION_RESUME_PENDING`.
4. Resume without checkpoint fails closed as `REGRESSION_CHECKPOINT_MISSING`
   before Stage 016 source evaluation.
5. Offline drive state fails closed as `REGRESSION_DRIVE_OFFLINE` before source
   identity evaluation.
6. Checkpoint/source identity mismatch becomes `REGRESSION_HASH_DRIFT`.
7. `IDS_MetaData` raw metadata paths are blocked before regression reads.
8. CLI JSON output uses Stage 017 Phase 2 identity and remains metadata-only.

The tests use tracked governance documents as real repository source evidence
and scalar test harness values for checkpoint comparison. They do not create or
present fake IDS business data, fake database rows, fake source documents, or
fabricated evidence.

## Validation Results

Final validation completed in this Phase 2 run:

- Focused Stage017 RED failed as expected with `Ran 8 tests ... FAILED
  (failures=8)` because `check_original_regression.py` did not exist.
- Focused Stage017 GREEN passed 8 tests after implementing the metadata-only
  regression preflight.
- Stage005 RED failed as expected with `Ran 33 tests ... FAILED
  (failures=4)` because `IDS-V0_1-STAGE017-P2`, the Stage017 focused test, and
  the Stage017 helper script were not yet accepted by the governance state
  machine/path policy.
- Stage005 intermediate RED failed as expected with `Ran 33 tests ... FAILED
  (failures=1)` because this Phase 2 evidence file was missing as required
  evidence.
- Stage005 GREEN passed 33 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 114 tests.
- `py_compile` passed for `check_original_regression.py` and the Stage005
  validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- Legacy path/name scan found only existing historical migration-policy,
  stale-path, do-not-revive, or scanner-rule references; this Phase 2 document
  does not add new legacy path literals.
- semantic validate remains diagnostic-only with 29 known sparse root-governance
  or registered-project missing paths and no new `KM_IDSystem` semantic error.
- Phase 2 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No service start, dependency install, production scanner, manifest/database/
  index/import writer, document/chunk/job creation, runtime output, external
  API call, GitHub upload, PR, merge, app reinstall, or Phase 3 work was
  performed.

## Stop Conditions Preserved

This Phase 2 slice must stop if a future change would:

- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- scan directories or discover files from an unbounded root;
- write runtime database rows, manifests, indexes, import records, evidence
  ledgers, audit logs, reports, outputs, caches, document rows, chunk rows, or
  job rows;
- use fake IDS business data or fabricated evidence;
- enter Phase 3 validation scenarios in the same run;
- push to GitHub before the STAGE-011..020 batch gate allows upload.

## Rollback

Revert `check_original_regression.py`, its focused test, this evidence file,
Stage005 validator/test updates, batch-lock, roadmap/event, and rendered owner
files only. Do not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, persisted manifests, evidence
ledgers, audit logs, indexes, delivered reports, runtime data, app entries,
GitHub state, or Phase 3.
