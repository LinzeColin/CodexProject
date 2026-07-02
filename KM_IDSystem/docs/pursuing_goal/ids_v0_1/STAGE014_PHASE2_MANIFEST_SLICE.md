# IDS v0.1 STAGE-014 Phase 2 Manifest Slice

## Identity

- Stage: `STAGE-014`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE014-P2`
- Acceptance ID: `ACC-STAGE-014`
- Stage title: `Manifest 生成`
- Recorded at UTC: `2026-07-02T13:46:40Z`

## Goal

Implement a minimum metadata-only manifest candidate slice that inherits the
STAGE-013 file-fingerprint preflight and preserves STAGE-012 original-material
read-only rules.

Marker: `STAGE014_PHASE2_MANIFEST_SLICE_NO_WRITES_NO_PHASE3`.

## Implemented Contract

`KM_IDSystem/scripts/check_manifest_generation.py` builds an in-memory manifest
candidate report for explicit local `file://` source URIs.

The slice:

- imports STAGE-013 fingerprint preflight rather than reimplementing raw file
  identity rules;
- maps ready fingerprint records into manifest candidates with `source_uri`,
  `source_path`, `sha256`, `file_size`, `mtime`, `first_seen_at`,
  `manifest_generated_at`, `manifest_state`, and deterministic `manifest_id`;
- keeps repeated same-source manifest generation idempotent;
- records missing, blocked, unreadable, unsafe, or unknown inputs in
  `rejected_inputs` with explicit manifest states;
- reports `document_delta=0`, `chunk_delta=0`, `job_delta=0`, and
  `manifest_write_delta=0`;
- exposes a CLI JSON report for deterministic local validation.

The slice does not write manifest files, database rows, evidence ledger rows,
audit log rows, report files, document rows, chunk rows, or job rows.

## Field Mapping

| STAGE-013 fingerprint field | STAGE-014 manifest candidate field | Rule |
|---|---|---|
| `source_uri` | `source_uri` | Preserve explicit source identity. |
| `source_path` | `source_path` | Preserve normalized local path as metadata only. |
| `sha256` | `sha256` | Inherit exact read-only fingerprint evidence. |
| `file_size` / `size` | `file_size` | Preserve byte count without creating a second fact. |
| `mtime` | `mtime` | Preserve observed modification time. |
| `first_seen_at` | `first_seen_at` | Preserve first evidence timestamp. |
| `sha256` | `manifest_id` | Use deterministic `ids-manifest-sha256-{sha256}`. |

## State Mapping

| Fingerprint state | Manifest state | Behavior |
|---|---|---|
| `FINGERPRINT_READY` | `MANIFEST_READY` | Add one metadata-only manifest candidate. |
| `FINGERPRINT_NOT_CONFIGURED` | `MANIFEST_NOT_CONFIGURED` | Fail closed. |
| `FINGERPRINT_PATH_BLOCKED` | `MANIFEST_SOURCE_BLOCKED` | Reject before manifest work. |
| `FINGERPRINT_READ_BLOCKED` | `MANIFEST_SOURCE_BLOCKED` | Reject before manifest work. |
| `FINGERPRINT_HASH_CONFLICT` | `MANIFEST_HASH_CONFLICT` | Preserve conflict state. |
| `FINGERPRINT_DUPLICATE_CONTENT` | `MANIFEST_DUPLICATE_CONTENT` | Preserve duplicate provenance state. |
| `FINGERPRINT_MANIFEST_UNSAFE` | `MANIFEST_SCHEMA_UNSAFE` | Block manifest write. |
| Other state | `MANIFEST_UNKNOWN` | Fail closed. |

## Real Source Evidence

Focused tests use the tracked governance file
`KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE014_ENTRY_CONTRACT.md` as real
repository source evidence. This is not IDS business data and is not a raw
metadata database payload.

No fake IDS business data, fake database rows, fake source documents,
placeholder corpora, or fabricated evidence were introduced.

## Validation Results

Final local validation for this run:

- STAGE-014 focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py -q`
  failed as expected with `Ran 5 tests ... FAILED (failures=4, errors=1)`
  because `check_manifest_generation.py` did not exist.
- STAGE-014 focused GREEN:
  the same command returned `Ran 5 tests ... OK`.
- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 21 tests ... FAILED (failures=4)` because
  STAGE-014 Phase 2 current state, script/test paths, and changed-scope
  allowance were not yet accepted.
- Stage005 governance GREEN:
  the same command returned `Ran 21 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issues=[]`, `missing_required_files=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 77 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_manifest_generation.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- CLI smoke:
  `check_manifest_generation.py` against `STAGE014_ENTRY_CONTRACT.md` returned
  `overall_state=MANIFEST_READY`, `candidate_count=1`,
  `manifest_write_delta=0`, `document_delta=0`, `chunk_delta=0`, and
  `job_delta=0`.
- Events JSONL parse returned `events_jsonl_ok`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned `drift_count=0`.
- `git diff --check`:
  returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem`:
  returned exit code `1` with 29 known sparse/root/registered-project
  diagnostics and no `KM_IDSystem` project regression.
- Marker scan:
  exact old underscored task-id variant scan returned no hits; legacy path/name
  scan still returns only stale-path, migration, and compatibility-policy
  references.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, persisted manifests, evidence ledgers, document rows, chunk rows,
  job rows, indexes, OCR output, Embedding output, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 3.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE014-P2` commit. Because
Phase 2 writes only tracked source/test/governance files, rollback does not
require data cleanup, schema rollback, service restart, dependency restoration,
manifest cleanup, runtime database cleanup, report cleanup, raw metadata repair,
GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
