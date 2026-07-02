# IDS v0.1 STAGE-016 Phase 2 Import Idempotency Slice

## Identity

- Stage: `STAGE-016`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE016-P2`
- Acceptance ID: `ACC-STAGE-016`
- Stage title: `导入幂等键`
- Recorded at UTC: `2026-07-02T15:05:46Z`

## Goal

Implement the minimum metadata-only import-idempotency slice on bounded
explicit inputs, proving that repeated source or batch import attempts do not
duplicate documents, chunks, jobs, or index entries.

Marker: `STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE_NO_DATABASE_NO_INDEX_WRITE_NO_PHASE3`.

## Implemented Slice

Implemented file:

- `KM_IDSystem/scripts/check_import_idempotency.py`

Focused test file:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py`

The slice exposes:

- `evaluate_import_idempotency(...)`
- CLI JSON output through `check_import_idempotency.py`

The implementation inherits:

- STAGE-013 explicit `file://` fingerprint evidence;
- STAGE-014 metadata-only manifest identity;
- STAGE-015 duplicate/conflict/repeated-input detection.

It creates no persistence adapter and writes no database, manifest, document,
chunk, job, index, evidence-ledger, audit-log, report, cache, or runtime output.

## Import Idempotency Contract

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | STAGE-013 fingerprint record |
| `source_path` | normalized local path for the explicit file | STAGE-013 fingerprint record |
| `basename` | source filename for conflict grouping | STAGE-015 duplicate identity |
| `sha256` | exact byte fingerprint inherited from STAGE-013 | STAGE-013 fingerprint record |
| `file_size` | byte length mapped from fingerprint evidence | STAGE-013 fingerprint record |
| `mtime` | filesystem modification time at fingerprint time | STAGE-013 fingerprint record |
| `first_seen_at` | first observation timestamp | STAGE-013 fingerprint record |
| `manifest_identity` | metadata-only manifest identity | STAGE-014 manifest contract |
| `duplicate_state` | duplicate/conflict classification | STAGE-015 duplicate report |
| `import_idempotency_key` | deterministic `ids-import-file-sha256-{sha256}` key | STAGE-016 import-idempotency slice |
| `batch_idempotency_key` | optional deterministic key for an approved batch identity and bounded source identities | STAGE-016 import-idempotency slice |

The key is deterministic for bounded metadata. It is not a production database
primary key, not a migration, and not a persistence write authorization.

## Status Mapping

| Input or inherited state | STAGE-016 state | Required behavior |
|---|---|---|
| ready duplicate identity | `IMPORT_KEY_READY` | key can be compared before future persistence |
| repeated same file input | `IMPORT_SINGLE_REPEAT` | keep document/chunk/job/index/import deltas at zero |
| same hash at different paths | `IMPORT_DUPLICATE_CONTENT` | preserve provenance; do not delete or merge originals |
| same basename with different hash | `IMPORT_KEY_CONFLICT` | stop for review; do not overwrite |
| no approved source evidence | `IMPORT_NOT_CONFIGURED` | fail closed |
| missing, unsafe, non-local, unreadable, or raw metadata source | `IMPORT_SOURCE_BLOCKED` | block before import work |
| missing fingerprint evidence | `IMPORT_FINGERPRINT_MISSING` | do not fabricate hash or size |
| unsafe future write target | `IMPORT_WRITE_BLOCKED` | do not write database, index, evidence, audit, or report records |
| unknown classification | `IMPORT_UNKNOWN` | fail closed |

## No-Persistence Proof

The returned report always keeps these deltas at zero in Phase 2:

- `document_delta`
- `chunk_delta`
- `job_delta`
- `index_delta`
- `import_write_delta`
- `manifest_write_delta`
- `duplicate_write_delta`

The report also carries explicit safety flags:

- `does_not_scan_recursively`
- `does_not_move_originals`
- `does_not_delete_originals`
- `does_not_overwrite_originals`
- `does_not_write_import_records`
- `does_not_write_manifest_files`
- `does_not_write_database`
- `does_not_write_index`
- `does_not_create_documents_chunks_jobs`
- `does_not_read_raw_metadata`
- `does_not_call_external_apis`

## Focused Scenarios Covered

Focused tests cover:

1. explicit local file URI generates a metadata-only import key;
2. repeated single-file import returns `IMPORT_SINGLE_REPEAT` with zero
   persistence deltas;
3. same hash at different paths preserves provenance without merge/delete;
4. same basename with different hash becomes `IMPORT_KEY_CONFLICT`;
5. missing file becomes `IMPORT_SOURCE_BLOCKED` and is not silently skipped;
6. `IDS_MetaData` raw metadata root path is blocked before import read;
7. CLI JSON output exposes the Stage 016 metadata-only contract.

The tests use tracked governance documents as real repository source evidence
and temporary process-owned copies only for structural duplicate/conflict
scenarios. They do not use fake IDS business data, fake database rows, fake
source documents, placeholder corpora, or fabricated evidence.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, duplicate-detection, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, persisted manifests, duplicate ledgers, evidence ledgers,
  document rows, chunk rows, job rows, index rows, OCR output, Embedding
  output, cache files, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 3.

## Validation Results

Final local validation for this run:

- Stage016 focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py -q`
  failed as expected with `Ran 7 tests ... FAILED (failures=7)` because
  `check_import_idempotency.py` did not exist.
- Stage016 focused GREEN:
  the same command returned exit code `0` with `Ran 7 tests` and `OK`.
- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 29 tests ... FAILED (failures=4)` because
  `IDS-V0_1-STAGE016-P2`, the new focused test, and the new script path were
  not yet accepted.
- Stage005 governance intermediate RED:
  the same command then failed with `Ran 29 tests ... FAILED (failures=1)`
  because `STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md` did not yet exist as
  required evidence.
- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 29 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 101 tests` and `OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_import_idempotency.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- Events JSONL parse returned `events_jsonl_ok`.
- Owner render:
  `python3 -B scripts/lean_governance.py render --project KM_IDSystem --write`
  updated `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned exit code `0`, `drift_count=0`, and `reference_issue_count=0`.
- `git diff --check`:
  returned exit code `0`.
- Semantic governance diagnostic:
  `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned exit code `1` with 29 known sparse-worktree/root or
  registered-project missing-path diagnostics and no new `KM_IDSystem`
  semantic error.
- Marker scan:
  exact old underscored task-id variant scan returned no hits; legacy path/name
  scan still returns only historical migration-policy, compatibility-scan,
  stale-path, or do-not-revive references.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE016-P2` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, import-record cleanup, index cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, GitHub cleanup, or app-entry reinstall because Phase 2 writes only
tracked source/test/governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
