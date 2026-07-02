# IDS v0.1 STAGE-014 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-014`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE014-P1`
- Acceptance ID: `ACC-STAGE-014`
- Stage title: `Manifest 生成`
- Recorded at UTC: `2026-07-02T13:34:59Z`

## Goal

Confirm the manifest generation contract before implementing any scanner,
manifest writer, duplicate detector, persistence adapter, document/chunk/job
creation, evidence ledger update, audit log write, report slice, or UI slice.

This phase records evidence and engineering contracts only. It does not start
services, install dependencies, write to `IDS_DATA_ROOT`, enumerate
`00_ORIGINAL_RAW_DATA`, read or scan `/Users/linzezhang/Downloads/IDS_MetaData`,
hash raw files, write manifests, write databases, create documents, create
chunks, create jobs, generate reports, or enter Phase 2.

Marker: `STAGE014_PHASE1_MANIFEST_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Source Evidence

Read-only source check:

| Check | Result |
|---|---|
| P0 taskpack zip | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` |
| P0 taskpack zip SHA | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| Stage file inside zip | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-014_Manifest生成.md` |
| Stage file SHA-256 | `ede58960f10bc0b4537f222ca93859ed0c32060be44ade4ce105525bbe7392ad` |
| Stage execution index | STAGE-014 maps to `D03-S003`, `ACC-STAGE-014`, and `stages/STAGE-014_Manifest生成.md` |

The stage source was read directly from the user-provided v0.1 taskpack zip
without extracting or copying it into the worktree.

## Relationship To STAGE-012 And STAGE-013

STAGE-014 extends the STAGE-012 original-material read-only contract and the
STAGE-013 file-fingerprint contract. It does not replace or weaken either one.

Inherited rules:

- original files remain read-only by default;
- original files must not be moved, deleted, overwritten, normalized,
  compacted, renamed, repaired, or deduplicated in place;
- file identity must remain linked to explicit `source_uri` evidence;
- manifest identity must use real future source metadata and fingerprint
  evidence, not fake business data or fabricated examples;
- repeated observation and repeated manifest generation must be idempotent;
- same-name/different-hash and same-hash/different-path cases must preserve
  provenance and explicit conflict/duplicate states;
- failure states must be explicit and fail closed.

## Manifest Field Contract

Future implementation must treat a manifest as a bounded metadata record. It
must not embed raw source payload content, secrets, screenshots, large binary
payloads, database dumps, or unbounded text extraction.

| Field | Required meaning | Phase 1 rule |
|---|---|---|
| `source_uri` | Absolute `file://` URI for a future user-approved explicit source. | Define only; do not open, scan, or normalize real raw content. |
| `sha256` | SHA-256 fingerprint inherited from bounded read-only fingerprint evidence. | Define only; Phase 1 does not hash real raw files. |
| `file_size` | Byte length observed at the same source/fingerprint time. | Define only; do not stat real raw files in this phase. |
| `mtime` | Filesystem modification time observed with the future source evidence. | Define only; later drift checks must not rewrite source files. |
| `first_seen_at` | UTC timestamp when IDS first records the manifestable file identity. | Define only; must come from real future observation time. |
| `manifest_state` | Explicit manifest readiness or failure classification. | Define only; unknown states fail closed. |

`file_size` is the STAGE-014 field name because the P0 taskpack names it.
STAGE-013 `size` evidence may be mapped into `file_size` only when the values
are identical and the mapping does not create a second source of truth.

## Manifest Idempotency And Duplicate Rules

Phase 1 defines these rules for later phases:

- same `source_uri` and same `sha256` maps to the same manifest identity;
- same basename with different `sha256` is a conflict, not an overwrite;
- same `sha256` at different paths is duplicate content with separate
  provenance, not a deletion request;
- repeated manifest generation must not create duplicate document rows, chunk
  rows, job rows, evidence ledger facts, audit events, reports, or manifest
  records;
- a manifest candidate may be compared and rebuilt from metadata, but Phase 1
  does not write a manifest file or database record.

## Future Status Contract

Phase 1 defines status names that later phases may implement:

| State | Meaning | Required behavior |
|---|---|---|
| `MANIFEST_READY` | A bounded metadata-only manifest can be generated. | Allow future manifest candidate or record creation under explicit gate. |
| `MANIFEST_NOT_CONFIGURED` | No approved source URI or fingerprint evidence exists. | Fail closed and request configuration. |
| `MANIFEST_SOURCE_BLOCKED` | Source path is unsafe, absent, non-local, or raw metadata root. | Block before side effects. |
| `MANIFEST_FINGERPRINT_MISSING` | Required fingerprint evidence is absent. | Do not fabricate hash or size metadata. |
| `MANIFEST_HASH_CONFLICT` | Same logical source/name has conflicting hashes. | Preserve both facts and require review. |
| `MANIFEST_DUPLICATE_CONTENT` | Same hash appears at multiple source URIs. | Preserve provenance and avoid duplicate persistence. |
| `MANIFEST_SCHEMA_UNSAFE` | Future manifest shape would store raw payload or secrets. | Block manifest write. |
| `MANIFEST_WRITE_BLOCKED` | Future manifest target is not safe or rollbackable. | Do not write manifest or database rows. |
| `MANIFEST_UNKNOWN` | Classification is incomplete. | Fail closed; do not scan, import, index, or report. |

## Allowed Phase 1 Outputs

Phase 1 may create or update only:

- `STAGE014_ENTRY_CONTRACT.md`;
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
- write manifest files, manifest database rows, audit log entries, evidence
  ledger entries, report files, document rows, chunk rows, or job rows;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated;
- enter Phase 2 in the same run.

## Evidence And Validation Plan

Phase 1 validation is evidence-based:

- confirm P0 STAGE-014 taskpack SHA-256;
- confirm stage execution index maps STAGE-014 to `D03-S003` and
  `ACC-STAGE-014`;
- confirm STAGE-012 and STAGE-013 evidence are predecessor boundaries;
- run Stage005 governance regression RED/GREEN for `IDS-V0_1-STAGE014-P1`;
- run `validate_stage005_governance_regression.py`;
- run pursuing-goal unittest discovery;
- run `check-render --project KM_IDSystem`;
- run `git diff --check`;
- run semantic validate only as a known sparse-worktree diagnostic and do not
  expand unrelated projects.

Phase 2 may implement a small bounded manifest-generation slice only after this
boundary is committed.

## Validation Results

Final local validation for this run:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected with `Ran 20 tests ... FAILED (failures=3)` because
  `IDS-V0_1-STAGE014-P1`, `STAGE014_ENTRY_CONTRACT.md`, and
  `STAGE014_PHASE1_SCOPE_BOUNDARY.md` were not yet accepted.
- Stage005 governance GREEN:
  the same command returned `Ran 20 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issues=[]`, `missing_required_files=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 71 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for
  `validate_stage005_governance_regression.py` returned exit code `0`.
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

## Rollback

Rollback Phase 1 by reverting the local `IDS-V0_1-STAGE014-P1` commit. Because
Phase 1 is governance/contract only, rollback does not require data cleanup,
schema rollback, service restart, dependency restoration, manifest cleanup,
runtime database cleanup, report cleanup, external-drive cleanup, raw metadata
repair, GitHub cleanup, or app-entry reinstall.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.

## Decision

STAGE-014 Phase 1 is allowed to complete when this boundary, the entry
contract, the batch lock, the roadmap, the event log, validator/test updates,
and rendered owner entries all point to `IDS-V0_1-STAGE014-P1`; upload remains
blocked until STAGE-011..020 are complete, reviewed, repaired, batch-gated,
and app entries are reinstalled.
