# IDS v0.1 STAGE-016 Phase 4 Closeout

## Identity

- Stage: `STAGE-016`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE016-P4`
- Acceptance ID: `ACC-STAGE-016`
- Stage title: `导入幂等键`
- Recorded at UTC: `2026-07-02T19:00:10Z`

## Goal

Close out STAGE-016 with import-idempotency delivery evidence,
idempotency-key examples, duplicate/conflict/unsupported-state summaries,
original-file protection proof, whole-stage review, rollback steps, and
Chinese owner feedback.

Marker: `STAGE016_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE017`.

## Delivered Contract

STAGE-016 now has a bounded metadata-only import-idempotency path:

- Phase 1 defined original-material protection, source identity fields,
  manifest compatibility, duplicate-state inheritance, idempotency rules, and
  failure states.
- Phase 2 implemented `check_import_idempotency.py`, which derives
  deterministic file and optional batch idempotency keys from explicit local
  `file://` inputs without persistence writes.
- Phase 3 validated same-file/same-hash repeat, same-name/different-hash
  conflict, same-hash/different-path duplicate content, repeated import
  no-persistence, and original hash stability.
- Phase 4 records closeout, whole-stage review, rollback, and owner-facing
  guidance.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no import-record write;
- no persisted manifest file write;
- no database write;
- no index write;
- no document, chunk, or job creation;
- no evidence ledger or audit log write;
- no report generation;
- no raw metadata database read;
- no external API call, service start, dependency install, or runtime output.

## Import Idempotency Example

The import-idempotency example is a field contract proven by focused tests
against tracked governance documents. It is not a committed runtime import
ledger, not a production database primary key, and not a business corpus
sample.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | STAGE-013 fingerprint record |
| `source_path` | normalized local path for the explicit file | STAGE-013 fingerprint record |
| `basename` | source filename for same-name conflict grouping | STAGE-015 duplicate identity |
| `sha256` | exact byte fingerprint inherited from STAGE-013 | STAGE-013 fingerprint record |
| `file_size` | byte length mapped from fingerprint evidence | STAGE-013 fingerprint record |
| `mtime` | filesystem modification time at fingerprint time | STAGE-013 fingerprint record |
| `first_seen_at` | first observation timestamp | STAGE-013 fingerprint record |
| `manifest_identity` | metadata-only manifest identity | STAGE-014 compatible identity |
| `duplicate_state` | duplicate/conflict classification | STAGE-015 duplicate detection |
| `import_checked_at` | idempotency comparison timestamp | STAGE-016 import slice |
| `import_idempotency_key` | deterministic `ids-import-file-sha256-{sha256}` value | STAGE-016 import slice |
| `batch_idempotency_key` | optional deterministic key from approved batch ID plus bounded file keys | STAGE-016 import slice |

The example proves that import identity can be rebuilt and compared from
metadata before any future persistence write. It does not authorize production
import, indexing, deletion, merge, deduplication, overwrite, or report
generation.

## Duplicate, Conflict, And Idempotency Summary

Phase 3 scenario evidence proves:

| Scenario | Import result | Persistence effect |
|---|---|---|
| same file and same hash | `IMPORT_SINGLE_REPEAT`, one import record and one duplicate input | no duplicate document/chunk/job/index/import write |
| same name and different hash | `IMPORT_KEY_CONFLICT`, one key conflict and one version conflict | no overwrite, merge, or delete |
| same hash and different path | `IMPORT_DUPLICATE_CONTENT`, duplicate content remains explicit | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0`, `index_delta=0`, `import_write_delta=0`, `manifest_write_delta=0`, `duplicate_write_delta=0` | no persistence adapter writes |
| original hash stability | same `sha256` and size before/after validation | original source unchanged |

These are structural validation results, not production-data findings. No real
business corpus or raw metadata database was scanned.

## Unsupported Or Blocked Inputs

The Stage 016 tests and inherited Stage 013/014/015 behavior explicitly cover
blocked or unsupported input states:

| Input type | State | Required behavior |
|---|---|---|
| no source URI | `IMPORT_NOT_CONFIGURED` | fail closed |
| missing explicit file | `IMPORT_SOURCE_BLOCKED` | record failure; do not skip silently |
| raw metadata root path | `IMPORT_SOURCE_BLOCKED` | block before import-idempotency work |
| same basename with different hash | `IMPORT_KEY_CONFLICT` | preserve both facts as review candidate |
| same hash at different paths | `IMPORT_DUPLICATE_CONTENT` | preserve provenance |
| missing fingerprint evidence | `IMPORT_FINGERPRINT_MISSING` | do not fabricate hash or size |
| unsafe future write target shape | `IMPORT_WRITE_BLOCKED` | block database/index/evidence/audit/report writes |
| incomplete classification | `IMPORT_UNKNOWN` | fail closed |

No unsupported real source file was opened or inspected in this phase.

## Original-File Protection Proof

Original-file protection is proven by the Stage 016 focused scenario report:

- tracked governance documents are used as real repository source evidence;
- temporary process-owned copies are used only for structural duplicate or
  conflict scenarios;
- the scenario report records before/after SHA-256 and size for the explicit
  source;
- document, chunk, job, index, import, manifest, and duplicate write deltas are
  all `0`;
- raw metadata root paths are blocked before import-idempotency work.

This proof does not include raw metadata database contents, raw filenames,
table contents, row values, schema details, credentials, private business
values, or derived dumps.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-016` had no Phase 4 closeout evidence.
   - Resolution: this file records delivery evidence, idempotency examples,
     duplicate/conflict/unsupported states, rollback, and Chinese owner
     feedback.
2. Stage005 governance regression did not yet accept the completed Phase 4
   closeout task-id state.
   - Resolution: the test was written first and failed; validator state
     acceptance was then extended for `IDS-V0_1-STAGE016-P4`.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE016-P4`, while keeping STAGE-017 pending.
4. Batch upload risk remained active after STAGE-016 local completion.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-017 through STAGE-020 remain pending.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `IDS_MetaData` content was read,
     listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned,
     or committed.

No finding required runtime code changes beyond already completed Phase 2/3
metadata-only helper behavior and governance closeout.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `IMPORT_NOT_CONFIGURED` | no approved explicit source URI exists | configure a user-approved explicit `file://` input |
| `IMPORT_SOURCE_BLOCKED` | source path is absent, unsafe, unreadable, non-local, or raw metadata root | correct path/permission outside Codex; do not mutate source |
| `IMPORT_FINGERPRINT_MISSING` | required fingerprint evidence is absent | rerun bounded STAGE-013 fingerprint preflight |
| `IMPORT_KEY_CONFLICT` | same logical name has different content hashes or key conflicts | review as version/conflict; do not overwrite |
| `IMPORT_DUPLICATE_CONTENT` | same content hash appears through multiple source paths | preserve provenance; do not delete originals |
| `IMPORT_SINGLE_REPEAT` | repeated single-file input points to an already observed identity | keep document/chunk/job/index/import writes at zero unless a later gate allows persistence |
| `IMPORT_WRITE_BLOCKED` | future write target is not safe or rollbackable | do not write import records, database, index, evidence, audit, or reports |
| `IMPORT_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

## Non-Recoverable Or Stop States

Stop immediately if a run would:

- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create unbounded import records, manifests, evidence ledgers, audit logs,
  indexes, embeddings, OCR outputs, runtime databases, backup payloads,
  reports, or document/chunk/job rows without a later explicit stage gate;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated.

## Chinese Owner Feedback

STAGE-016 已在本地完成。当前系统已经具备一个只读、可测试的导入幂等键
能力：对明确传入的本地文件身份，可以生成稳定的 import idempotency key，并把
“同一文件重复导入”“同内容不同路径”“同名但内容不同”和“无法处理的输入”拆成
明确状态。

业务上可以把它理解为：系统现在能先判断“这次导入是否已经处理过、是否是重复内容、
是否是版本冲突”，再决定未来是否允许写入 document、chunk、job 或 index。当前
实现不会因为重复导入而自动生成重复记录，也不会自动删除、合并、移动、覆盖或重写
原始文件。

当前能力仍不是生产导入。它不会扫描原始目录，不会写 import ledger/database/index，
不会创建 document、chunk 或 job。真正把真实业务资料写入持久层，必须等待后续明确
Stage。

## Validation Results

Final validation completed in this Phase 4 run:

- Stage005 RED failed as expected with `Ran 31 tests ... FAILED
  (failures=1)` because `IDS-V0_1-STAGE016-P4` was not yet accepted by the
  governance state machine.
- Stage005 intermediate RED failed as expected with `Ran 31 tests ... FAILED
  (failures=1)` because `STAGE016_PHASE4_CLOSEOUT.md` was missing as required
  evidence.
- Stage005 GREEN passed 31 tests.
- Stage016 focused import-idempotency tests passed 8 tests.
- Stage005 validator returned `valid=true` with no issues, no missing required
  files, no event JSON errors, no forbidden changed paths, and no unexpected
  changed paths.
- Full IDS v0.1 pursuing-goal unittest discover passed 104 tests.
- `py_compile` passed for `check_import_idempotency.py` and the Stage005
  validator.
- events JSONL parsing returned `events_jsonl_ok`.
- bundled Python `render --project KM_IDSystem --write` updated the three
  rendered owner files, and `check-render --project KM_IDSystem` returned
  `drift_count=0` and `reference_issue_count=0`.
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
  databases, persisted manifests, import ledgers, duplicate ledgers, evidence
  ledgers, document rows, chunk rows, job rows, indexes, OCR output, Embedding
  output, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-017.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE016-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, import-ledger cleanup, manifest cleanup, runtime
database cleanup, report cleanup, external-drive cleanup, raw metadata repair,
GitHub cleanup, or app-entry reinstall because Phase 4 writes only tracked
source/test/governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
