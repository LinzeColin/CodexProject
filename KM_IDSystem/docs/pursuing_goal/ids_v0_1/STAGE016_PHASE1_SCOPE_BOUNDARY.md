# IDS v0.1 STAGE-016 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-016`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE016-P1`
- Acceptance ID: `ACC-STAGE-016`
- Stage title: `导入幂等键`
- Recorded at UTC: `2026-07-02T14:53:57Z`

## Goal

Confirm the import-idempotency-key contract before implementing any scanner,
import adapter, database write, document/chunk/job creation, index write,
evidence ledger update, audit log write, report slice, or UI slice.

This phase records evidence and engineering contracts only. It does not start
services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
`00_ORIGINAL_RAW_DATA`, read or scan `/Users/linzezhang/Downloads/IDS_MetaData`,
hash raw files, write manifests, write databases, create documents, create
chunks, create jobs, update indexes, generate reports, or enter Phase 2.

Marker: `STAGE016_PHASE1_IMPORT_IDEMPOTENCY_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-016_导入幂等键.md` |
| Stage file SHA-256 | `0abc5ed195217226b96c41ff1064d07dfea01beead173a07ab313d68f4bb28f4` |
| Stage execution index | STAGE-016 maps to `D03-S005`, `ACC-STAGE-016`, and `stages/STAGE-016_导入幂等键.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree.

## Relationship To STAGE-012 Through STAGE-015

STAGE-016 extends prior D03 boundaries:

- STAGE-012: original-material read-only identity and no-mutation rules.
- STAGE-013: explicit `file://` fingerprint evidence and conflict/duplicate
  state patterns.
- STAGE-014: metadata-only manifest candidates, idempotency, manifest state
  mapping, and no persistence writes.
- STAGE-015: duplicate-file detection, duplicate/conflict states, repeated
  import no-persistence proof, and original-file protection proof.

STAGE-016 does not replace or weaken any of these rules.

Inherited rules:

- original files remain read-only by default;
- original files must not be moved, deleted, overwritten, normalized,
  compacted, renamed, repaired, or deduplicated in place;
- import idempotency must remain linked to explicit `source_uri`, `sha256`,
  `file_size`, `mtime`, `first_seen_at`, fingerprint, manifest, and duplicate
  evidence;
- idempotency checks must occur before document/chunk/job/index writes;
- repeated observation and repeated batch import must be idempotent;
- same-name/different-hash and same-hash/different-path cases must preserve
  provenance and explicit conflict/duplicate states;
- failure states must be explicit and fail closed.

## Import Idempotency Field Contract

Future implementation must compare bounded metadata records. It must not embed
raw source payload content, secrets, screenshots, large binary payloads,
database dumps, or unbounded text extraction.

| Field | Required meaning | Phase 1 rule |
|---|---|---|
| `source_uri` | Absolute `file://` URI for a future user-approved explicit source. | Define only; do not open, scan, or normalize real raw content. |
| `sha256` | SHA-256 fingerprint inherited from bounded read-only fingerprint evidence. | Define only; Phase 1 does not hash real raw files. |
| `file_size` | Byte length observed at the same source/fingerprint time. | Define only; do not stat real raw files in this phase. |
| `mtime` | Filesystem modification time observed with the future source evidence. | Define only; later drift checks must not rewrite source files. |
| `first_seen_at` | UTC timestamp when IDS first records the file identity. | Define only; must be reused as the original observation time for repeated imports. |
| `manifest_identity` | Stable metadata-only manifest identity from STAGE-014 or a later approved manifest gate. | Define only; do not write manifests in Phase 1. |
| `duplicate_state` | Duplicate/conflict/readiness classification inherited from STAGE-015. | Define only; unknown states fail closed. |
| `import_idempotency_key` | Deterministic key for a source identity or batch identity. | Define only; must be checked before document/chunk/job/index writes. |

## Idempotency Key Rules

Phase 1 defines these rules for later phases:

- file-level idempotency must be deterministic for the same approved
  `source_uri`, `sha256`, `file_size`, and manifest/fingerprint evidence;
- content-level identity may be shared by the same `sha256` and `file_size`,
  but source provenance must remain separate;
- batch-level idempotency must be derived from an approved batch identity plus
  the ordered set of bounded source identities, not from wall-clock retry time;
- `first_seen_at` is metadata evidence, not a reason to create a duplicate row
  on retry;
- repeated single-file import must keep `document_delta=0`, `chunk_delta=0`,
  `job_delta=0`, and `index_delta=0` after the identity is already recorded;
- repeated batch import must not duplicate documents, chunks, jobs, index
  entries, manifests, evidence facts, audit events, or reports;
- same basename with different `sha256` remains a conflict/version candidate,
  not an idempotent overwrite;
- unsupported or incomplete evidence must be recorded as an explicit state
  instead of being silently skipped.

## Future Status Contract

Phase 1 defines status names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `IMPORT_IDEMPOTENCY_READY` | A bounded idempotency check can run. | Allow future metadata-only comparison under explicit gate. |
| `IMPORT_NOT_CONFIGURED` | No approved source URI, fingerprint, manifest, or batch identity exists. | Fail closed and request configuration. |
| `IMPORT_SOURCE_BLOCKED` | Source path is unsafe, absent, non-local, unreadable, or raw metadata root. | Block before side effects. |
| `IMPORT_FINGERPRINT_MISSING` | Required fingerprint evidence is absent. | Do not fabricate hash or size metadata. |
| `IMPORT_MANIFEST_MISSING` | Required manifest evidence is absent. | Do not write manifest or import rows in this phase. |
| `IMPORT_KEY_READY` | The idempotency key can be derived from bounded metadata. | Compare before persistence writes. |
| `IMPORT_KEY_CONFLICT` | Same key maps to conflicting metadata. | Stop and require review; do not overwrite. |
| `IMPORT_SINGLE_REPEAT` | The same source identity was already imported. | Keep document/chunk/job/index deltas at zero. |
| `IMPORT_BATCH_REPEAT` | The same approved batch identity was already imported. | Keep all import and index deltas at zero. |
| `IMPORT_DUPLICATE_CONTENT` | Same content hash appears through another source path. | Preserve provenance; do not delete originals. |
| `IMPORT_WRITE_BLOCKED` | Future write target is not safe or rollbackable. | Do not write database, index, evidence, audit, or report records. |
| `IMPORT_UNKNOWN` | Classification is incomplete. | Fail closed; do not scan, import, index, or report. |

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- `STAGE016_ENTRY_CONTRACT.md`;
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
- write import records, document rows, chunk rows, job rows, index rows,
  manifest files, manifest database rows, audit log entries, evidence ledger
  entries, report files, or cache files;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated;
- enter Phase 2 in the same run.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-016 taskpack SHA-256;
- confirm stage execution index maps STAGE-016 to `D03-S005` and
  `ACC-STAGE-016`;
- confirm STAGE-012 through STAGE-015 evidence are predecessor boundaries;
- run Stage005 governance regression RED/GREEN for `IDS-V0_1-STAGE016-P1`;
- run `validate_stage005_governance_regression.py`;
- run pursuing-goal unittest discovery;
- run `check-render --project KM_IDSystem`;
- run `git diff --check`;
- run semantic validate only as a known sparse-worktree diagnostic and do not
  expand unrelated projects.

Phase 2 may implement a small bounded import-idempotency slice only after this
boundary is committed.

## Validation Results

Final local validation for this run:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 28 tests ... FAILED (failures=3)` because
  `IDS-V0_1-STAGE016-P1`, `STAGE016_ENTRY_CONTRACT.md`, and
  `STAGE016_PHASE1_SCOPE_BOUNDARY.md` were not yet accepted.
- Stage005 governance intermediate RED:
  the same command then failed with `Ran 28 tests ... FAILED (failures=1)`
  because the required STAGE-016 evidence files had not yet been created.
- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 28 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 93 tests` and `OK`.
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
  scan still returns only historical migration-policy, compatibility-scan,
  stale-path, or do-not-revive references.

No raw metadata content was read, listed, opened, hashed, copied, moved,
deleted, modified, dumped, scanned, or committed in this phase.

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE016-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, service restart, dependency restoration, manifest cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.

## Decision

STAGE-016 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, the event log, validator/test updates,
and rendered owner entries all point to `IDS-V0_1-STAGE016-P1`; upload remains
blocked until STAGE-011..020 are complete, reviewed, repaired, batch-gated,
and app entries are reinstalled.
