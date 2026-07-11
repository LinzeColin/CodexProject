# IDS v0.1 STAGE-037 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE037-P4`
- Acceptance ID: `ACC-STAGE-037`
- Stage: `STAGE-037 · 任务状态模型`
- Phase: `Phase 4 · 任务状态模型 交付证据、回滚与中文反馈`
- Entrance: `IDS 系统运营入口`
- Marker: `STAGE037_PHASE4_CLOSEOUT_NO_STAGE_REVIEW_THIS_RUN_NO_BATCH_UPLOAD_NO_GITHUB_UPLOAD`

## P0 Binding

- Source member:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-037_任务状态模型.md`
- Tracked P0 SHA-256:
  `ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2`
- Goal:
  `定义 import、archive、parse、ocr、chunk、embed、index、report 的统一 job 状态机。`
- Phase 4 delivery objective: state graph, retry/backpressure/cleanup evidence
  contracts, automatic/manual handling boundary, safe shutdown, recovery,
  rollback, known limits, and Chinese owner feedback.

The current machine source is
`job_state_model/stage037_job_state_model_index.json`. The checker entry is
`KM_IDSystem/scripts/check_job_state_model.py build_stage037_delivery_report`.
It returns one in-memory `ids.stage037.job_state_model.phase4.v1` report backed
by `ids.stage037.job_state_model.delivery_contract.v1` and nests the complete
Phase 3 and Phase 2 reports.

## state_graph

The delivery report binds the exact `ids.job_state.v1` graph:

- eight job types: `IMPORT`, `ARCHIVE`, `PARSE`, `OCR`, `CHUNK`, `EMBED`,
  `INDEX`, and `REPORT`;
- eleven states: `CREATED`, `QUEUED`, `CLAIMED`, `RUNNING`,
  `PAUSE_REQUESTED`, `PAUSED`, `RETRY_WAIT`, `SUCCEEDED`, `FAILED`,
  `DEAD_LETTERED`, and `CANCELLED`;
- twenty-one allowed directed transitions from the exact Phase 1/2 matrix;
- four immutable terminal states and three active execution states;
- pause reason, retry disposition, lock ownership, cleanup status, and Chinese
  status are separate dimensions, not extra lifecycle states.

This graph is static engineering evidence. It does not insert values into
`ids_state_value_registry`, create a job row, or execute a transition.

## retry_evidence_contract

- Runtime owner: `STAGE-039`.
- `max_retries` remains attempts after the initial attempt, with
  `total_attempt_limit = 1 + max_retries`.
- Retryable failure reserves eligibility in `RETRY_WAIT` without incrementing
  the counter; admission consumes exactly one reservation.
- Resource pause preserves an eligible reservation; exhaustion can only route
  to `DEAD_LETTERED`.
- Exact delay, jitter, taxonomy, and scheduler policy remain
  `POLICY_VALUE_DEFERRED_TO_STAGE039_040_041`.
- No retry scheduler or dead-letter runtime was created or executed.

## backpressure_evidence_contract

- Runtime owner: `STAGE-040`.
- Drive, storage, API budget, dependency, and queue pressure are bounded pause
  reasons/evidence, not new states.
- A blocked resource gate cannot silently requeue work or consume a retry.
- Numeric thresholds and queue limits remain deferred; this phase does not
  invent values.
- No measured backpressure, queue admission, pause runtime, or resume runtime
  was executed.

## cleanup_evidence_contract

- Runtime owner: `STAGE-044`.
- A state transition never authorizes deletion.
- Cleanup still requires exact attempt ownership, approved-root identity,
  root-relative path, immutable lstat identity, symlink blocking, exclusive
  namespace lock, writer quiescence, `openat` no-follow traversal, and
  `unlinkat` under the same lock.
- `00_ORIGINAL_RAW_DATA`, source data/database, manifest, evidence ledger,
  audit log, report snapshot, active index, and required checkpoint remain
  forbidden cleanup targets.
- No cleanup candidate, manifest, file operation, or runtime was created.

## automatic_manual_boundary

- Runtime owner: `STAGE-042`.
- Automatic run, resume, and shutdown are disabled in STAGE-037.
- Reconnect or resource recovery cannot auto-resume a paused job. Owner
  revalidation and fresh resource gates are required before requeue.
- Cancellation from active execution must first reach a safe checkpoint or
  quarantine boundary, revoke lease/lock ownership, and advance fencing.
- Manual rerun of a terminal job creates a new linked job in a later runtime;
  it never rewrites terminal history.

## safe_shutdown_steps

1. `stop_new_admission`: a future lifecycle controller stops new admission and
   records a bounded shutdown reason. This phase does not operate a queue.
2. `request_safe_checkpoint`: active work follows `PAUSE_REQUESTED` to a safe
   checkpoint or quarantine boundary; uncontrolled continuation is forbidden.
3. `deactivate_and_fence`: one compare-and-set transaction must record state
   and audit, revoke lease/lock, and advance fencing before shutdown completes.
4. `preserve_source_and_evidence`: shutdown never deletes source, durable
   evidence, validated output, or a checkpoint needed for recovery.

## recovery_steps

1. `record_worker_loss_evidence`: a future STAGE-043 coordinator records safe
   lease-expiry or worker-loss evidence; this phase fabricates no crash log.
2. `cas_deactivate_expired_attempt`: the coordinator performs fenced
   compare-and-set deactivation before retry admission.
3. `reserve_retry_without_consuming`: remaining budget creates one idempotent
   pending reservation and does not increment `retry_count` until admission.
4. `require_owner_resource_revalidation`: drive reconnect, restored disk, or
   dependency recovery still requires owner and resource revalidation.
5. `block_stale_worker_commit`: every stale state or output commit fails after
   state-version/fencing advancement.

No crash recovery, lease expiry, retry admission, queue action, or real job was
executed by this phase.

## rollback_steps

1. `stop_on_invalid_contract`: if any P2/P3/P4 machine or evidence check fails,
   keep the stage blocked and do not run orchestration behavior.
2. `revert_phase4_contract_only`: revert only the P4 index field, delivery
   builder, closeout doc/tests, governance event/state, compatibility changes,
   and rendered owner views.
3. `preserve_phase1_phase3_evidence`: retain the P1 boundary, P2 deterministic
   engine, P3 scenarios, prior stage evidence, and taskpack identity.
4. `preserve_data_and_runtime`: do not mutate raw metadata, source/runtime
   databases, registry values, job rows, queue state, locks, reports, indexes,
   app entries, GitHub state, or user-edited files during rollback.

## known_limits

- `no_queue_or_worker_runtime`: no queue, worker, claim transport, scheduler,
  dead-letter processor, lock manager, or lifecycle controller exists here.
- `numeric_policies_deferred`: retry delays, jitter, queue limits, storage
  thresholds, lease durations, and lock timeouts remain downstream-owned.
- `no_live_crash_or_recovery`: worker-crash and stale-fencing results are
  deterministic in-memory contract scenarios, not live recovery evidence.
- `no_cleanup_runtime`: cleanup guards are a downstream interface only; no
  deletion was attempted.
- `no_database_or_registry_execution`: PostgreSQL was not connected; no schema,
  job row, transition audit, or state-registry value was written.
- `static_closeout_is_not_readiness`: `PASS_STATIC_CLOSEOUT_RUNTIME_DISABLED`
  proves static contract consistency only, not production readiness.
- `stage_review_and_batch_upload_blocked`: whole-stage review is a later run;
  GitHub upload and app reinstall remain blocked by `BATCH031_040`.

## Truthful Result

Expected machine result:

- `delivery_contract_valid=true`
- `result=PASS_STATIC_CLOSEOUT_RUNTIME_DISABLED`
- `execution_ready=false`
- `execution_state=STATIC_JOB_STATE_CLOSEOUT_VALID_RUNTIME_DISABLED`
- `stage_review_status=pending_next_run`
- `next_gate=IDS-STAGE037-REVIEW-GATE`
- every queue, worker, retry/dead-letter, backpressure, lock, automatic
  lifecycle, crash recovery, cleanup, database, schema, registry, runtime
  output, real-job, fake-data, and raw-metadata action remains `false`
- `github_upload_allowed=false`
- `app_reinstall_allowed=false`

## Stage And Batch Boundary

STAGE-037 has local Phase 1 through Phase 4 evidence. This is not the required
whole-stage review.

- `NO_STAGE_REVIEW_THIS_RUN`
- `NO_STAGE038`
- `NO_BATCH_REVIEW`
- `NO_BATCH_UPLOAD`
- `NO_GITHUB_UPLOAD`
- `NO_PR_OR_MERGE`
- `NO_ISSUE_MUTATION`
- `NO_APP_REINSTALL`

The next run may only enter `IDS-V0_1-STAGE037-REVIEW` from
`IDS-STAGE037-REVIEW-GATE`.

## Raw Data And Real-Data-Only Boundary

The real metadata root is recorded as path-only:

`/Users/linzezhang/Downloads/IDS_MetaData`

This phase does not read, list, hash, open, copy, move, delete, modify, dump,
scan, normalize, restore, or commit any content under that path. It does not
move, delete, or overwrite source/durable evidence. 不得使用虚构 IDS 业务数据、
虚构数据库行、placeholder corpus、fabricated jobs/logs/evidence 或伪造执行证据。

## chinese_owner_feedback

STAGE-037 Phase 4 已交付统一任务状态图、重试/反压/清理证据合同、自动与人工
处理边界，以及安全关闭、恢复、回滚和已知限制。当前结果只证明 tracked 静态
合同与十项异常场景一致；没有运行队列、worker、重试、反压、锁、自动生命周期、
崩溃恢复、清理或数据库，也没有访问原始资料。

下一步只能在独立 run 中进行 STAGE-037 whole-stage review，并修复复审发现的
问题。本轮不进入 STAGE-038，不上传 GitHub，不重装 app。
