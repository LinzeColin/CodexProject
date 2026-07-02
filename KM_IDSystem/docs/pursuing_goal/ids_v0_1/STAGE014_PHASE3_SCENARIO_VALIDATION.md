# IDS v0.1 STAGE-014 Phase 3 Scenario Validation

## Identity

- Stage: `STAGE-014`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE014-P3`
- Acceptance ID: `ACC-STAGE-014`
- Stage title: `Manifest 生成`
- Recorded at UTC: `2026-07-02T13:55:14Z`

## Goal

Validate metadata-only manifest generation scenarios for duplicates, conflicts,
idempotent repeated import, and original-file protection before Phase 4
closeout.

Marker: `STAGE014_PHASE3_SCENARIO_VALIDATION_NO_WRITES_NO_PHASE4`.

## Scenario Coverage

`KM_IDSystem/scripts/check_manifest_generation.py` now exposes
`build_stage014_scenario_report(...)`.

The report covers:

| Scenario | Expected state | Required proof |
|---|---|---|
| same file and same hash | `MANIFEST_READY` | one manifest candidate and one duplicate input |
| same name and different hash | `MANIFEST_HASH_CONFLICT` | conflict count is one; no overwrite |
| same hash and different path | `MANIFEST_DUPLICATE_CONTENT` | duplicate content count is one; provenance preserved |
| duplicate import without persistence | `MANIFEST_READY` | `document_delta=0`, `chunk_delta=0`, `job_delta=0`, `manifest_write_delta=0` |
| original hash stability | `MANIFEST_READY` | before/after `sha256` and size are unchanged |

## Evidence Boundary

Focused tests use tracked governance documents as real repository source
evidence and temporary process-owned copies only for structural duplicate and
conflict scenarios.

This is not IDS business data and is not a raw metadata database payload. No
fake IDS business data, fake database rows, fake source documents, placeholder
corpora, or fabricated evidence were introduced.

The temporary files are created under the process temp directory and are removed
by the test runner. They are not committed, not copied into product runtime
folders, and not treated as source corpus.

## No-Persistence Proof

The Phase 3 scenario report records:

- `document_delta=0`;
- `chunk_delta=0`;
- `job_delta=0`;
- `manifest_write_delta=0`;
- `does_not_write_manifest_files=true`;
- `does_not_write_database=true`;
- `does_not_create_documents_chunks_jobs=true`;
- `does_not_read_raw_metadata=true`;
- `does_not_call_external_apis=true`.

## Validation Results

- Focused RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py -q`
  first failed with `Ran 6 tests`, `errors=1`, because
  `build_stage014_scenario_report` did not exist yet.
- Focused GREEN:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py -q`
  returned exit code `0` with `Ran 6 tests` and `OK`.
- Governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  first failed with `Ran 22 tests`, `failures=1`, because the Phase 3
  batch/roadmap state was not yet whitelisted.
- Governance GREEN:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned exit code `0` with `Ran 22 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `unexpected_changed_paths=[]`, and `forbidden_changed_paths=[]`.
- Full v0.1 unittest discover:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 79 tests` and `OK`.
- Python compile:
  `python3 -B -m py_compile KM_IDSystem/scripts/check_manifest_generation.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`.
- Owner render:
  `python3 -B scripts/lean_governance.py render --project KM_IDSystem --write`
  updated `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- Semantic governance diagnostic:
  `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned exit code `1` with 29 known sparse-worktree/root or
  registered-project missing-path diagnostics and no new `KM_IDSystem`
  semantic error.
- Final check-render:
  `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned exit code `0`, `drift_count=0`, and `reference_issue_count=0`.
- Final diff whitespace check:
  `git diff --check` returned exit code `0`.
- Final old underscored task-id variant scan returned no hits.
- Legacy name scan for `OpMe_System` and `opme-system` found only historical
  migration, stale-path, or do-not-revive references. This Phase 3 run did not
  recreate either as an active development path.

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
- push to GitHub, open a PR, merge, reinstall app entries, or enter Phase 4.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE014-P3` commit. Because
Phase 3 writes only tracked source/test/governance files, rollback does not
require data cleanup, schema rollback, service restart, dependency restoration,
manifest cleanup, runtime database cleanup, report cleanup, raw metadata repair,
GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
