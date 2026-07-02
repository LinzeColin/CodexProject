# IDS v0.1 STAGE-015 Phase 2 Duplicate Detection Slice

## Identity

- Stage: `STAGE-015`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE015-P2`
- Acceptance ID: `ACC-STAGE-015`
- Stage title: `重复文件检测`
- Recorded at UTC: `2026-07-02T14:26:42Z`

## Goal

Implement a minimum duplicate-file detection slice for bounded explicit local
`file://` inputs. The slice classifies same hash at different paths,
same basename with different hashes, repeated batch input, missing or blocked
sources, and version-conflict candidates without creating duplicate ledgers,
database rows, document rows, chunk rows, job rows, manifests, reports, OCR,
embeddings, indexes, backups, or runtime outputs.

Marker: `STAGE015_PHASE2_DUPLICATE_SLICE_METADATA_ONLY_NO_PERSISTENCE_NO_PHASE3`.

## Implemented Contract

`KM_IDSystem/scripts/check_duplicate_files.py` exposes:

- `evaluate_duplicate_files(source_uris, first_seen_at, duplicate_checked_at)`;
- CLI arguments `--source-uri`, `--first-seen-at`, and
  `--duplicate-checked-at`;
- metadata-only output schema `ids.stage015.duplicate_detection.v1`;
- explicit duplicate identities with `source_uri`, `source_path`, `basename`,
  `sha256`, `file_size`, `mtime`, `first_seen_at`, and
  `duplicate_checked_at`;
- explicit rejected inputs for absent, blocked, unreadable, unsafe, or unknown
  source evidence;
- zero persistence deltas: `document_delta=0`, `chunk_delta=0`, `job_delta=0`,
  `duplicate_write_delta=0`, and inherited `manifest_write_delta=0`.

The implementation reuses STAGE-013 fingerprint records for path/hash
comparison and STAGE-014 manifest-candidate state for compatibility. It does
not recursively scan directories and does not read or write
`/Users/linzezhang/Downloads/IDS_MetaData` content.

## State Mapping

| Scenario | State |
|---|---|
| explicit readable local file identity | `DUPLICATE_READY` |
| no approved source URI | `DUPLICATE_NOT_CONFIGURED` |
| absent, non-local, directory, unreadable, or raw metadata source | `DUPLICATE_SOURCE_BLOCKED` |
| same `sha256` at different paths | `DUPLICATE_SAME_HASH_DIFFERENT_PATH` |
| same basename with different `sha256` | `DUPLICATE_SAME_NAME_DIFFERENT_HASH` |
| repeated exact batch input | `DUPLICATE_BATCH_REPEAT` |
| same-name/different-hash version review candidate | `DUPLICATE_VERSION_CONFLICT` counted through `version_conflict_count` |
| unsafe future write target | `DUPLICATE_WRITE_BLOCKED` |
| incomplete evidence | `DUPLICATE_UNKNOWN` |

## Real Source Evidence

Focused tests use tracked governance documents as real repository evidence:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE1_SCOPE_BOUNDARY.md`

Temporary process-owned copies are used only to create structural
same-name/different-hash and same-hash/different-path cases. They are not IDS
business corpus, database rows, raw metadata, or fabricated delivery evidence.

## Validation Results

Completed during implementation:

- Focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_duplicate_detection.py -q`
  failed as expected with `Ran 7 tests ... FAILED (failures=6, errors=1)`
  because `KM_IDSystem/scripts/check_duplicate_files.py` did not yet exist.
- Focused GREEN:
  the same command returned exit code `0` with `Ran 7 tests` and `OK`.
- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 25 tests ... FAILED (failures=4)` because the
  validator had not yet accepted `IDS-V0_1-STAGE015-P2`, the new focused test,
  or the new duplicate-check script path.

Final local validation for this run:

- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 25 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 89 tests` and `OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_duplicate_files.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- Events JSONL parse returned `events_jsonl_ok`.
- Owner render:
  `python3 -B scripts/lean_governance.py render --project KM_IDSystem --write`
  updated `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned exit code `0`, `drift_count=0`, and
  `reference_issue_count=0`.
- `git diff --check`:
  returned exit code `0`.
- Exact old underscored task-id variant scan:
  returned exit code `1` with no hits.
- Legacy path/name scan:
  returned only stale-path, migration-policy, compatibility-scan, or
  do-not-revive references.
- Semantic governance diagnostic:
  `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned exit code `1` with 29 known sparse-worktree/root or
  registered-project missing-path diagnostics and no new `KM_IDSystem`
  semantic error.

## Forbidden Actions Preserved

This phase did not:

- read, list, hash, open, copy, move, delete, modify, dump, scan, compact, or
  commit `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, OCR,
  Embedding, indexes, manifests, duplicate ledgers, evidence ledgers, runtime
  databases, document rows, chunk rows, job rows, generated reports, or backup
  payloads;
- start backend, frontend, Docker, workers, import jobs, report jobs, external
  APIs, or app-entry reinstall;
- push to GitHub, open a PR, merge a PR, or enter Phase 3.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE015-P2` commit. Because
the implementation is metadata-only and zero-persistence, rollback does not
require database cleanup, duplicate-ledger cleanup, manifest cleanup, runtime
output cleanup, service restart, dependency restoration, raw metadata repair,
GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
