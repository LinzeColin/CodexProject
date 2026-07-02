# IDS v0.1 STAGE-016 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-016`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE016-P3`
- Acceptance ID: `ACC-STAGE-016`
- Stage title: `导入幂等键`
- Recorded at UTC: `2026-07-02T15:18:06Z`

## Goal

Validate import-idempotency scenarios for repeated import, duplicate content,
version conflicts, no-persistence deltas, and original-material stability
without writing import records, manifests, databases, indexes, documents,
chunks, jobs, reports, outputs, or runtime data.

Marker: `STAGE016_PHASE3_IMPORT_IDEMPOTENCY_SCENARIO_VALIDATION_NO_DATABASE_NO_INDEX_WRITE_NO_PHASE4`.

## Scenario Report

Implemented report function:

- `KM_IDSystem/scripts/check_import_idempotency.py::build_stage016_scenario_report`

Focused test:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py`

The report covers:

| Scenario | Expected state | Acceptance check |
|---|---|---|
| same file / same hash | `IMPORT_SINGLE_REPEAT` | one import record, one duplicate input, zero write deltas |
| same basename / different hash | `IMPORT_KEY_CONFLICT` | key conflict and version conflict are both explicit |
| same hash / different path | `IMPORT_DUPLICATE_CONTENT` | duplicate content is explicit and provenance is preserved |
| duplicate import no persistence | `IMPORT_SINGLE_REPEAT` | document/chunk/job/index/import/manifest/duplicate deltas remain `0` |
| original hash stable | `IMPORT_KEY_READY` | before/after SHA-256 and file size are unchanged |

The focused tests use tracked governance documents as real repository source
evidence and temporary process-owned copies only for structural duplicate or
conflict cases. They do not use fake IDS business data, fake database rows,
fake source documents, placeholder corpora, or fabricated evidence.

## Boundary

This phase does not:

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
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 4.

## TDD Evidence

- Stage016 focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py -q`
  failed as expected with `Ran 8 tests ... FAILED (errors=1)` because
  `build_stage016_scenario_report` did not exist.
- Stage016 focused GREEN:
  the same command returned exit code `0` with `Ran 8 tests` and `OK`.
- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 30 tests ... FAILED (failures=1)` because
  `IDS-V0_1-STAGE016-P3` was not accepted by the governance state machine.
- Stage005 governance intermediate RED:
  the same command then failed with `Ran 30 tests ... FAILED (failures=1)`
  because `STAGE016_PHASE3_SCENARIO_VALIDATION.md` was missing as required
  evidence.

## Validation Results

Final local validation for this run:

- Stage016 focused GREEN:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage016_import_idempotency.py -q`
  returned exit code `0` with `Ran 8 tests` and `OK`.
- Stage005 governance GREEN:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned exit code `0` with `Ran 30 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 103 tests` and `OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_import_idempotency.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- Events JSONL parse returned `events_jsonl_ok`.
- Owner render:
  bundled Python
  `scripts/lean_governance.py render --project KM_IDSystem --write`
  updated `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned exit code `0`, `drift_count=0`, and `reference_issue_count=0`.
- `git diff --check`:
  returned exit code `0`.
- Exact old underscored task-id variant scan:
  returned exit code `1` with no hits.
- Legacy path/name scan:
  `rg -n "opme-system|OpMe_System" KM_IDSystem` returned historical
  migration-policy, compatibility-scan, stale-path, and do-not-revive
  references only.
- Semantic governance diagnostic:
  bundled Python
  `scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned exit code `1` with 29 known sparse-worktree/root or
  registered-project missing-path diagnostics and no new `KM_IDSystem`
  semantic error.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE016-P3` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, import-record cleanup, index cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, GitHub cleanup, or app-entry reinstall because Phase 3 writes only
tracked source/test/governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
