# IDS v0.1 STAGE-017 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-017`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE017-P1`
- Acceptance ID: `ACC-STAGE-017`
- Stage title: `原始资料回归测试`
- Recorded at UTC: `2026-07-02T19:11:14Z`

## Goal

Define the original-material regression-test boundary before any scan, resume,
offline-drive recovery adapter, database write, manifest write, index write, or
runtime output is implemented.

Marker: `STAGE017_PHASE1_ORIGINAL_MATERIAL_REGRESSION_BOUNDARY_NO_IMPLEMENTATION_NO_PHASE2`.

## P0 Evidence

| Item | Value |
|---|---|
| P0 taskpack zip SHA-256 | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| P0 stage file | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-017_原始资料回归测试.md` |
| P0 stage file SHA-256 | `29d9e298d0a79367405cf7c513dbabec0f9d2fcf15f3dac8719c0cd82fe56954` |
| Stage index mapping | `STAGE-017,D03-S006,原始资料回归测试,v0.1,D03,ACC-STAGE-017` |

## Inherited Boundary From STAGE-012 Through STAGE-016

| Upstream stage | Inherited rule |
|---|---|
| `STAGE-012` | Original materials and raw metadata roots remain read-only; source identity is metadata-only. |
| `STAGE-013` | File identity requires bounded `source_uri`, `sha256`, `file_size`, `mtime`, and `first_seen_at`. |
| `STAGE-014` | Manifest decisions are metadata-only and must not write persisted manifests in Phase 1. |
| `STAGE-015` | Duplicate and conflict states must be explicit and must preserve provenance. |
| `STAGE-016` | Import idempotency must keep document, chunk, job, index, import, manifest, duplicate, evidence, audit, and report deltas at zero unless a later gate authorizes writes. |

## Regression Field Contract

Phase 1 defines these fields for later implementation and validation. It does
not create, persist, or backfill them.

| Field | Required meaning |
|---|---|
| `source_uri` | explicit local source URI approved by the caller or future user workflow |
| `sha256` | byte-stable source fingerprint inherited from bounded identity evidence |
| `file_size` | source byte length at the fingerprint observation |
| `mtime` | filesystem modification time at the fingerprint observation |
| `first_seen_at` | first approved observation timestamp for this source identity |
| `manifest_identity` | metadata-only manifest identity, not a persisted manifest write |
| `duplicate_state` | duplicate/conflict classification inherited from duplicate detection |
| `import_idempotency_key` | stable key used to avoid duplicate import side effects |
| `scan_attempt_id` | future bounded scan attempt identity, not a runtime row in Phase 1 |
| `scan_checkpoint_id` | future checkpoint identity for interrupted/resumed scans |
| `resume_token` | future metadata-only resume token derived from an approved checkpoint |
| `drive_state` | future removable-drive state such as online, offline, reconnected, or blocked |

## Regression Rules

### Repeated Scan

- A repeated scan of the same `source_uri`, `sha256`, `file_size`, `mtime`, and
  compatible manifest identity must resolve to the same source identity and
  import idempotency key.
- A new observation timestamp must not create a new document identity by
  itself.
- Same hash at a different path may share content identity while preserving
  separate provenance.
- Same basename with a different hash remains a conflict/version candidate,
  not an overwrite.
- Repeated scan must keep document, chunk, job, index, import, manifest,
  duplicate, evidence, audit, and report deltas at `0` unless a later explicit
  gate authorizes a controlled write.

### Breakpoint Resume

- Resume may continue only from approved metadata state: source identity,
  manifest identity, import idempotency key, scan checkpoint, and resume token.
- If checkpoint state is missing, incompatible, or ambiguous, the system must
  fail closed with an explicit state instead of inventing progress.
- Resume must not rescan or rehash the raw metadata root and must not read,
  list, open, dump, copy, move, delete, modify, or scan
  `/Users/linzezhang/Downloads/IDS_MetaData`.

### Removable Drive Offline Recovery

- Offline drive recovery must pause or fail closed when the source is absent.
- Reconnected drive recovery must revalidate bounded metadata identity before
  considering any continuation.
- Path equality alone is insufficient after reconnection; the future check must
  compare fingerprint and manifest identity.
- Recovery must never move, repair, rename, deduplicate, normalize, or overwrite
  original files.

## Phase 1 State Names

These state names are reserved for later implementation and validation. Phase 1
does not emit runtime records.

| State | Meaning |
|---|---|
| `REGRESSION_READY` | bounded metadata is sufficient for a future regression check |
| `REGRESSION_NOT_CONFIGURED` | no approved source or checkpoint identity exists |
| `REGRESSION_SOURCE_BLOCKED` | source path is absent, unsafe, unreadable, non-local, or raw metadata root |
| `REGRESSION_CHECKPOINT_MISSING` | interrupted/resume state lacks required checkpoint identity |
| `REGRESSION_RESUME_PENDING` | future resume can continue after metadata revalidation |
| `REGRESSION_DRIVE_OFFLINE` | removable source is unavailable and must not be mutated |
| `REGRESSION_DRIVE_RECONNECTED_REVALIDATION` | source reappeared and must be revalidated before continuation |
| `REGRESSION_REPEAT_SCAN` | repeated scan compares to an existing identity without duplicate writes |
| `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | duplicate document/chunk/job/index/import/manifest registration is blocked |
| `REGRESSION_HASH_STABLE` | before/after identity remains byte-stable |
| `REGRESSION_HASH_DRIFT` | hash or size changed and requires conflict handling |
| `REGRESSION_WRITE_BLOCKED` | a proposed persistence/report/audit/index write is outside the current gate |
| `REGRESSION_UNKNOWN` | classification is incomplete; fail closed |

## Phase 1 Allowed Outputs

- This scope-boundary document.
- The STAGE-017 entry contract.
- Stage005 governance-regression validator and unit-test updates that only
  accept the Phase 1 state.
- Roadmap, batch-lock, event-log, and rendered owner-file updates reflecting
  `IDS-V0_1-STAGE017-P1`.

## Phase 1 Forbidden Outputs

- No scanner, resume adapter, offline-drive recovery adapter, database adapter,
  manifest writer, import writer, index writer, report writer, OCR, embedding,
  file copier, or directory crawler.
- No document, chunk, job, index, import, duplicate, evidence, audit, manifest,
  report, runtime database, cache, output, or backup writes.
- No service start, dependency install, external API call, GitHub push, PR,
  merge, app reinstall, or Phase 2 work.
- No read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  of `/Users/linzezhang/Downloads/IDS_MetaData` content.

## Validation Results

Final validation completed in this Phase 1 run:

- Stage005 RED failed as expected with `Ran 32 tests ... FAILED
  (failures=3)` because `IDS-V0_1-STAGE017-P1` was not yet accepted by the
  governance state machine and `STAGE017_*` evidence paths were not allowed.
- Stage005 intermediate RED failed as expected with `Ran 32 tests ... FAILED
  (failures=1)` because `STAGE017_ENTRY_CONTRACT.md` and
  `STAGE017_PHASE1_SCOPE_BOUNDARY.md` were missing as required evidence.
- Stage005 GREEN passed 32 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 105 tests.
- `py_compile` passed for the Stage005 validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  Chinese owner files; bundled `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- exact old underscored task-id variant scan returned no hits.
- Legacy path/name scan found only historical migration-policy, stale-path,
  do-not-revive, or scanner-rule references; this Phase 1 document does not
  add new legacy path literals.
- semantic validate remains diagnostic-only with 29 known sparse root-governance
  or registered-project missing paths and no new `KM_IDSystem` semantic error.
- Phase 1 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No service start, dependency install, scanner/resume/offline-drive adapter,
  manifest/database/index/import writer, document/chunk/job creation, runtime
  output, external API call, GitHub upload, PR, merge, app reinstall, or Phase
  2 work was performed.

## Owner Feedback Draft

STAGE-017 Phase 1 只定义“重复扫描、断点续扫、移动硬盘离线恢复”如何被安全验证。
当前不会扫描真实资料目录，不会打开或读取本机 raw metadata 数据库内容，不会写入
document、chunk、job、index、manifest、import、报告或审计记录，也不会自动删除、
合并、移动、覆盖或重写原始文件。

## Rollback

Revert the STAGE-017 Phase 1 documents, Stage005 validator/test updates,
batch-lock, roadmap/event, and rendered owner-file changes only. Do not touch
`00_ORIGINAL_RAW_DATA`, `/Users/linzezhang/Downloads/IDS_MetaData`, existing
manifests, evidence ledgers, audit logs, indexes, delivered reports, runtime
data, app entries, GitHub state, or Phase 2.
