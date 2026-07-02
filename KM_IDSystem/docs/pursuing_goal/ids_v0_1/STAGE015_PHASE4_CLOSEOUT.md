# IDS v0.1 STAGE-015 Phase 4 Closeout

## Identity

- Stage: `STAGE-015`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE015-P4`
- Acceptance ID: `ACC-STAGE-015`
- Stage title: `重复文件检测`
- Recorded at UTC: `2026-07-02T14:43:27Z`

## Goal

Close out STAGE-015 with duplicate-detection delivery evidence, duplicate and
conflict summaries, unsupported-input handling, original-file protection proof,
whole-stage review, rollback steps, and Chinese owner feedback.

Marker: `STAGE015_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE016`.

## Delivered Contract

STAGE-015 now has a bounded metadata-only duplicate-file detection path:

- Phase 1 defined the duplicate detection fields, source protection boundary,
  idempotency, same-hash duplicate states, same-name conflict states, repeated
  import rules, version-conflict rules, and failure-state contract.
- Phase 2 implemented `check_duplicate_files.py`, which compares explicit
  local `file://` fingerprint and manifest-compatible metadata without
  persistence writes.
- Phase 3 validated same-file/same-hash, same-name/different-hash,
  same-hash/different-path, repeated import without persistence, and original
  hash stability.
- Phase 4 records closeout, whole-stage review, rollback, and owner-facing
  guidance.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no persisted duplicate ledger write;
- no persisted manifest file write;
- no database write;
- no document, chunk, or job creation;
- no evidence ledger or audit log write;
- no report generation;
- no raw metadata database read;
- no external API call, service start, dependency install, or runtime output.

## Duplicate Detection Example

The duplicate detection example is a field contract proven by focused tests
against tracked governance documents. It is not a committed runtime duplicate
ledger and not a business corpus sample.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | STAGE-013 fingerprint record |
| `source_path` | normalized local path for the explicit file | STAGE-013 fingerprint record |
| `basename` | source filename for same-name comparison | STAGE-015 duplicate slice |
| `sha256` | exact byte fingerprint inherited from STAGE-013 | STAGE-013 fingerprint record |
| `file_size` | byte length mapped from the fingerprint `file_size` field | STAGE-013 fingerprint record |
| `mtime` | filesystem modification time at fingerprint time | STAGE-013 fingerprint record |
| `first_seen_at` | first observation timestamp | STAGE-013 fingerprint record |
| `duplicate_checked_at` | duplicate comparison timestamp | STAGE-015 duplicate slice |
| `content_identity_id` | deterministic `ids-duplicate-sha256-{sha256}` value | STAGE-015 duplicate slice |
| `duplicate_state` | readiness, duplicate, conflict, repeat, blocked, or unknown classification | STAGE-015 state mapping |

The example proves that duplicate identity can be rebuilt and compared from
metadata. It does not authorize production deletion, merging, deduplication, or
persistence.

## Duplicate And Conflict Summary

Phase 3 scenario evidence proves:

| Scenario | Duplicate result | Persistence effect |
|---|---|---|
| same file and same hash | `DUPLICATE_BATCH_REPEAT`, one identity and one duplicate input | no duplicate document/chunk/job |
| same name and different hash | `DUPLICATE_SAME_NAME_DIFFERENT_HASH`, one version conflict | no overwrite, merge, or delete |
| same hash and different path | `DUPLICATE_SAME_HASH_DIFFERENT_PATH`, one duplicate-content group | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0`, `duplicate_write_delta=0`, `manifest_write_delta=0` | no persistence adapter writes |
| original hash stability | same `sha256` and size before/after validation | original source unchanged |

These are structural validation results, not production-data findings. No real
business corpus or raw metadata database was scanned.

## Unsupported Or Blocked Inputs

The Stage 015 tests and inherited Stage 013/014 behavior explicitly cover
blocked or unsupported input states:

| Input type | State | Required behavior |
|---|---|---|
| no source URI | `DUPLICATE_NOT_CONFIGURED` | fail closed |
| missing explicit file | `DUPLICATE_SOURCE_BLOCKED` | record failure; do not skip silently |
| raw metadata root path | `DUPLICATE_SOURCE_BLOCKED` | block before duplicate work |
| unreadable explicit file | `DUPLICATE_SOURCE_BLOCKED` | record failure; do not mutate source |
| same basename with different hash | `DUPLICATE_SAME_NAME_DIFFERENT_HASH` | preserve both facts as review candidate |
| same hash at different paths | `DUPLICATE_SAME_HASH_DIFFERENT_PATH` | preserve provenance |
| missing fingerprint evidence | `DUPLICATE_FINGERPRINT_MISSING` | do not fabricate hash or size |
| unsafe future write target shape | `DUPLICATE_WRITE_BLOCKED` | block duplicate-ledger/database write |
| incomplete classification | `DUPLICATE_UNKNOWN` | fail closed |

No unsupported real source file was opened or inspected in this phase.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-015` had no Phase 4 closeout evidence.
   - Resolution: this file records delivery evidence, scenario summaries,
     unsupported states, rollback, and Chinese owner feedback.
2. Stage005 governance regression did not yet accept the completed Phase 4
   closeout task-id state.
   - Resolution: the test was written first and failed; validator state
     acceptance was then extended for `IDS-V0_1-STAGE015-P4`.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE015-P4`, while keeping STAGE-016 pending.
4. Batch upload risk remained active after STAGE-015 local completion.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-016 through STAGE-020 remain pending.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `IDS_MetaData` content was read,
     listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned,
     or committed.

No finding required runtime code changes beyond already completed Phase 2/3
metadata-only helper behavior and governance closeout.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `DUPLICATE_NOT_CONFIGURED` | no approved explicit source URI exists | configure a user-approved explicit `file://` input |
| `DUPLICATE_SOURCE_BLOCKED` | source path is absent, unsafe, unreadable, non-local, or raw metadata root | correct path/permission outside Codex; do not mutate source |
| `DUPLICATE_FINGERPRINT_MISSING` | required fingerprint evidence is absent | rerun bounded STAGE-013 fingerprint preflight |
| `DUPLICATE_SAME_NAME_DIFFERENT_HASH` | same logical name has different content hashes | review as version/conflict; do not overwrite |
| `DUPLICATE_SAME_HASH_DIFFERENT_PATH` | same hash appears at multiple paths | preserve provenance; do not delete originals |
| `DUPLICATE_BATCH_REPEAT` | repeated batch input points to an already observed identity | keep document/chunk/job/duplicate writes at zero unless a later gate allows persistence |
| `DUPLICATE_WRITE_BLOCKED` | future write target is not safe or rollbackable | do not write duplicate ledger/database |
| `DUPLICATE_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

## Non-Recoverable Or Stop States

Stop immediately if a run would:

- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create unbounded duplicate ledgers, manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  reports, or document/chunk/job rows without a later explicit stage gate;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated.

## Chinese Owner Feedback

STAGE-015 已在本地完成。当前系统已经具备一个只读、可测试的重复文件检测
能力：对明确传入的本地文件身份，可以识别同一文件重复导入、同内容出现在不同
路径、同名但内容不同、以及需要人工复核的版本冲突。

业务上可以把它理解为：系统现在能把“重复”“同名冲突”“重复批量导入”和
“无法处理的输入”拆成明确状态，而不是静默跳过或直接覆盖。系统不会因此自动删除、
合并、移动、覆盖或重写原始文件。

当前能力仍不是生产导入。它不会扫描原始目录，不会写 duplicate ledger/database，
不会创建 document、chunk 或 job。真正把真实业务资料写入持久层，必须等待后续
明确 Stage。

## Validation Results

Final validation completed in this Phase 4 run:

- Stage005 RED failed as expected with 27 tests and 1 failure because
  `IDS-V0_1-STAGE015-P4` was not yet accepted by the governance state machine.
- Stage005 GREEN passed 27 tests.
- Stage015 focused duplicate-detection tests passed 8 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 92 tests.
- `py_compile` passed for `check_duplicate_files.py` and the Stage005
  validator.
- events JSONL parsing returned `events_jsonl_ok`.
- `render --project KM_IDSystem --write` updated the three rendered owner
  files, and `check-render --project KM_IDSystem` returned `drift_count=0` and
  `reference_issue_count=0`.
- `git diff --check` passed.
- old underscored task-id variant scan returned no hits.
- legacy path/name scan still shows only historical migration-policy,
  compatibility-scan, stale-path, or do-not-revive references.
- semantic validate remains diagnostic-only under the sparse worktree, with 29
  known missing root-governance or registered-project paths and no new
  `KM_IDSystem` semantic error.

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
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-016.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE015-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, duplicate-ledger cleanup, manifest cleanup, runtime
database cleanup, report cleanup, external-drive cleanup, raw metadata repair,
GitHub cleanup, or app-entry reinstall because Phase 4 writes only tracked
source/test/governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
