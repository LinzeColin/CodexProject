# IDS v0.1 STAGE-013 Phase 4 Closeout

## Identity

- Stage: `STAGE-013`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE013-P4`
- Acceptance ID: `ACC-STAGE-013`
- Stage title: `文件指纹引擎`
- Recorded at UTC: `2026-07-02T13:24:12Z`

## Goal

Close out STAGE-013 with delivery evidence, duplicate/conflict/unsupported
file summaries, rollback steps, whole-stage review, and Chinese owner feedback
for the file-fingerprint engine.

Marker: `STAGE013_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE014`.

## Delivered Contract

STAGE-013 now has a bounded metadata-only file-fingerprint engine:

- Phase 1 defines the file identity, hash, manifest, idempotency, duplicate,
  extension, MIME, and raw-source protection contract.
- Phase 2 implements a read-only `file://` fingerprint preflight with
  `sha256`, `size`, `mtime`, `extension`, `mime`, `source_uri`,
  `source_path`, and `first_seen_at`.
- Phase 3 validates same-file/same-hash, same-name/different-hash,
  same-hash/different-path, duplicate import without persistence, and original
  hash stability scenarios.
- Phase 4 records closeout, review, rollback, and owner-facing guidance.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no persisted manifest write;
- no database write;
- no document, chunk, or job creation;
- no evidence ledger or audit log write;
- no raw metadata database read;
- no external API call, service start, or runtime output generation.

## Metadata-Only Manifest Candidate Example

The manifest candidate remains an in-memory report candidate, not a persisted
manifest file.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | Phase 2 fingerprint slice |
| `source_path` | normalized local path for the explicit file | Phase 2 fingerprint slice |
| `sha256` | exact byte fingerprint for the explicit file | Phase 2 fingerprint slice |
| `size` | byte length observed at fingerprint time | Phase 2 fingerprint slice |
| `file_size` | compatibility alias for canonical `size` | Phase 2 fingerprint slice |
| `mtime` | filesystem modification time at fingerprint time | Phase 2 fingerprint slice |
| `extension` | lowercase filename suffix | Phase 2 fingerprint slice |
| `mime` | best-effort standard-library MIME inference | Phase 2 fingerprint slice |
| `first_seen_at` | deterministic UTC first-seen timestamp in tests | Phase 2 fingerprint slice |
| `state` | `FINGERPRINT_READY` or explicit failure state | Phase 2/3 state contract |

Focused tests use tracked governance files as real repository source evidence.
This is not IDS business data and is not a raw metadata database payload.

## Duplicate And Conflict Summary

Phase 3 scenario evidence proves:

| Scenario | Stage result | Persistence effect |
|---|---|---|
| same file and same hash | one manifest candidate, one duplicate input | no duplicate document/chunk/job |
| same name and different hash | `FINGERPRINT_HASH_CONFLICT` | no overwrite, no merge, no delete |
| same hash and different path | `FINGERPRINT_DUPLICATE_CONTENT` | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0` | no persistence adapter exists |
| original hash stability | same `sha256` and `size` before/after validation | original file unchanged |

These findings are structural validation results, not production-data findings.
No real original-material corpus was scanned.

## Unsupported Or Blocked Inputs

The Stage 013 tests explicitly cover unsupported or blocked input states:

| Input type | State | Required behavior |
|---|---|---|
| missing explicit file | `FINGERPRINT_PATH_BLOCKED` | record failure; do not skip silently |
| local raw metadata root path | `FINGERPRINT_PATH_BLOCKED` | block before existence check, read, or hash |
| no source URI | `FINGERPRINT_NOT_CONFIGURED` | fail closed |
| unreadable explicit file | `FINGERPRINT_READ_BLOCKED` | record failure; do not mutate source |

No unsupported real source file was opened or inspected in this phase.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-013` had no Phase 4 closeout evidence.
   - Resolution: this file records delivery evidence, conflict/duplicate
     summary, unsupported states, rollback, and Chinese owner feedback.
2. Stage005 governance regression did not yet accept the completed
   `IDS-V0_1-STAGE013-P4` state.
   - Resolution: validator/test now accept STAGE-013 local completion while
     keeping the STAGE-011..020 upload gate locked.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE013-P4` and `STAGE-014` as the next stage.
4. Batch upload risk remained ambiguous after completing STAGE-013.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-014 through STAGE-020 remain pending.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `IDS_MetaData` content was read,
     listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned,
     or committed.

No finding required runtime code changes beyond already completed Phase 2/3
operations-only helper behavior and governance closeout.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `FINGERPRINT_NOT_CONFIGURED` | no approved source URI was provided | configure a user-approved explicit `file://` input |
| `FINGERPRINT_PATH_BLOCKED` | path is absent, unsafe, non-local, directory, or raw metadata root | correct path configuration; do not mutate source |
| `FINGERPRINT_READ_BLOCKED` | explicit file cannot be read | fix permissions outside Codex, then rerun preflight |
| `FINGERPRINT_HASH_CONFLICT` | same basename has different hashes | review as version/conflict; do not overwrite |
| `FINGERPRINT_DUPLICATE_CONTENT` | same hash appears at different paths | preserve provenance; do not delete originals |
| `FINGERPRINT_MIME_UNKNOWN` | MIME cannot be determined safely | continue only when downstream stage allows unknown MIME |
| `FINGERPRINT_MIME_CONFLICT` | extension and MIME disagree under future detector logic | record mismatch; do not rewrite file |
| `FINGERPRINT_MANIFEST_UNSAFE` | future manifest target would be unsafe | block manifest write before side effects |
| `FINGERPRINT_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

## Non-Recoverable Or Stop States

Stop immediately if a run would:

- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create unbounded manifests, evidence ledgers, audit logs, indexes,
  embeddings, OCR outputs, runtime databases, backup payloads, reports, or
  document/chunk/job rows without a later explicit stage gate;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated.

## Chinese Owner Feedback

STAGE-013 已在本地完成。当前系统已经具备一个只读、可测试的文件指纹预检能力：
对明确传入的本地文件，可以生成 `sha256`、大小、修改时间、扩展名、MIME 和首次
记录时间，并能识别重复、冲突和受阻路径。

业务上可以把它理解为：后续真实资料进入系统前，先用文件指纹确认“这是不是同一个
文件、是否同名但内容不同、是否同内容出现在不同路径”。系统不会因此自动覆盖、删除
或合并原始文件。

当前能力仍不是生产导入。它不会扫描原始目录，不会写 manifest/database，不会创建
document、chunk 或 job。真正把真实业务资料写入持久层，必须等待后续明确 Stage。

## Validation Results

Final validation in this run:

- Stage013 focused fingerprint test: bundled Python unittest ran 6 tests OK.
- Stage005 governance regression: bundled Python unittest ran 19 tests OK.
- Stage005 validator: `valid=true`, `issues=[]`, `missing_required_files=[]`,
  `event_json_errors=[]`, `forbidden_changed_paths=[]`,
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal discover: bundled Python unittest ran 70 tests OK.
- Python compile: `check_file_fingerprint.py` and
  `validate_stage005_governance_regression.py` passed.
- Events JSONL parse passed.
- `git diff --check` passed.
- Exact old underscored task-id marker scan returned no hits.
- Legacy path/name scan returned only existing stale-path, migration-policy, or
  compatibility-scan references.
- Semantic governance validate returned rc=1 with 29 known sparse/root/
  registered-project diagnostics and no KM_IDSystem project regression.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, manifests, evidence ledgers, document rows, chunk rows, job rows,
  indexes, OCR output, Embedding output, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-014.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE013-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, GitHub cleanup, or
app-entry reinstall because Phase 4 writes only tracked governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
