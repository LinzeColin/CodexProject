# IDS v0.1 STAGE-014 Phase 4 Closeout

## Identity

- Stage: `STAGE-014`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE014-P4`
- Acceptance ID: `ACC-STAGE-014`
- Stage title: `Manifest 生成`
- Recorded at UTC: `2026-07-02T14:05:44Z`

## Goal

Close out STAGE-014 with manifest delivery evidence, duplicate/conflict and
unsupported-input summaries, original-file protection proof, rollback steps,
whole-stage review, and Chinese owner feedback.

Marker: `STAGE014_PHASE4_CLOSEOUT_NO_GITHUB_UPLOAD_NO_STAGE015`.

## Delivered Contract

STAGE-014 now has a bounded metadata-only manifest generation path:

- Phase 1 defined the manifest fields, source protection boundary,
  idempotency, duplicate/conflict states, and failure-state contract.
- Phase 2 implemented `check_manifest_generation.py`, which maps explicit
  local `file://` fingerprint evidence into in-memory manifest candidates.
- Phase 3 validated same-file/same-hash, same-name/different-hash,
  same-hash/different-path, repeated import without persistence, and original
  hash stability.
- Phase 4 records closeout, whole-stage review, rollback, and owner-facing
  guidance.

The implementation remains intentionally narrow:

- no directory discovery;
- no recursive scan;
- no persisted manifest file write;
- no database write;
- no document, chunk, or job creation;
- no evidence ledger or audit log write;
- no report generation;
- no raw metadata database read;
- no external API call, service start, dependency install, or runtime output.

## Manifest Candidate Example

The manifest example is a field contract proven by focused tests against
tracked governance documents. It is not a committed runtime manifest and not a
business corpus sample.

| Field | Meaning | Source |
|---|---|---|
| `source_uri` | explicit local `file://` URI supplied by caller | STAGE-013 fingerprint record |
| `source_path` | normalized local path for the explicit file | STAGE-013 fingerprint record |
| `sha256` | exact byte fingerprint inherited from STAGE-013 | STAGE-013 fingerprint record |
| `file_size` | byte length mapped from the fingerprint `size` field | STAGE-013 fingerprint record |
| `mtime` | filesystem modification time at fingerprint time | STAGE-013 fingerprint record |
| `first_seen_at` | first observation timestamp | STAGE-013 fingerprint record |
| `manifest_generated_at` | manifest-candidate generation timestamp | STAGE-014 manifest slice |
| `manifest_id` | deterministic `ids-manifest-sha256-{sha256}` value | STAGE-014 manifest slice |
| `manifest_state` | readiness or explicit failure classification | STAGE-014 state mapping |

The example proves that a manifest candidate can be rebuilt and compared from
metadata. It does not authorize production persistence.

## Duplicate And Conflict Summary

Phase 3 scenario evidence proves:

| Scenario | Manifest result | Persistence effect |
|---|---|---|
| same file and same hash | one `MANIFEST_READY` candidate and one duplicate input | no duplicate document/chunk/job |
| same name and different hash | `MANIFEST_HASH_CONFLICT` | no overwrite, merge, or delete |
| same hash and different path | `MANIFEST_DUPLICATE_CONTENT` | provenance preserved |
| repeated import | `document_delta=0`, `chunk_delta=0`, `job_delta=0`, `manifest_write_delta=0` | no persistence adapter exists |
| original hash stability | same `sha256` and size before/after validation | original source unchanged |

These are structural validation results, not production-data findings. No real
business corpus or raw metadata database was scanned.

## Unsupported Or Blocked Inputs

The Stage 014 tests and inherited Stage 013 behavior explicitly cover blocked
or unsupported input states:

| Input type | State | Required behavior |
|---|---|---|
| no source URI | `MANIFEST_NOT_CONFIGURED` | fail closed |
| missing explicit file | `MANIFEST_SOURCE_BLOCKED` | record failure; do not skip silently |
| raw metadata root path | `MANIFEST_SOURCE_BLOCKED` | block before manifest work |
| unreadable explicit file | `MANIFEST_SOURCE_BLOCKED` | record failure; do not mutate source |
| same basename with different hash | `MANIFEST_HASH_CONFLICT` | preserve both facts |
| same hash at different paths | `MANIFEST_DUPLICATE_CONTENT` | preserve provenance |
| unsafe manifest target shape | `MANIFEST_SCHEMA_UNSAFE` | block manifest write |
| incomplete classification | `MANIFEST_UNKNOWN` | fail closed |

No unsupported real source file was opened or inspected in this phase.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

Findings checked and resolved in this phase:

1. `STAGE-014` had no Phase 4 closeout evidence.
   - Resolution: this file records delivery evidence, scenario summaries,
     unsupported states, rollback, and Chinese owner feedback.
2. Stage005 governance regression did not yet accept the completed Phase 4
   closeout task-id state.
   - Resolution: the test was written first and failed; validator state
     acceptance was then extended for the hyphenated `IDS-V0_1-STAGE014-P4`
     closeout state.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files now
     point to `IDS-V0_1-STAGE014-P4` while keeping STAGE-015 pending.
4. Batch upload risk remained active after STAGE-014 local completion.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false`;
     STAGE-015 through STAGE-020 remain pending.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `IDS_MetaData` content was read,
     listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned,
     or committed.

No finding required runtime code changes beyond already completed Phase 2/3
metadata-only helper behavior and governance closeout.

## Recoverable States

| State | Owner meaning | Recovery |
|---|---|---|
| `MANIFEST_NOT_CONFIGURED` | no approved explicit source URI exists | configure a user-approved explicit `file://` input |
| `MANIFEST_SOURCE_BLOCKED` | source path is absent, unsafe, unreadable, non-local, or raw metadata root | correct path/permission outside Codex; do not mutate source |
| `MANIFEST_FINGERPRINT_MISSING` | required fingerprint evidence is absent | rerun bounded STAGE-013 fingerprint preflight |
| `MANIFEST_HASH_CONFLICT` | same logical name has different content hashes | review as version/conflict; do not overwrite |
| `MANIFEST_DUPLICATE_CONTENT` | same hash appears at multiple paths | preserve provenance; do not delete originals |
| `MANIFEST_SCHEMA_UNSAFE` | future manifest shape would store raw payload or secrets | block manifest write and revise schema |
| `MANIFEST_WRITE_BLOCKED` | future write target is not safe or rollbackable | do not write manifest/database |
| `MANIFEST_UNKNOWN` | classification is incomplete | fail closed and gather stronger evidence |

## Non-Recoverable Or Stop States

Stop immediately if a run would:

- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- create unbounded manifests, evidence ledgers, audit logs, indexes,
  embeddings, OCR outputs, runtime databases, backup payloads, reports, or
  document/chunk/job rows without a later explicit stage gate;
- use fake IDS business data, fake database rows, fake source documents,
  placeholder corpora, or fabricated evidence;
- push to GitHub before STAGE-011..020 are complete, reviewed, repaired, and
  batch-gated.

## Chinese Owner Feedback

STAGE-014 已在本地完成。当前系统已经具备一个只读、可测试的 manifest 候选生成
能力：对明确传入的本地文件身份，可以从文件指纹生成可重建、可审计、可对比的
metadata-only manifest candidate。

业务上可以把它理解为：系统现在能判断“这个文件是否已经出现过、同名内容是否冲突、
同内容是否存在于多个路径”，并把这些情况记录为明确状态。系统不会因此自动覆盖、
删除、合并、移动或重写原始文件。

当前能力仍不是生产导入。它不会扫描原始目录，不会写 manifest/database，不会创建
document、chunk 或 job。真正把真实业务资料写入持久层，必须等待后续明确 Stage。

## Validation Results

Final validation in this run:

- Stage005 governance RED:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  first failed with `Ran 23 tests ... FAILED (failures=1)` because
  `IDS-V0_1-STAGE014-P4` closeout state was not accepted.
- Stage005 governance intermediate RED:
  the same command then failed with `Ran 23 tests ... FAILED (failures=1)`
  because `STAGE014_PHASE4_CLOSEOUT.md` had not yet been created as required
  evidence.
- Stage005 governance GREEN:
  the same command returned exit code `0` with `Ran 23 tests` and `OK`.
- Stage014 focused manifest test:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage014_manifest_generation.py -q`
  returned exit code `0` with `Ran 6 tests` and `OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`, `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, and `unexpected_changed_paths=[]`.
- Full v0.1 pursuing-goal unittest discovery:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned exit code `0` with `Ran 80 tests` and `OK`.
- Python compile:
  `python3 -B -m py_compile KM_IDSystem/scripts/check_manifest_generation.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned exit code `0`.
- Events JSONL parse returned `events_jsonl_ok`.
- Owner render:
  `python3 -B scripts/lean_governance.py render --project KM_IDSystem --write`
  updated `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- Final check-render:
  `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned exit code `0`, `drift_count=0`, and `reference_issue_count=0`.
- Final diff whitespace check:
  `git diff --check` returned exit code `0`.
- Semantic governance diagnostic:
  `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned exit code `1` with 29 known sparse-worktree/root or
  registered-project missing-path diagnostics and no new `KM_IDSystem`
  semantic error.
- Final old underscored task-id variant scan returned no hits.
- Legacy name scan for `OpMe_System` and `opme-system` found only historical
  migration, stale-path, compatibility-scan, or do-not-revive references. This
  Phase 4 run did not recreate either as an active development path.

## Forbidden Actions Preserved

This phase did not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import,
  backup, manifest, report, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime
  databases, persisted manifests, evidence ledgers, document rows, chunk rows,
  job rows, indexes, OCR output, Embedding output, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit
  `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate
  original files in place;
- use fake IDS business data, fake database rows, fake source documents, or
  fabricated evidence;
- push to GitHub, open a PR, merge, reinstall app entries, or enter STAGE-015.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE014-P4` commit.

Rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, manifest cleanup, runtime database cleanup, report
cleanup, external-drive cleanup, raw metadata repair, GitHub cleanup, or
app-entry reinstall because Phase 4 writes only tracked governance evidence.

Do not alter `00_ORIGINAL_RAW_DATA` or
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
