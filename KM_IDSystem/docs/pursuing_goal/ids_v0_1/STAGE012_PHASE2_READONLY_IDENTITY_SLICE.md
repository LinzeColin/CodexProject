# IDS v0.1 STAGE-012 Phase 2 Read-Only Identity Slice

## Identity

- Stage: `STAGE-012`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE012-P2`
- Acceptance ID: `ACC-STAGE-012`
- Stage title: `原始资料只读合同`
- Recorded at UTC: `2026-07-02T12:21:19Z`

## Goal

Implement the smallest runnable original-material identity slice before any
database, manifest-file, import, index, OCR, Embedding, backup, report, or UI
integration.

This phase implements metadata-only read-only identity capture for explicit
`file://` source URIs. It computes `sha256`, `file_size`, `mtime`, and
`first_seen_at` for an explicitly supplied file, deduplicates repeated input
within the report, and records abnormal input as explicit states.

Marker: `STAGE012_PHASE2_READONLY_IDENTITY_SLICE_NO_DB_NO_MANIFEST_WRITE_NO_PHASE3`.

## Implemented Slice

Implementation file:

- `KM_IDSystem/scripts/check_original_raw_identity.py`

Focused test file:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py`

The implementation intentionally stays narrow:

- accepts only explicit `file://` source URIs supplied by the caller;
- refuses non-local URI schemes and directories;
- blocks `/Users/linzezhang/Downloads/IDS_MetaData` paths before reading or
  hashing;
- computes file identity metadata only for explicit readable files;
- returns records in memory/stdout JSON only;
- does not write manifest files, databases, document rows, chunk rows, job
  rows, evidence ledgers, audit logs, reports, caches, indexes, OCR output,
  Embedding output, or backup payloads;
- does not recursively scan source directories;
- does not move, delete, overwrite, compact, normalize, rename, or repair
  original files.

## Test Data Boundary

Focused tests use the tracked governance contract
`KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md` as the
real file input. This is repository source evidence, not fabricated IDS
business data and not a raw metadata database payload.

The tests do not create fake IDS business records, fake database rows, fake
source documents, placeholder corpora, or fabricated evidence.

No command listed, opened, hashed, copied, moved, deleted, modified, dumped, or
scanned `/Users/linzezhang/Downloads/IDS_MetaData` content in this phase.

## Runtime Contract

The JSON report has:

- `schema_version=ids.stage012.original_raw_identity.v1`
- `stage=STAGE-012`
- `phase=Phase 2`
- `acceptance_id=ACC-STAGE-012`
- `entrance=IDS 系统运营入口`
- `overall_state`
- `records`
- `record_count`
- `manifest_record_count`
- `duplicate_input_count`
- `error_count`
- no-side-effect flags

Successful records include:

- `source_uri`
- `source_path`
- `sha256`
- `file_size`
- `mtime`
- `first_seen_at`
- `state=ORIGINAL_RAW_READY`

The report excludes raw payload content. It is a metadata-only preflight and
not a manifest-file write.

## Status Contract

Implemented states:

| State | Meaning | Phase 2 behavior |
|---|---|---|
| `ORIGINAL_RAW_READY` | Explicit file URI was readable and identity metadata was captured. | Return metadata-only record. |
| `ORIGINAL_RAW_NOT_CONFIGURED` | No source URI was provided. | Return failure state without side effects. |
| `ORIGINAL_RAW_PATH_BLOCKED` | URI/path is missing, unsafe, non-local, absent, a directory, or inside blocked IDS_MetaData raw metadata root. | Return explicit failure record; do not hash or read payload. |
| `ORIGINAL_RAW_READ_BLOCKED` | File exists but cannot be read by the process. | Return explicit failure record; do not skip silently. |

Future Phase 3 may add scenario evidence for same-name/different-hash and
same-hash/different-path cases. Phase 2 only proves the minimal explicit-file
identity path and repeated-input idempotency.

## Idempotency Evidence

Repeated `source_uri` input for the same file and same hash produces one
manifest candidate record and increments `duplicate_input_count`. It does not
create duplicate document, chunk, job, manifest, evidence, or audit rows because
this phase has no persistence adapter.

## Validation Results

Final local validation for this run:

- Stage012 focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py -q`
  failed as expected because `check_original_raw_identity.py` did not exist.
- Stage012 focused GREEN:
  the same command returned `Ran 4 tests ... OK`.
- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected because `IDS-V0_1-STAGE012-P2`, the new script, and the
  focused test were not yet allowed.
- Stage005 governance GREEN:
  the same command returned `Ran 13 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 57 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_original_raw_identity.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- CLI smoke:
  `check_original_raw_identity.py --source-uri STAGE012_ENTRY_CONTRACT.md --first-seen-at 2026-07-02T12:25:00Z`
  returned `overall_state=ORIGINAL_RAW_READY`, `record_count=1`,
  `manifest_record_count=1`, `error_count=0`, and all no-side-effect flags
  true.
- `scripts/lean_governance.py check-render --project KM_IDSystem` returned
  `drift_count=0`.
- `git diff --check` returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem` returned exit
  code `1` with 29 known sparse/root/registered-project diagnostics and no
  `KM_IDSystem` project regression.

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
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 3.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE012-P2` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, or app-entry reinstall
because Phase 2 writes only tracked code, tests, and governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
