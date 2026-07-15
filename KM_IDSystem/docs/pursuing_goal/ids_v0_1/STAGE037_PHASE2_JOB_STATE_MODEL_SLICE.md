# STAGE-037 Phase 2 - Deterministic Job State Model Slice

## Identity
- Stage: `STAGE-037 · 任务状态模型`
- Task: `IDS-V0_1-STAGE037-P2`
- Acceptance: `ACC-STAGE-037`
- Contract id: `ids_stage037_job_state_model_static_slice`
- Index schema: `ids.stage037.job_state_model.index.v1`
- Report schema: `ids.stage037.job_state_model.phase2.v1`
- Decision schema: `ids.stage037.job_state_model.transition_decision.v1`
- Contract state: `STATIC_JOB_STATE_CONTRACT_VALID_RUNTIME_DISABLED`
- Next gate: `IDS-STAGE037-P3-GATE`

## Implemented Slice
Phase 2 implements one metadata-only deterministic state-transition engine
slice with three tracked engineering artifacts:

1. `job_state_model/stage037_job_state_model_index.json` is the
   machine-readable contract for eight job types, eleven states, exact allowed
   transitions, guards, retry accounting, references, Chinese projections,
   runtime blocks, downstream ownership, source hashes, and one explicit
   `ids.job_control_envelope.v1` field-compatibility contract. The envelope
   separates the Phase 2 evaluator subset from fields whose persistence stays
   owned by STAGE-038..041.
2. `scripts/check_job_state_model.py` validates that tracked contract and
   exposes a pure `evaluate_transition` function.
3. This document records the truthful result, input/output/error/checkpoint
   boundary, rollback, and owner feedback.

The evaluator uses `STATIC_CONTRACT_EVALUATION_ONLY`. It accepts bounded
metadata and returns an in-memory candidate decision. It never persists the
candidate, and `runtime_transition_performed=false` in every accepted or
rejected result. This is no queue/worker runtime and is not a job execution
claim.

## Deterministic Transition Boundary
The engine evaluates the Phase 1 transition matrix without changing an
external record:

- every request carries `job_id`; compare-and-set requires that exact
  `job_id`, `expected_state`, and `expected_state_version` to match the
  supplied snapshot;
- a successful candidate increments `state_version` by exactly one;
- `transition_request_id` replay fingerprints the request including
  `job_id`, validates the complete prior decision and candidate shape, and
  returns the original candidate only for the same job; cross-job replay,
  modified prior results, and the same id with different content fail closed;
- terminal states are immutable, and `RUNNING -> CANCELLED` remains illegal;
- every allowed `* -> CANCELLED` request carries a bounded `stop_reason`; a
  generic boolean cancel fact or audit ref alone cannot authorize cancellation;
- entering `CLAIMED` requires a complete candidate lease/lock/fencing
  envelope with a strictly advanced fencing token;
- active execution transitions require the matching fencing token;
- `RUNNING -> SUCCEEDED` and `RUNNING -> FAILED` require a live lease;
  lease-expiry evidence can route recovery into retry handling but cannot
  authorize success or permanent-failure completion;
- every transition leaving `CLAIMED`, `RUNNING`, or
  `PAUSE_REQUESTED` for a non-active state clears lease/lock ownership and
  advances fencing in the returned candidate;
- no candidate is written to PostgreSQL, a queue, a registry, an audit ledger,
  a file, or another runtime surface.

The returned `transition_candidate` is explicitly `candidate_only=true`
and `persisted=false`. It is not a fabricated job log or execution evidence.
Phase 3 may validate adversarial static scenarios later; Stage 038 and later
stages own real orchestration behavior.

## Retry, Pause, And Exhaustion
`max_retries` remains the immutable number of attempts after the initial
attempt. A retryable active failure enters `RETRY_WAIT` without incrementing
`retry_count`:

- when budget remains, the candidate sets `retry_pending=true` and
  `retry_disposition=eligible` and carries the caller-supplied bounded
  `next_eligible_at` control ref;
- `RETRY_WAIT -> QUEUED` requires both `next_eligible_reached=true` and a
  bounded `next_eligible_evidence_ref`; a bare boolean cannot prove timing;
- `RETRY_WAIT -> PAUSED` preserves that reservation when a resource gate is
  blocked;
- `PAUSED -> QUEUED` with `retry_pending=true` still requires the preserved
  bounded `next_eligible_at`, a bounded `next_eligible_evidence_ref`, and
  `next_eligible_reached=true`; only then does it atomically increment
  `retry_count` and clear `retry_pending`;
- an ordinary pause has no pending reservation and does not consume retry
  budget;
- when `retry_count == max_retries`, entry to `RETRY_WAIT` sets
  `retry_pending=false` and `retry_disposition=exhausted`;
- an exhausted retry cannot pause, requeue, or cancel through the evaluator;
  its only next state is `DEAD_LETTERED`.

No retry time, jitter, taxonomy, or scheduler is invented. `next_eligible_at`
is an opaque bounded control ref supplied by the future STAGE-039 runtime, not
a timestamp calculated by Phase 2. Numeric policy values remain
`POLICY_VALUE_DEFERRED_TO_STAGE039_040_041`; STAGE-039 owns retry and
dead-letter runtime, STAGE-040 owns backpressure runtime, and STAGE-042 owns
automatic lifecycle runtime.

## Reference Validation
The engine validates only bounded control metadata. Scalar refs and ref lists
are limited by the machine contract, and it rejects:

- absolute paths, case variants of `file:` refs, Windows/backslash paths,
  Unicode separator variants, percent-encoded path tokens, parent traversal,
  null/newline content, and case variants of the path-only root
  `/Users/linzezhang/Downloads/IDS_MetaData`;
- plaintext secret, password, credential, DSN, API key, raw source/document/
  OCR body, vector payload, report binary, or raw log fields;
- missing output refs for success, missing error refs for failure/retry,
  missing checkpoint or quarantine refs for safe deactivation, and missing
  resource evidence for a resource pause;
- missing retry-eligibility time/evidence and missing or unbounded cancellation
  `stop_reason`;
- unbounded or structurally unknown request fields.

The checker requires exact top-level and safety-subcontract key sets. Removing
or adding transition guards, reference requirements, forbidden secret/body
tokens, deactivation/retry/truth fields, source refs, runtime switches, or
unknown top-level policy fields invalidates the whole contract instead of being
silently ignored.

Inputs may reference tracked contracts, immutable control identities, bounded
output refs, checkpoint refs, error refs, and resource-gate refs. They never
contain source bodies or real metadata content.

## Source And Cleanup Protection
The checker binds hashes for the tracked Phase 1 scope, STAGE-008/009/011/
016/022 dependencies, STAGE-030 `ids_jobs` schema, STAGE-036 registry
structure, and raw-data boundary. It reads those Git-tracked engineering
contracts only.

A state transition never authorizes deletion. STAGE-044 still owns cleanup and
must require the approved root identity, root-relative path, immutable lstat
identity, symlink blocking, exclusive namespace lock, writer quiescence,
`openat` with no-follow behavior, and `unlinkat`. Phase 2 does not delete
or mutate `00_ORIGINAL_RAW_DATA`, source data, manifest, evidence ledger,
audit log, report snapshot, active index, checkpoint, or temporary artifact.

## Truthful Result
The expected checker result is:

- `contract_valid=true`
- `execution_ready=false`
- `execution_state=STATIC_JOB_STATE_CONTRACT_VALID_RUNTIME_DISABLED`
- `runtime_transition_performed=false`
- `real_job_created=false`
- every queue/worker/retry-scheduler/dead-letter/backpressure/lock/automatic-
  lifecycle/cleanup/database/schema/runtime-output action is false
- `github_upload_allowed=false`
- `app_reinstall_allowed=false`
- `next_gate=IDS-STAGE037-P3-GATE`

`contract_valid=true` means the tracked JSON, source hashes, checker, exact
state vocabulary, transition rules, guard facts, reference policy, retry
accounting, complete future envelope field partition, Chinese projection,
runtime blocks, and downstream ownership agree.
It does not mean a queue exists, a worker ran, PostgreSQL was connected, a
state-registry row was inserted, a real job was evaluated, or production is
ready.

This phase did not read, list, hash, open, copy, move, delete, modify, dump,
scan, normalize, restore, or commit content under
`/Users/linzezhang/Downloads/IDS_MetaData`. It used no real business content
and created no substitute business dataset. 不得使用虚构 IDS 业务数据、虚构数据库
行、placeholder corpus 或伪造证据；本 phase 的测试输入只引用真实 tracked
contract/task/acceptance identifiers and is explicitly non-runtime contract
evaluation.

## Validation Command
Run from the repository root:

```bash
python3 -B KM_IDSystem/scripts/check_job_state_model.py
```

The command reads tracked engineering contracts and prints one deterministic
JSON object to stdout. It writes no report, database, job, queue, checkpoint,
error log, audit event, cleanup manifest, or runtime output.

## Stop Conditions
- Do not create or execute a queue, worker, scheduler, retry, dead-letter,
  backpressure, lock, automatic lifecycle, crash recovery, or cleanup runtime.
- Do not connect PostgreSQL, modify schema, insert state registry values, or
  create a real job row.
- Do not read raw metadata content or use fake IDS business data, fake database
  rows, fabricated jobs, logs, or evidence.
- Do not enter Phase 3, STAGE-038, or any later implementation in this run.
- Do not upload GitHub, create/merge a PR, mutate issues, reinstall app entries,
  run whole-stage review, batch review, or an upload gate.

## Error Reference Boundary
Rejected candidates return a stable safe code such as
`COMPARE_AND_SET_MISMATCH`, `TRANSITION_NOT_ALLOWED`,
`FENCING_TOKEN_MISMATCH`, `MISSING_TRANSITION_GUARD`,
`MISSING_REQUIRED_REFERENCE`, `EXHAUSTED_RETRY_MUST_DEAD_LETTER`,
`MISSING_RETRY_SCHEDULE_EVIDENCE`, `MISSING_STOP_REASON`,
`FORBIDDEN_REFERENCE`, or `INVALID_CONTRACT`. They do not echo source
content or secrets and do not claim that an audit event was persisted.

## Rollback
Revert only this Phase 2 document, the job-state index/checker, Stage037 and
Stage005 test/validator updates, narrow compatibility changes, batch lock,
roadmap/event update, and rendered owner files. Do not touch Phase 1, prior
stages, raw metadata, PostgreSQL, SQL migrations, source/runtime data,
manifests, evidence, audit logs, reports, indexes, app entries, or GitHub
state.

## 中文 Owner 反馈
STAGE-037 Phase 2 已形成可机器检查、无副作用的统一任务状态转换工程切片。当前
只验证 bounded metadata 候选；重试资格必须带时间引用与证据，取消必须带
`stop_reason`，完整 job envelope 已按 evaluator 与后续持久化责任分层。系统不
创建队列、不运行 worker、不连接数据库，也不执行重试、反压、自动恢复或清理。
`PAUSE_REQUESTED` 显示为“暂停中”，只有 `PAUSED` 才显示“已暂停”。这些结果不
代表真实任务已运行。下一步只能从 `IDS-STAGE037-P3-GATE` 进入独立 Phase 3 异常
场景验证。
