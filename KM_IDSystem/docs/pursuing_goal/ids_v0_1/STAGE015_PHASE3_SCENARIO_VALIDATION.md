# IDS v0.1 STAGE-015 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-015`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE015-P3`
- Acceptance ID: `ACC-STAGE-015`
- Stage title: `重复文件检测`
- Recorded at UTC: `2026-07-02T14:36:15Z`

## Goal

Validate duplicate-file detection scenarios for same-file/same-hash,
same-name/different-hash, same-hash/different-path, duplicate import without
persistence, and original-file hash stability before Phase 4 closeout.

Marker: `STAGE015_PHASE3_SCENARIO_VALIDATION_NO_WRITES_NO_PHASE4`.

## Scenario Coverage

`KM_IDSystem/scripts/check_duplicate_files.py` now exposes
`build_stage015_scenario_report(...)`.

The report covers:

| Scenario | Expected state | Required proof |
|---|---|---|
| same file and same hash | `DUPLICATE_BATCH_REPEAT` | one duplicate input and one identity |
| same name and different hash | `DUPLICATE_SAME_NAME_DIFFERENT_HASH` | version conflict count is one |
| same hash and different path | `DUPLICATE_SAME_HASH_DIFFERENT_PATH` | duplicate content count is one |
| duplicate import without persistence | `DUPLICATE_BATCH_REPEAT` | `document_delta=0`, `chunk_delta=0`, `job_delta=0`, `duplicate_write_delta=0`, `manifest_write_delta=0` |
| original hash stability | `DUPLICATE_READY` | before/after `sha256` and size are unchanged |

## Evidence Boundary

Focused tests use tracked governance documents as real repository source
evidence:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE015_PHASE1_SCOPE_BOUNDARY.md`

Temporary process-owned copies are used only to build structural duplicate and
conflict cases. They are not IDS corpus, fake business data, fake database
rows, raw metadata, or committed source documents.

The local raw metadata database root
`/Users/linzezhang/Downloads/IDS_MetaData` remains blocked before existence
checks, file opening, hashing, copying, listing, scanning, moving, deleting,
modification, dumping, or persistence. No raw metadata content was read,
listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned, or
committed in this phase.

## No-Persistence Proof

The Phase 3 scenario report records:

- `document_delta=0`;
- `chunk_delta=0`;
- `job_delta=0`;
- `duplicate_write_delta=0`;
- `manifest_write_delta=0`;
- `does_not_write_duplicate_ledger=true`;
- `does_not_write_database=true`;
- `does_not_create_documents_chunks_jobs=true`;
- `does_not_read_raw_metadata=true`;
- `does_not_call_external_apis=true`.

## Validation Results

Completed during implementation:

- Focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage015_duplicate_detection.py -q`
  failed as expected with `Ran 8 tests ... FAILED (errors=1)` because
  `build_stage015_scenario_report` did not exist yet.
- Focused GREEN:
  the same command returned exit code `0` with `Ran 8 tests` and `OK`.
- Governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 26 tests ... FAILED (failures=1)` because the
  Phase 3 batch/roadmap state was not yet accepted by the validator.

Final local validation for this run:

- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 26 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 91 tests` and `OK`.
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

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, duplicate-ledger, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, persisted manifests, duplicate ledgers, evidence ledgers,
  document rows, chunk rows, job rows, indexes, OCR output, Embedding output,
  or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 4.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE015-P3` commit. Because
Phase 3 writes only tracked source/test/governance files, rollback does not
require data cleanup, schema rollback, service restart, dependency restoration,
manifest cleanup, duplicate-ledger cleanup, runtime database cleanup, report
cleanup, raw metadata repair, GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
