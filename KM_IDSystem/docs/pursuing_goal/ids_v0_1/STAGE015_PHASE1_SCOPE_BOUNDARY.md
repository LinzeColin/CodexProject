# IDS v0.1 STAGE-015 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-015`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE015-P1`
- Acceptance ID: `ACC-STAGE-015`
- Stage title: `重复文件检测`
- Recorded at UTC: `2026-07-02T14:14:14Z`

## Goal

Confirm the duplicate-file detection contract before implementing any scanner,
duplicate detector, persistence adapter, document/chunk/job creation, evidence
ledger update, audit log write, report slice, or UI slice.

This phase records evidence and engineering contracts only. It does not start
services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
`00_ORIGINAL_RAW_DATA`, read or scan `/Users/linzezhang/Downloads/IDS_MetaData`,
hash raw files, write manifests, write databases, create documents, create
chunks, create jobs, generate reports, or enter Phase 2.

Marker: `STAGE015_PHASE1_DUPLICATE_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-015_重复文件检测.md` |
| Stage file SHA-256 | `5c2f7e743862db9ae6bfdc0dd876335398322a8d6881fc052bbc7d48337f3be1` |
| Stage execution index | STAGE-015 maps to `D03-S004`, `ACC-STAGE-015`, and `stages/STAGE-015_重复文件检测.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree.

## Relationship To STAGE-012 Through STAGE-014

STAGE-015 extends prior D03 boundaries:

- STAGE-012: original-material read-only identity and no-mutation rules.
- STAGE-013: explicit `file://` fingerprint evidence and conflict/duplicate
  state patterns.
- STAGE-014: metadata-only manifest candidates, idempotency, manifest state
  mapping, and no persistence writes.

STAGE-015 does not replace or weaken any of these rules.

Inherited rules:

- original files remain read-only by default;
- original files must not be moved, deleted, overwritten, normalized,
  compacted, renamed, repaired, or deduplicated in place;
- duplicate identity must remain linked to explicit `source_uri`, `sha256`,
  `file_size`, `mtime`, and `first_seen_at` evidence;
- duplicate detection must use real future source metadata and fingerprint
  evidence, not fake business data or fabricated examples;
- repeated observation and repeated batch import must be idempotent;
- same-name/different-hash and same-hash/different-path cases must preserve
  provenance and explicit conflict/duplicate states;
- failure states must be explicit and fail closed.

## Duplicate Detection Field Contract

Future implementation must compare bounded metadata records. It must not embed
raw source payload content, secrets, screenshots, large binary payloads,
database dumps, or unbounded text extraction.

| Field | Required meaning | Phase 1 rule |
|---|---|---|
| `source_uri` | Absolute `file://` URI for a future user-approved explicit source. | Define only; do not open, scan, or normalize real raw content. |
| `sha256` | SHA-256 fingerprint inherited from bounded read-only fingerprint evidence. | Define only; Phase 1 does not hash real raw files. |
| `file_size` | Byte length observed at the same source/fingerprint time. | Define only; do not stat real raw files in this phase. |
| `mtime` | Filesystem modification time observed with the future source evidence. | Define only; later drift checks must not rewrite source files. |
| `first_seen_at` | UTC timestamp when IDS first records the duplicate-comparable file identity. | Define only; must come from real future observation time. |
| `duplicate_state` | Explicit duplicate/conflict/readiness classification. | Define only; unknown states fail closed. |

## Duplicate Idempotency And Recognition Rules

Phase 1 defines these rules for later phases:

- same `source_uri` and same `sha256` is the same observed file identity;
- same `sha256` at different paths is duplicate content with separate
  provenance, not a deletion request;
- same basename with different `sha256` is a version/conflict candidate, not an
  overwrite;
- repeated batch import must not create duplicate document rows, chunk rows,
  job rows, evidence ledger facts, audit events, reports, manifests, or
  duplicate-detection facts;
- unsupported or incomplete evidence must be recorded as an explicit state
  instead of being silently skipped.

## Future Status Contract

Phase 1 defines status names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `DUPLICATE_READY` | A bounded duplicate comparison can run. | Allow future metadata-only comparison under explicit gate. |
| `DUPLICATE_NOT_CONFIGURED` | No approved source URI, fingerprint, or manifest evidence exists. | Fail closed and request configuration. |
| `DUPLICATE_SOURCE_BLOCKED` | Source path is unsafe, absent, non-local, or raw metadata root. | Block before side effects. |
| `DUPLICATE_FINGERPRINT_MISSING` | Required fingerprint evidence is absent. | Do not fabricate hash or size metadata. |
| `DUPLICATE_SAME_HASH_DIFFERENT_PATH` | Same hash appears at multiple source URIs. | Preserve provenance; do not delete originals. |
| `DUPLICATE_SAME_NAME_DIFFERENT_HASH` | Same basename has conflicting hashes. | Preserve both facts and require review. |
| `DUPLICATE_BATCH_REPEAT` | Repeated batch input points to an already observed identity. | Keep persistence deltas at zero unless later gate allows updates. |
| `DUPLICATE_VERSION_CONFLICT` | Evidence suggests version lineage or conflicting source identity. | Route to later review; do not overwrite. |
| `DUPLICATE_WRITE_BLOCKED` | Future duplicate-record target is not safe or rollbackable. | Do not write database rows. |
| `DUPLICATE_UNKNOWN` | Classification is incomplete. | Fail closed; do not scan, import, index, or report. |

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- `STAGE015_ENTRY_CONTRACT.md`;
- this Phase 1 boundary document;
- `BATCH011_020_UPLOAD_LOCK.yaml`;
- roadmap and event-log governance records;
- Stage005 governance regression validator and tests for current-state forward
  compatibility;
- rendered Chinese owner-entry files.

## Forbidden Phase 1 Actions

Phase 1 must not:

- start Docker Desktop, Docker Compose, backend, frontend, workers, OCR,
  Embedding, indexing, import, report, backup, manifest, duplicate-detection,
  MIME detection, or API jobs;
- install Python, npm, Docker, or system dependencies;
- create `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `data/`,
  `reports/`, `outputs/`, manifests, duplicate ledgers, evidence ledgers,
  runtime databases, document/chunk/job rows, generated indexes, OCR outputs,
  embeddings, or backup payloads;
- create, list, hash, open, copy, move, delete, overwrite, normalize, compact,
  or mutate `00_ORIGINAL_RAW_DATA` or
  `/Users/linzezhang/Downloads/IDS_MetaData`;
- write duplicate records, manifest files, manifest database rows, audit log
  entries, evidence ledger entries, report files, document rows, chunk rows, or
  job rows;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated;
- enter Phase 2 in the same run.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-015 taskpack SHA-256;
- confirm stage execution index maps STAGE-015 to `D03-S004` and
  `ACC-STAGE-015`;
- confirm STAGE-012, STAGE-013, and STAGE-014 evidence are predecessor
  boundaries;
- run Stage005 governance regression RED/GREEN for `IDS-V0_1-STAGE015-P1`;
- run `validate_stage005_governance_regression.py`;
- run pursuing-goal unittest discovery;
- run `check-render --project KM_IDSystem`;
- run `git diff --check`;
- run semantic validate only as a known sparse-worktree diagnostic and do not
  expand unrelated projects.

Phase 2 may implement a small bounded duplicate-detection slice only after this
boundary is committed.

## Validation Results

Final local validation for this run:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 24 tests ... FAILED (failures=3)` because
  `IDS-V0_1-STAGE015-P1`, `STAGE015_ENTRY_CONTRACT.md`, and
  `STAGE015_PHASE1_SCOPE_BOUNDARY.md` were not yet accepted.
- Stage005 governance intermediate RED:
  the same command then failed with `Ran 24 tests ... FAILED (failures=1)`
  because the required STAGE-015 evidence files had not yet been created.
- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 24 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 81 tests` and `OK`.
- Python syntax check:
  `python3 -B -m py_compile` for
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
  scan still returns only stale-path, migration, compatibility-policy, and
  do-not-revive references.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE015-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, service restart, dependency restoration, manifest cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.

## Decision

STAGE-015 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, the event log, validator/test updates,
and rendered owner entries all point to `IDS-V0_1-STAGE015-P1`; upload remains
blocked until STAGE-011..020 are complete, reviewed, repaired, batch-gated,
and app entries are reinstalled.
