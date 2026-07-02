# IDS v0.1 STAGE-013 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-013`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE013-P1`
- Acceptance ID: `ACC-STAGE-013`
- Stage title: `文件指纹引擎`
- Recorded at UTC: `2026-07-02T12:52:29Z`

## Goal

Confirm the file-fingerprint engine contract before implementing any scanner,
hasher, MIME detector, manifest writer, persistence adapter, index job, import
job, evidence ledger update, or report slice.

This phase records evidence and engineering contracts only. It does not start
services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
`00_ORIGINAL_RAW_DATA`, read or scan `/Users/linzezhang/Downloads/IDS_MetaData`,
hash raw files, detect MIME from raw bytes, write manifests, generate evidence
ledgers, create documents, create chunks, create jobs, generate reports, or
enter Phase 2.

Marker: `STAGE013_PHASE1_FINGERPRINT_ENGINE_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-013_文件指纹引擎.md` |
| Stage file SHA-256 | `514e55b51c6031fb9c6eb1c7e14a511334fc00a7f9dfd79c25b53b7e469c9316` |
| Stage execution index | STAGE-013 maps to `D03-S002`, `ACC-STAGE-013`, and `stages/STAGE-013_文件指纹引擎.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree.

## Relationship To STAGE-012

STAGE-013 extends the STAGE-012 original-material read-only contract. It does
not replace or weaken it.

Inherited rules:

- original files remain read-only by default;
- original files must not be moved, deleted, overwritten, normalized,
  compacted, renamed, repaired, or deduplicated in place;
- repeated observation must be idempotent;
- same-name/different-hash and same-hash/different-path cases must preserve
  provenance;
- failure states must be explicit and fail closed;
- no fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence may be introduced.

## Fingerprint Field Contract

Future implementation must treat file fingerprints as immutable metadata
derived from bounded read-only observation.

| Field | Required meaning | Phase 1 rule |
|---|---|---|
| `source_uri` | Absolute `file://` URI for a user-approved explicit source file or bounded source path. | Define only; do not open, scan, or normalize real raw content. |
| `sha256` | Hex SHA-256 fingerprint of exact file bytes. | Define only; Phase 1 does not hash real raw files. |
| `size` | Byte length observed at fingerprint time. | Define only; Phase 1 does not stat real raw files. |
| `mtime` | Source filesystem modification time observed at fingerprint time. | Define only; later drift checks must not rewrite files. |
| `extension` | Lowercase normalized filename suffix, including multi-part suffix rules only when explicitly defined by later implementation. | Define only; extension is not trusted content type. |
| `mime` | Best-effort MIME metadata from safe future logic. | Define only; Phase 1 does not inspect bytes or call external services. |
| `first_seen_at` | UTC timestamp when IDS first records the fingerprint identity. | Define only; must be generated from actual future observation time. |

`size` is the stage-level field name because the P0 taskpack names `size`.
Future adapters may expose compatibility aliases such as `file_size` only if
they preserve the canonical `size` value and do not create duplicate facts.

## MIME And Extension Rules

Phase 1 only defines the contract:

- `extension` may be derived from the filename string supplied by the explicit
  local path.
- `mime` may be `UNKNOWN` when safe detection is unavailable.
- no future `mime` decision may be based on remote service calls unless a later
  explicit stage grants that scope;
- no future `mime` decision may allow raw payload content into GitHub,
  manifests, reports, logs, or evidence ledgers;
- mismatch between extension and MIME must become an explicit state, not a
  silent correction or overwrite.

## Future Status Contract

Phase 1 defines status names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `FINGERPRINT_READY` | A bounded explicit source can be fingerprinted under read-only rules. | Allow metadata-only fingerprint report. |
| `FINGERPRINT_NOT_CONFIGURED` | No approved source URI was supplied. | Fail closed and request configuration. |
| `FINGERPRINT_PATH_BLOCKED` | Source path is outside allowed roots, unsafe, missing, or unvalidated. | Block before side effects. |
| `FINGERPRINT_READ_BLOCKED` | Explicit file cannot be read by a future authorized scanner. | Record explicit failure; do not skip silently. |
| `FINGERPRINT_HASH_CONFLICT` | Same source/name maps to conflicting hash evidence. | Record conflict; do not overwrite. |
| `FINGERPRINT_DUPLICATE_CONTENT` | Same hash appears at multiple source URIs. | Preserve provenance; do not delete originals. |
| `FINGERPRINT_MIME_UNKNOWN` | MIME cannot be determined safely. | Continue only when downstream stage allows unknown MIME. |
| `FINGERPRINT_MIME_CONFLICT` | Extension and MIME disagree under future detector logic. | Record mismatch; do not rewrite file or extension. |
| `FINGERPRINT_MANIFEST_UNSAFE` | Manifest target would store raw payload, secrets, unbounded data, or unsafe path. | Block manifest write before side effects. |
| `FINGERPRINT_UNKNOWN` | State cannot be classified from available evidence. | Fail closed; do not scan, import, index, or report. |

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- `STAGE013_ENTRY_CONTRACT.md`;
- this Phase 1 boundary document;
- `BATCH011_020_UPLOAD_LOCK.yaml`;
- roadmap and event-log governance records;
- Stage005 governance regression validator and tests for current-state forward
  compatibility;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, workers, OCR,
  Embedding, indexing, import, report, backup, manifest, MIME detection, or API
  jobs;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, manifests, evidence ledgers, runtime databases,
  document/chunk/job rows, generated indexes, OCR outputs, embeddings, or
  backup payloads;
- create, list, hash, open, copy, move, delete, overwrite, normalize, compact,
  or mutate `00_ORIGINAL_RAW_DATA` or
  `/Users/linzezhang/Downloads/IDS_MetaData`;
- infer MIME by opening raw files or calling external services;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated;
- enter Phase 2 in the same run.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-013 taskpack SHA-256;
- confirm stage execution index maps STAGE-013 to `D03-S002` and
  `ACC-STAGE-013`;
- confirm STAGE-012 read-only identity contract is the predecessor boundary;
- run Stage005 governance regression RED/GREEN for `IDS-V0_1-STAGE013-P1`;
- run `validate_stage005_governance_regression.py`;
- run pursuing-goal unittest discovery;
- run `check-render --project KM_IDSystem`;
- run `git diff --check`;
- run semantic validate only as a known sparse-worktree diagnostic and do not
  expand unrelated projects.

Phase 2 may implement a small bounded fingerprinting slice only after this
boundary is committed.

## Validation Results

Final local validation for this run:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 16 tests ... FAILED (failures=3)` because
  `IDS-V0_1-STAGE013-P1`, `STAGE013_ENTRY_CONTRACT.md`, and
  `STAGE013_PHASE1_SCOPE_BOUNDARY.md` were not yet accepted.
- Stage005 governance GREEN:
  the same command returned `Ran 16 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 61 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for
  `validate_stage005_governance_regression.py` returned exit code `0`.
- `scripts/lean_governance.py check-render --project KM_IDSystem`:
  returned `drift_count=0`.
- `git diff --check`:
  returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem`:
  returned exit code `1` with 29 known sparse/root/registered-project
  diagnostics and no `KM_IDSystem` project regression.
- Marker scan:
  exact underscored task-id variant scan returned no hits; legacy path/name
  scan still returns only stale-path, migration, and compatibility-policy
  references.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE013-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, service restart, dependency restoration, manifest cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, or GitHub PR cleanup.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.

## Decision

STAGE-013 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, the event log, validator/test updates,
and rendered owner entries all point to `IDS-V0_1-STAGE013-P1`; upload remains
blocked until STAGE-011..020 are complete, reviewed, repaired, batch-gated,
and app entries are reinstalled.
