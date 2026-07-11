# STAGE-037 Phase 3 - Job-State Adversarial Scenarios

## Identity
- Stage: `STAGE-037 · 任务状态模型`
- Task: `IDS-V0_1-STAGE037-P3`
- Acceptance: `ACC-STAGE-037`
- Report schema: `ids.stage037.job_state_model.phase3.v1`
- Execution mode: `STATIC_JOB_STATE_ADVERSARIAL_SCENARIO_VALIDATION_ONLY`
- Valid state: `STATIC_JOB_STATE_SCENARIOS_VALID_RUNTIME_DISABLED`
- P0 taskpack SHA-256:
  `ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2`
- Next gate: `IDS-STAGE037-P4-GATE`

## Phase 3 Boundary
Phase 3 calls the Phase 2 pure `evaluate_transition` function with bounded,
tracked-contract metadata. It validates result codes, candidate state, retry
accounting, lease/lock deactivation, fencing, idempotent replay, resource-pause
guards, unknown request shapes, and zero-runtime truth fields. It creates no
queue, worker, scheduler, lock record, cleanup manifest, database row, job log,
checkpoint, runtime report artifact, report file, index, or runtime output.

Scenario identities use only the real tracked task, acceptance, contract, and
source-document identifiers already present in this repository. They are not
business records and do not claim that a real job, disk failure, drive event,
worker crash, lock contention, or deletion occurred. 不得使用虚构 IDS 业务数据、
虚构数据库行、placeholder corpus、fabricated jobs/logs/evidence 或伪造执行证据。

## Scenario Matrix

| Scenario id | Expected result | Contract invariant |
|---|---|---|
| `duplicate_click_idempotent_replay` | `TRANSITION_ACCEPTED` replay | same request returns the original candidate and emits no second action |
| `duplicate_click_payload_conflict` | `TRANSITION_REQUEST_CONFLICT` | one request id cannot authorize a different target state |
| `worker_crash_retry_reservation` | `RETRY_WAIT` candidate | retry is reserved without increment; lease/lock are revoked and fencing advances |
| `stale_worker_fencing_block` | `COMPARE_AND_SET_MISMATCH` | the pre-crash worker cannot mark the post-crash snapshot successful |
| `removable_drive_offline_pause` | `PAUSED` candidate | `SAFE_MODE_DRIVE_OFFLINE` pauses before any claim is activated |
| `drive_reconnect_no_auto_resume` | `MISSING_TRANSITION_GUARD` | reconnect without `owner_revalidated` cannot requeue |
| `low_disk_retry_pause_preserves_budget` | `PAUSED` candidate | `BUDGET_BLOCKED_LOW_FREE` preserves the pending retry and counter |
| `same_source_concurrency_blocked` | `MISSING_TRANSITION_GUARD` | one complete holder claim is accepted; a distinct job with the exact same source identity and lock key is blocked without acquisition proof |
| `lock_claim_without_proof_blocked` | `MISSING_TRANSITION_GUARD` | a complete claim passes with proof=true, then fails when only that proof changes to false |
| `cleanup_authorization_blocked` | `INVALID_REQUEST_SHAPE` | baseline cancellation passes, then fails when only `cleanup_manifest_ref` is added; STAGE-044 remains owner |

Same-source identity, holder state, and lock contention are contract inputs
only. The two in-memory job identities share the exact tracked source ref and
lock key, but the second claim is blocked by explicit external acquisition
proof=false. STAGE-041 owns real lock/lease/fencing runtime, while STAGE-043
owns real worker-crash recovery. Phase 3 proves that an unverified guard cannot
pass; it does not pretend to detect a live conflict.

## Truthful Scenario Result
The deterministic report produced by
`build_stage037_scenario_validation_report` must state:

- `scenario_validation_valid=true` only when the exact ten scenarios pass;
- `execution_ready=false`;
- `live_execution_performed=false`;
- queue, worker, retry scheduler, backpressure, lock, automatic lifecycle,
  crash recovery, cleanup, database, schema, registry, and runtime-output
  actions are all false;
- `real_job_created=false`;
- `fake_ids_business_data_used=false`;
- `raw_metadata_content_accessed=false`;
- `github_upload_allowed=false` and `app_reinstall_allowed=false`;
- the complete Phase 2 report remains nested as historical contract evidence;
- a malformed or runtime-enabled Phase 2 contract makes every scenario return
  `accepted=false`, `INVALID_CONTRACT`, and no candidate;
- the only next gate is `IDS-STAGE037-P4-GATE`.

A scenario `PASS` proves only that the in-memory contract evaluation produced
the expected safe result and zero-side-effect fields. It is not evidence that a
worker, drive, disk budget, lock manager, cleanup process, database, or real job
was exercised.

## Raw Data And Cleanup Protection
`/Users/linzezhang/Downloads/IDS_MetaData` remains path-only. This phase does
not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize,
restore, or commit anything under that path. It does not move, delete, or
overwrite `00_ORIGINAL_RAW_DATA`, source data, manifest, evidence ledger,
audit log, report snapshot, active index, or checkpoint.

`cleanup_authorization_blocked` deliberately proves that adding a cleanup field
to a transition request is rejected. No test deletes a temporary file. Cleanup
remains a separately audited STAGE-044 action with its own allowlist, trusted
root, lstat identity, exclusive namespace lock, writer-quiescence, and
no-follow deletion requirements.

## Validation
Run from the repository root:

```bash
python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage037_job_state_model.Stage037JobStateModelPhase3Tests -q
python3 -B KM_IDSystem/scripts/check_job_state_model.py
```

The checker prints one deterministic JSON report to stdout and writes no file.

## Independent Review And Remediation
The first independent read-only Phase 3 review found zero Critical and six
Important evidence-quality issues. This phase repaired all six before commit:

1. non-object loader results are normalized and fail closed;
2. same-source concurrency now includes an accepted holder and a distinct
   contender sharing the exact source identity and lock key;
3. lock-proof blocking now has a complete accepted positive control and changes
   only the acquisition proof for the negative case;
4. invalid contracts require every scenario to return `accepted=false`,
   `INVALID_CONTRACT`, `candidate_created=false`, and no observed state;
5. dependent crash/reconnect scenarios never evaluate an empty snapshot and
   require exact prerequisite candidates;
6. cleanup blocking now proves the baseline cancellation first, then adds only
   the unauthorized cleanup field.

The final read-only re-review found zero Critical, zero Important, and zero
Minor findings and marked the phase ready for local commit. This is phase-level
review evidence only; it is not the later whole-stage review.

## Stop Conditions
- `NO_PHASE4`: do not enter Phase 4 or whole-stage review in this run.
- Do not create or run queue, worker, retry, dead-letter, backpressure, lock,
  automatic lifecycle, crash-recovery, or cleanup behavior.
- Do not connect PostgreSQL, modify schema, seed the state registry, or create
  real/fake job rows.
- Do not access raw metadata content or substitute fake IDS business data.
- Do not upload GitHub, create/merge a PR, mutate issues, reinstall app
  entries, run batch review, or run an upload gate.

## Rollback
Revert only this Phase 3 document, the scenario builder and tests, exact
Stage005/compatibility support, batch lock, roadmap/event update, and rendered
owner views. Preserve the Phase 1/2 contracts, prior stages, user-edited files,
raw metadata, PostgreSQL, SQL, runtime data, app entries, and GitHub state.

## 中文 Owner 反馈
Stage 37 Phase 3 已验证重复点击、worker 崩溃候选、移动硬盘离线、低磁盘、
同源并发、锁阻断与清理保护的静态失败关闭行为。所有结果均为内存合同证据，
没有运行真实任务或访问真实资料。下一步只能从 `IDS-STAGE037-P4-GATE`
进入独立 Phase 4。
