# IDS v0.1 STAGE-012 Phase 4 Closeout

## Identity

- Stage: `STAGE-012`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE012-P4`
- Acceptance ID: `ACC-STAGE-012`
- Stage title: `原始资料只读合同`
- Recorded at UTC: `2026-07-02T12:43:43Z`

## Goal

Close out STAGE-012 with delivery evidence, whole-stage review, rollback steps,
and Chinese owner feedback for the original-material read-only contract.

Marker: `STAGE012_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE013`.

## Delivered Contract

STAGE-012 is a read-only original-material identity contract. It now has:

- Phase 1 boundary evidence for `00_ORIGINAL_RAW_DATA`, identity fields,
  manifest metadata rules, idempotency, duplicate handling, and forbidden raw
  mutation.
- Phase 2 metadata-only identity slice for explicit `file://` inputs.
- Phase 3 deterministic scenario validation for duplicate/conflict/hash
  stability cases.
- Phase 4 closeout, whole-stage review, rollback, and owner feedback.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no manifest-file write;
- no database write;
- no document, chunk, or job creation;
- no evidence ledger or audit log write;
- no raw metadata database read;
- no API call or service start.

## Metadata-Only Manifest Candidate Example

The manifest candidate remains an in-memory report candidate, not a persisted
manifest file.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit `file://` URI supplied by caller | Phase 2 identity slice |
| `source_path` | normalized local path for the explicit file | Phase 2 identity slice |
| `sha256` | exact byte fingerprint for the explicit file | Phase 2 identity slice |
| `file_size` | byte length observed at identity time | Phase 2 identity slice |
| `mtime` | filesystem modification time at identity time | Phase 2 identity slice |
| `first_seen_at` | deterministic UTC first-seen timestamp | Phase 2 identity slice |
| `state` | `ORIGINAL_RAW_READY` or explicit failure state | Phase 2 status contract |

Focused tests use the tracked governance file
`KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE012_ENTRY_CONTRACT.md` as real
repository source evidence. This is not IDS business data and is not a raw
metadata database payload.

## Duplicate Detection Report Summary

Phase 3 scenario evidence proves:

| Scenario | Stage result | Persistence effect |
|---|---|---|
| same file and same hash | one manifest candidate, one duplicate input | no duplicate document/chunk/job |
| same name and different hash | `ORIGINAL_RAW_HASH_CONFLICT` | no overwrite, no merge, no delete |
| same hash and different path | `ORIGINAL_RAW_DUPLICATE_CONTENT` | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0` | no persistence adapter exists |
| original hash stability | same sha256 and file size before/after validation | original file unchanged |

The duplicate report is evidence for future persistence design. It is not a
database migration, not a manifest write, and not a production import result.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-012` had no Phase 4 closeout evidence.
   - Resolution: this file records closeout, delivery evidence, rollback, and
     Chinese owner feedback.
2. Stage005 governance regression did not yet accept the completed
   `IDS-V0_1-STAGE012-P4` state.
   - Resolution: validator/test now accept STAGE-012 local completion while
     keeping the STAGE-011..020 upload gate locked.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE012-P4`.
4. Batch upload risk remained ambiguous after completing STAGE-012.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-013 through STAGE-020 remain pending.
5. Prior marker-scan evidence included the exact underscored task-id marker in
   its own prose, causing future scans to match the evidence text itself.
   - Resolution: Phase 3 evidence and the rendered roadmap now describe the
     scan without embedding that exact marker.

No finding required code changes beyond governance closeout and validator
forward compatibility.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `ORIGINAL_RAW_NOT_CONFIGURED` | no approved source URI was provided | configure a user-approved explicit `file://` input |
| `ORIGINAL_RAW_PATH_BLOCKED` | path is absent, unsafe, non-local, a directory, or raw metadata root | correct path configuration; do not mutate source |
| `ORIGINAL_RAW_READ_BLOCKED` | explicit file is not readable | fix permissions outside Codex, then rerun preflight |
| `ORIGINAL_RAW_HASH_CONFLICT` | same basename has different hashes | review as version/conflict; do not overwrite |
| `ORIGINAL_RAW_DUPLICATE_CONTENT` | same hash appears at different paths | preserve provenance; do not delete originals |
| `ORIGINAL_RAW_MANIFEST_UNSAFE` | future manifest target would be unsafe | block manifest write before side effects |
| `ORIGINAL_RAW_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

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

STAGE-012 已在本地完成。当前系统只建立了“显式文件身份识别和重复/冲突判断”的
只读合同，不会自动扫描原始目录，不会写 manifest/database，也不会创建
document、chunk 或 job。

业务上可以把它理解为：以后导入真实资料前，系统必须先确认文件身份、重复关系和
冲突状态；遇到同名不同 hash 或同 hash 不同路径时，只记录判断，不自动覆盖、
删除或合并原始文件。

当前不能把 Phase 2/3 的内存报告误当成生产导入结果。真正读取真实业务资料、写入
manifest 或创建数据库记录，必须等待后续明确 stage。

## Validation Results

Final validation for this run is recorded after the final command pass:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  failed as expected before validator support with one failure in
  `test_phase_state_allows_stage012_phase4_closeout_completion`.
- Stage005 governance GREEN:
  after adding the P4 state and the `STAGE-013` next-stage whitelist, the same
  command returned `Ran 15 tests ... OK`.
- Stage012 focused tests:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage012_original_raw_identity.py -q`
  returned `Ran 5 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, and
  `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 60 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_original_raw_identity.py` and
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
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-013.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE012-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, GitHub cleanup, or
app-entry reinstall because Phase 4 writes only tracked governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
