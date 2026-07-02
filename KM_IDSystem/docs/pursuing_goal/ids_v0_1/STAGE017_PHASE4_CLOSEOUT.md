# IDS v0.1 STAGE-017 Phase 4 Closeout

## Identity

- Stage: `STAGE-017`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE017-P4`
- Acceptance ID: `ACC-STAGE-017`
- Stage title: `原始资料回归测试`
- Recorded at UTC: `2026-07-02T19:41:13Z`

## Goal

Close out STAGE-017 with original-material regression delivery evidence,
manifest/checkpoint examples, duplicate/conflict/unsupported-state summaries,
original-file protection proof, whole-stage review, rollback steps, and
Chinese owner feedback.

Marker: `STAGE017_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE018`.

## Delivered Contract

STAGE-017 now has a bounded metadata-only original-material regression path:

- Phase 1 defined repeated scan, breakpoint resume, removable-drive offline
  recovery, no-mutation rules, state names, and rollback boundaries.
- Phase 2 implemented `check_original_regression.py`, which evaluates explicit
  local `file://` inputs, repeated scan, resume checkpoint, offline drive,
  hash drift, blocked source, and zero persistence deltas.
- Phase 3 validated same-file/same-hash, same-name/different-hash,
  same-hash/different-path, matching resume checkpoint, offline drive,
  checkpoint hash drift, duplicate import no-persistence, and original hash
  stability.
- Phase 4 records closeout, whole-stage review, rollback, and owner-facing
  guidance.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no production scanner, resume adapter, or offline-drive recovery adapter;
- no manifest file write;
- no database write;
- no index write;
- no document, chunk, or job creation;
- no import, duplicate, evidence, audit, report, or runtime-output write;
- no raw metadata database read;
- no external API call, service start, dependency install, or GitHub upload.

## Manifest And Checkpoint Examples

The examples below are field contracts proven by focused tests against tracked
governance documents. They are not committed runtime manifests, production
database rows, business-corpus samples, generated reports, or raw metadata
extracts.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | Stage017 regression record |
| `source_path` | normalized local path for the explicit file | Stage013 inherited fingerprint |
| `basename` | source filename for same-name conflict grouping | Stage015 duplicate identity |
| `sha256` | exact byte fingerprint for the explicit file | Stage013 inherited fingerprint |
| `file_size` | byte length mapped from fingerprint evidence | Stage013 inherited fingerprint |
| `mtime` | filesystem modification time at fingerprint time | Stage013 inherited fingerprint |
| `first_seen_at` | first observation timestamp | Stage013 inherited fingerprint |
| `scan_checked_at` | regression-check timestamp | Stage017 regression slice |
| `manifest_identity` | metadata-only manifest identity | Stage014 compatible identity |
| `duplicate_state` | duplicate/conflict classification | Stage015 duplicate detection |
| `import_state` | inherited import-idempotency state | Stage016 import-idempotency slice |
| `import_idempotency_key` | deterministic import key for the explicit source identity | Stage016 import-idempotency slice |
| `content_identity_id` | content identity for same-hash comparison | Stage016 import-idempotency slice |
| `scan_checkpoint_id` | deterministic metadata-only checkpoint identifier | Stage017 regression slice |
| `resume_token` | deterministic resume token from bounded metadata fields | Stage017 regression slice |
| `drive_state` | online/offline/missing drive state supplied by caller | Stage017 regression slice |

The example proves that original-material regression checks can be rebuilt and
compared from metadata before any future persistence write. It does not
authorize production import, indexing, deletion, merge, deduplication,
overwrite, report generation, or automatic recovery.

## Duplicate, Conflict, And Unsupported-State Summary

Phase 3 scenario evidence proves:

| Scenario | Regression result | Required behavior |
|---|---|---|
| same file and same hash | `REGRESSION_REPEAT_SCAN` | collapse repeated input to one identity without duplicate registration writes |
| same basename and different hash | `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | preserve both facts as conflict/version candidates; do not overwrite |
| same hash and different path | `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | preserve provenance; do not delete either original |
| matching resume checkpoint | `REGRESSION_RESUME_PENDING` | allow future continuation only from matching metadata checkpoint |
| offline removable drive | `REGRESSION_DRIVE_OFFLINE` | fail closed before source identity evaluation |
| checkpoint/source hash drift | `REGRESSION_HASH_DRIFT` | block silent continuation and require review |
| repeated import no-persistence | `REGRESSION_REPEAT_SCAN` with all write deltas at `0` | no document/chunk/job/index/import/manifest/duplicate/evidence/audit/report/database write |
| original hash stable | `REGRESSION_HASH_STABLE` | before/after SHA-256 and size remain unchanged |

Blocked or recoverable states remain explicit:

| State | Required behavior |
|---|---|
| `REGRESSION_NOT_CONFIGURED` | fail closed until an approved explicit source URI exists |
| `REGRESSION_SOURCE_BLOCKED` | block unsafe, absent, non-local, or raw metadata root paths before regression work |
| `REGRESSION_CHECKPOINT_MISSING` | require approved metadata checkpoint for resume |
| `REGRESSION_HASH_DRIFT` | stop and review before any continuation |
| `REGRESSION_DRIVE_OFFLINE` | wait for owner-approved drive availability; do not infer source identity |
| `REGRESSION_WRITE_BLOCKED` | block database, index, evidence, audit, report, manifest, import, and duplicate writes |
| `REGRESSION_UNKNOWN` | fail closed and gather stronger evidence |

These are structural validation results, not production-data findings. No real
business corpus or raw metadata database was scanned.

## Original-File Protection Proof

Original-file protection is proven by the Stage 017 focused scenario report:

- tracked governance documents are used as real repository source evidence;
- temporary process-owned copies are used only for structural duplicate or
  conflict path scenarios;
- the scenario report records before/after SHA-256 and size for the explicit
  source;
- document, chunk, job, index, import, manifest, duplicate, evidence, audit,
  report, and database write deltas are all `0`;
- offline-drive recovery fails closed before source identity evaluation;
- raw metadata root paths are blocked before source identity, hashing, resume,
  import-idempotency, or regression work.

This proof does not include raw metadata database contents, raw filenames,
table contents, row values, schema details, credentials, private business
values, or derived dumps.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-017` had no Phase 4 closeout evidence.
   - Resolution: this file records delivery evidence, manifest/checkpoint
     examples, duplicate/conflict/unsupported states, rollback, and Chinese
     owner feedback.
2. Stage005 governance regression did not yet accept the completed Phase 4
   closeout task-id state.
   - Resolution: the test was written first and failed; validator state
     acceptance was then extended for `IDS-V0_1-STAGE017-P4`.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE017-P4`, while keeping STAGE-018 pending.
4. Batch upload risk remains active after STAGE-017 local completion.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-018 through STAGE-020 remain pending.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `/Users/linzezhang/Downloads/IDS_MetaData`
     content was read, listed, opened, hashed, copied, moved, deleted,
     modified, dumped, scanned, or committed.

No finding required runtime code changes beyond already completed Phase 2/3
metadata-only helper behavior and governance closeout.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `REGRESSION_NOT_CONFIGURED` | no approved explicit source URI exists | configure a user-approved explicit `file://` input |
| `REGRESSION_SOURCE_BLOCKED` | source path is absent, unsafe, unreadable, non-local, or raw metadata root | correct path/permission outside Codex; do not mutate source |
| `REGRESSION_CHECKPOINT_MISSING` | resume was requested without approved checkpoint | rerun bounded metadata preflight and save checkpoint only after a later gate authorizes persistence |
| `REGRESSION_RESUME_PENDING` | checkpoint matches current source metadata | continue only under a future explicit resume gate |
| `REGRESSION_HASH_DRIFT` | checkpoint and current source metadata no longer match | stop and review source/version history; do not silently continue |
| `REGRESSION_DRIVE_OFFLINE` | removable drive is unavailable | wait for owner-approved drive availability; do not infer source state |
| `REGRESSION_DUPLICATE_REGISTRATION_BLOCKED` | repeated or conflicting identity could cause duplicate registration | preserve provenance and review; do not delete or merge originals |
| `REGRESSION_REPEAT_SCAN` | repeated input points to an already observed identity | keep write deltas at zero unless a later gate allows persistence |
| `REGRESSION_WRITE_BLOCKED` | future write target is not safe or rollbackable | do not write manifest, import, duplicate, evidence, audit, report, index, or database records |
| `REGRESSION_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

## Non-Recoverable Or Stop States

Stop immediately if a run would:

- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create unbounded scanner output, resume checkpoints, manifests, evidence
  ledgers, audit logs, indexes, embeddings, OCR outputs, runtime databases,
  backup payloads, reports, imports, duplicate ledgers, or document/chunk/job
  rows without a later explicit stage gate;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated.

## Chinese Owner Feedback

STAGE-017 已在本地完成。当前系统已经具备一个只读、可测试的原始资料回归检查
能力：它能识别同一文件重复扫描、同名但内容不同、同内容不同路径、断点续扫
checkpoint 匹配、移动硬盘离线、checkpoint hash drift 和重复导入不写入。

业务上可以把它理解为：系统现在先判断“这次扫描是否重复、是否可续扫、是否因
离线盘或 hash 漂移必须停止”，再决定未来是否允许写入 manifest、database、
index、document、chunk、job、import 或报告。当前实现不会自动删除、合并、移动、
覆盖或重写原始文件，也不会因为重复扫描而写入重复登记。

当前能力仍不是生产扫描或生产恢复。它不会扫描原始目录，不会写 checkpoint、
manifest、database、index、import ledger、duplicate ledger、evidence/audit log、
report、document、chunk 或 job。真正把真实业务资料写入持久层，必须等待后续明确
Stage。

## Validation Results

Final validation completed in this Phase 4 run:

- Stage005 RED failed as expected with `Ran 35 tests ... FAILED
  (failures=1)` because `IDS-V0_1-STAGE017-P4` was not yet accepted by the
  governance state machine.
- Stage005 intermediate RED failed as expected with `Ran 35 tests ... FAILED
  (failures=1)` because `STAGE017_PHASE4_CLOSEOUT.md` was missing as required
  evidence.
- Stage005 GREEN passed 35 tests.
- Stage017 focused original-regression tests passed 9 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 117 tests.
- `py_compile` passed for `check_original_regression.py` and the Stage005
  validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  rendered owner files, and `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
- `git diff --check` passed.
- old underscored task-id variant scan returned no hits.
- legacy path/name scan still shows only historical migration-policy,
  stale-path, do-not-revive, or scanner-rule references.
- semantic validate remains diagnostic-only under the sparse worktree, with 29
  known missing root-governance or registered-project paths and no new
  `KM_IDSystem` semantic error.
- Phase 4 did not read, list, hash, open, copy, move, delete, modify, dump,
  scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content.
- No service start, dependency install, production scanner, resume adapter,
  offline-drive recovery adapter, manifest/database/index/import/duplicate/
  evidence/audit/report writer, document/chunk/job creation, runtime output,
  external API call, GitHub upload, PR, merge, app reinstall, or STAGE-018 work
  was performed.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, duplicate-ledger, report, scanner, resume, offline-drive,
  or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, persisted manifests, import ledgers, duplicate ledgers, evidence
  ledgers, document rows, chunk rows, job rows, indexes, OCR output, Embedding
  output, checkpoints, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-018.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE017-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, scanner output cleanup, resume checkpoint cleanup,
import-ledger cleanup, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, GitHub cleanup, or
app-entry reinstall because Phase 4 writes only tracked source/test/governance
evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` while rolling back this phase.
