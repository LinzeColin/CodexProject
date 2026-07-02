# IDS v0.1 STAGE-013 Phase 2 File Fingerprint Slice

## Identity

- Stage: `STAGE-013`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE013-P2`
- Acceptance ID: `ACC-STAGE-013`
- Stage title: `文件指纹引擎`
- Recorded at UTC: `2026-07-02T13:05:50Z`

## Goal

Implement a minimum bounded file-fingerprint slice for explicit local `file://`
inputs. This phase records metadata-only fingerprints and explicit failure
states without creating manifests, database rows, document/chunk/job records,
runtime outputs, reports, indexes, OCR outputs, embeddings, backups, or
customer-visible records.

## Implemented Slice

`KM_IDSystem/scripts/check_file_fingerprint.py` now provides:

- `evaluate_file_fingerprints(...)` for explicit local `file://` source URIs;
- `sha256`, canonical `size`, compatibility `file_size`, `mtime`,
  `extension`, `mime`, `source_uri`, `source_path`, and `first_seen_at`;
- idempotent repeated-input handling through `duplicate_input_count`;
- explicit `FINGERPRINT_PATH_BLOCKED` and `FINGERPRINT_READ_BLOCKED` states;
- fail-closed `FINGERPRINT_NOT_CONFIGURED` behavior when no source URI is
  supplied;
- a JSON CLI for operations-only smoke checks.

The implementation derives `extension` from the filename suffix and `mime`
from Python standard-library `mimetypes`. It does not inspect raw bytes for
MIME, call external services, write manifests, write databases, create
document/chunk/job records, or scan recursively.

## Real Data Boundary

Focused tests use the tracked
`KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE013_ENTRY_CONTRACT.md` governance
document as a real repository source input. This is not fake IDS business data,
not a fake database row, and not a fabricated source document.

The local raw metadata database root
`/Users/linzezhang/Downloads/IDS_MetaData` is blocked before existence checks,
hashing, file opening, MIME inference, copying, listing, scanning, moving,
deleting, modification, dumping, or persistence. No raw metadata content was
read, listed, opened, hashed, copied, moved, deleted, modified, dumped,
scanned, or committed in this phase.

## TDD Evidence

- Focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py -q`
  failed as expected with `Ran 5 tests ... FAILED (failures=4, errors=1)`
  because `check_file_fingerprint.py` was missing.
- Focused GREEN:
  the same command returned `Ran 5 tests ... OK` after implementation.
- Governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 17 tests ... FAILED (failures=4)` because
  `STAGE013-P2`, the new test path, and `check_file_fingerprint.py` were not
  yet accepted by the governance-regression validator.

## Validation Results

Final local validation for this phase:

- STAGE-013 focused tests:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage013_file_fingerprint.py -q`
  returned `Ran 5 tests ... OK`.
- Stage005 governance regression:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned `Ran 17 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, `unexpected_changed_paths=[]`,
  `missing_required_files=[]`, and `forbidden_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 67 tests ... OK`.
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
  the exact underscored task-id marker scan returned no hits; legacy
  path/name scan hits remain stale-path, migration-note, and
  compatibility-scan references only.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE013-P2` commit. This
removes the file-fingerprint script, focused tests, Phase 2 evidence, batch
lock, roadmap/event, validator/test, and rendered owner-entry changes.

Rollback must not touch `00_ORIGINAL_RAW_DATA`,
`/Users/linzezhang/Downloads/IDS_MetaData`, manifests, evidence ledgers, audit
logs, delivered reports, runtime data, app entries, GitHub state, or Phase 3.

## Decision

STAGE-013 Phase 2 may complete locally when the focused fingerprint tests,
Stage005 governance regression, Stage005 validator, full v0.1 unittest
discovery, syntax checks, render drift check, `git diff --check`, and sparse
semantic validate diagnostic are recorded. These checks are now recorded for
this run. GitHub upload remains blocked until STAGE-011..020 are complete,
reviewed, repaired, batch-gated, and app entries are reinstalled.
