# IDS v0.1 STAGE-013 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-013`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE013-P3`
- Acceptance ID: `ACC-STAGE-013`
- Stage title: `文件指纹引擎`
- Recorded at UTC: `2026-07-02T13:16:44Z`

## Goal

Validate file-fingerprint scenarios for same-file/same-hash, same-name/
different-hash, same-hash/different-path, duplicate import without persistence,
and original-file hash stability.

This phase extends the Phase 2 metadata-only preflight with an in-memory
scenario report. It does not create persisted manifests, database records,
document/chunk/job records, runtime outputs, reports, indexes, OCR outputs,
embeddings, backups, or customer-visible records.

## Scenario Coverage

`KM_IDSystem/scripts/check_file_fingerprint.py` now provides
`build_stage013_scenario_report(...)` with these checks:

| Scenario | Expected state | Persistence effect |
|---|---|---|
| same file and same hash | `FINGERPRINT_READY` with one duplicate input | no duplicate manifest candidate |
| same name and different hash | `FINGERPRINT_HASH_CONFLICT` | no overwrite, merge, or delete |
| same hash and different path | `FINGERPRINT_DUPLICATE_CONTENT` | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0` | no persistence adapter exists |
| original hash stability | before/after `sha256` and `size` unchanged | original file unchanged |

The report is a validation artifact for future persistence design. It is not a
production import, not a manifest write, and not a database migration.

## Real Data Boundary

Focused tests use tracked governance documents as real repository source
evidence:

- `STAGE013_ENTRY_CONTRACT.md`
- `STAGE013_PHASE2_FILE_FINGERPRINT_SLICE.md`

Temporary process-owned copies are used only to build structural duplicate and
conflict cases. They are not IDS corpus, not fake business data, not fake
database rows, and not committed source documents.

The local raw metadata database root
`/Users/linzezhang/Downloads/IDS_MetaData` remains blocked before existence
checks, file opening, hashing, MIME inference, copying, listing, scanning,
moving, deleting, modification, dumping, or persistence. No raw metadata
content was read, listed, opened, hashed, copied, moved, deleted, modified,
dumped, scanned, or committed in this phase.

## TDD Evidence

- Focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py -q`
  failed as expected with `Ran 6 tests ... FAILED (errors=1)` because
  `build_stage013_scenario_report` was missing.
- Focused GREEN:
  the same command returned `Ran 6 tests ... OK` after implementation.
- Governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 18 tests ... FAILED (failures=1)` because
  `IDS-V0_1-STAGE013-P3` was not yet accepted by the governance-regression
  validator.

## Validation Results

Final local validation for this phase:

- STAGE-013 focused tests:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py -q`
  returned `Ran 6 tests ... OK`.
- Stage005 governance regression:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned `Ran 18 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, `unexpected_changed_paths=[]`,
  `missing_required_files=[]`, and `forbidden_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 69 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_file_fingerprint.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned `drift_count=0`.
- `git diff --check`:
  returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem`:
  returned exit code `1` with 29 known sparse/root/registered-project
  diagnostics and no `KM_IDSystem` project regression.
- Marker scans:
  the exact underscored task-id marker scan returned no hits; legacy path/name
  scan hits remain stale-path, migration-note, and compatibility-scan
  references only.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE013-P3` commit. This
removes the scenario-report implementation, focused tests, Phase 3 evidence,
batch lock, roadmap/event, validator/test, and rendered owner-entry changes.

Rollback must not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, manifests, evidence ledgers, audit
logs, delivered reports, runtime data, app entries, GitHub state, or Phase 4.

## Decision

STAGE-013 Phase 3 may complete locally when the focused scenario tests,
Stage005 governance regression, Stage005 validator, full v0.1 unittest
discovery, syntax checks, render drift check, `git diff --check`, and sparse
semantic validate diagnostic are recorded. These checks are now recorded for
this run. GitHub upload remains blocked until STAGE-011..020 are complete,
reviewed, repaired, batch-gated, and app entries are reinstalled.
