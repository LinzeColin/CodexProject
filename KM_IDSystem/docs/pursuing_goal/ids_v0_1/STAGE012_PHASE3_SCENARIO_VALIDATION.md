# IDS v0.1 STAGE-012 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-012`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE012-P3`
- Acceptance ID: `ACC-STAGE-012`
- Stage title: `原始资料只读合同`
- Recorded at UTC: `2026-07-02T12:31:22Z`

## Goal

Validate the Phase 2 original-material identity slice against duplicate,
conflict, idempotency, and hash-stability scenarios while preserving the
read-only raw-material contract.

This phase adds scenario validation only. It does not write manifest files,
databases, document rows, chunk rows, job rows, audit ledgers, evidence
ledgers, reports, indexes, OCR output, Embedding output, backup payloads, or
runtime data.

Marker: `STAGE012_PHASE3_SCENARIO_VALIDATION_NO_DB_NO_MANIFEST_WRITE_NO_PHASE4`.

## Implemented Slice

Updated read-only script:

- `KM_IDSystem/scripts/check_original_raw_identity.py`

Updated focused test:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py`

The script now exposes:

- `build_stage012_scenario_report(...)`

The scenario report composes the Phase 2
`evaluate_original_raw_identity(...)` function and caller-supplied explicit
`file://` paths. It returns an in-memory JSON-serializable report only.

## Scenario Matrix

| Scenario | Expected result |
|---|---|
| `same_file_same_hash` | repeated input of the same file keeps one manifest candidate and records one duplicate input |
| `same_name_different_hash` | two explicit files with the same basename and different hashes are classified as `ORIGINAL_RAW_HASH_CONFLICT` |
| `same_hash_different_path` | two explicit files at different paths with the same hash are classified as `ORIGINAL_RAW_DUPLICATE_CONTENT` |
| `duplicate_import_no_persistence` | duplicate import simulation keeps `document_delta=0`, `chunk_delta=0`, and `job_delta=0` |
| `original_hash_stable` | the original explicit source file has the same sha256 and file size before and after scenario evaluation |

## Test Data Boundary

Focused tests use already tracked governance documents as real repository
source evidence:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_PHASE1_SCOPE_BOUNDARY.md`

The test creates temporary structural copies of those tracked documents inside
a process-owned temporary directory to model same-name/different-hash and
same-hash/different-path cases. These temporary copies are not IDS business
records, not fake database rows, not fake customer source documents, not
placeholder corpora, and not committed artifacts.

No command listed, opened, hashed, copied, moved, deleted, modified, dumped, or
scanned `/Users/linzezhang/Downloads/IDS_MetaData` content in this phase.

## No-Side-Effect Guardrails

The scenario report keeps these flags true:

- `does_not_scan_recursively`
- `does_not_move_originals`
- `does_not_delete_originals`
- `does_not_overwrite_originals`
- `does_not_write_manifests`
- `does_not_write_database`
- `does_not_create_documents_chunks_jobs`
- `does_not_read_raw_metadata`
- `does_not_call_external_apis`

## Validation Results

Final local validation for this run:

- Stage012 focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py -q`
  failed as expected before implementation with
  `AttributeError: module 'stage012_original_raw_identity' has no attribute 'build_stage012_scenario_report'`.
- Stage012 focused GREEN:
  the same command returned `Ran 5 tests ... OK`.
- Stage005 governance regression:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned `Ran 14 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 59 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_original_raw_identity.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned `drift_count=0`.
- `git diff --check`:
  returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem`:
  returned exit code `1` with 29 known sparse/root/registered-project
  diagnostics and no `KM_IDSystem` project regression.
- Marker scan:
  the underscored task-id variant was not present; remaining legacy path/name
  hits are stale-path policy references from prior migration evidence.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, manifests, evidence ledgers, document rows, chunk rows, job rows,
  indexes, OCR output, Embedding output, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 4.

## Phase 4 Entry

Phase 4 may close out STAGE-012 with delivery evidence, whole-stage review,
recoverable and non-recoverable identity states, default configuration,
rollback steps, and Chinese owner feedback. It must keep all raw-data,
read-only, no-side-effect, and no-upload guardrails intact until the
STAGE-011..020 batch is complete, reviewed, repaired, and app entries are
reinstalled.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE012-P3` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, or app-entry reinstall
because Phase 3 writes only tracked code, tests, and governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
