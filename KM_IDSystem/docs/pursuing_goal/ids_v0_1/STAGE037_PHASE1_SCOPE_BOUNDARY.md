# STAGE-037 Phase 1 - Job State Model Scope Boundary

## Identity And Goal
- Stage: `STAGE-037 · 任务状态模型`
- Task: `IDS-V0_1-STAGE037-P1`
- Acceptance: `ACC-STAGE-037`
- Local code: `D07-S001`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Goal:
  `定义 import、archive、parse、ocr、chunk、embed、index、report 的统一 job 状态机。`
- Contract id field: `job_state_model_contract_id`
- P0 source:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-037_任务状态模型.md`
- P0 SHA-256:
  `ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2`

This phase defines a contract only. It does not create or mutate a queue,
worker, registry row, database, schema, lock, checkpoint, task, source file, or
runtime output.

## Authoritative Inputs
- `removable_drive_state_ref`:
  `STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md`
- `storage_budget_ref`: `STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md`
- `safe_mode_ref`: `STAGE011_PHASE2_SAFE_MODE_BASELINE.md`
- `import_idempotency_ref`: `STAGE016_PHASE2_IMPORT_IDEMPOTENCY_SLICE.md`
- `priority_queue_ref`: `STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md`
- `control_plane_schema_ref`:
  `postgresql_control_plane/001_control_plane_schema.sql`
- `database_quality_ref`:
  `database_quality_constraints/stage036_database_quality_constraints_index.json`
- `state_registry_structure_ref`:
  `database_quality_constraints/002_database_quality_constraints.sql`
- `raw_data_boundary_ref`: `IDS_METADATA_RAW_DATA_BOUNDARY.md`

The tracked `ids_jobs` baseline has `job_id`, `job_type`, `job_state`,
`parent_job_id`, `retry_count`, `max_retries`, `stop_reason`, and bounded
control-plane payload fields. Phase 1 treats those as schema facts. Additional
fields below are future contract requirements, not claims about installed SQL.

## Canonical Job Types
Canonical job types:
`IMPORT, ARCHIVE, PARSE, OCR, CHUNK, EMBED, INDEX, REPORT`

| Type | Stable target identity | Future output boundary |
|---|---|---|
| `IMPORT` | STAGE-013 fingerprint or STAGE-016 import identity | document/job refs only |
| `ARCHIVE` | archive hash plus extraction generation | archive manifest and reingest refs |
| `PARSE` | document id plus content/contract version | parser artifact refs |
| `OCR` | document/page-set plus OCR contract version | OCR artifact refs |
| `CHUNK` | document plus parse artifact version | chunk-set refs |
| `EMBED` | chunk-set plus embedding contract/model version | vector/index-input refs |
| `INDEX` | index id and immutable index version | built-index and switch-candidate refs |
| `REPORT` | subject plus evidence/report snapshot version | immutable report snapshot refs |

Job types identify orchestration intent; they do not authorize source reads,
provider calls, parsing, OCR, embedding, indexing, or report generation.

## Canonical Lifecycle States
Canonical job states:
`CREATED, QUEUED, CLAIMED, RUNNING, PAUSE_REQUESTED, PAUSED, RETRY_WAIT, SUCCEEDED, FAILED, DEAD_LETTERED, CANCELLED`

The registry namespace is `state_namespace=job_state`, and this state set is
published as `state_model_version=ids.job_state.v1` with introduced version
`v0.1`. Phase 1 defines values and compatibility only; it inserts no registry
row. Values cannot be renamed or reassigned in place. Future retirement is
versioned, and transition rules are versioned separately from membership.

- `CREATED`: identity and bounded input refs accepted; not yet admitted.
- `QUEUED`: eligible for a future worker claim after all gates pass.
- `CLAIMED`: one worker owns a time-bounded claim lease but has not started
  side effects.
- `RUNNING`: current attempt is executing under the same live lease and
  `fencing_token`.
- `PAUSE_REQUESTED`: a running attempt must reach a safe checkpoint and stop.
- `PAUSED`: no worker may progress the job until owner revalidation succeeds.
- `RETRY_WAIT`: retryable failure is recorded and waits for `next_eligible_at`.
- `SUCCEEDED`: terminal success with validated output and audit refs.
- `FAILED`: terminal permanent failure; manual rerun creates a new linked job.
- `DEAD_LETTERED`: terminal retry-exhausted or owner-intervention state.
- `CANCELLED`: terminal cancellation with source and evidence preserved.

terminal states: SUCCEEDED, FAILED, DEAD_LETTERED, CANCELLED

`pause_reason_code`, retry disposition, resource gate, worker identity, error
class, cleanup status, and human label are separate dimensions. In particular,
pause reason is not a job state. This prevents states such as `LOW_DISK` or
`DRIVE_OFFLINE` from becoming irreversible workflow vocabulary.

## Allowed Transition Matrix
Every mutation uses compare-and-set over `job_id`, `expected_state`, and
`state_version`; a successful mutation increments `state_version` and emits an
append-only transition audit. Any unlisted transition fails closed.

| From | Allowed to | Required guard |
|---|---|---|
| `CREATED` | `QUEUED`, `CANCELLED` | identity/idempotency and admission result |
| `QUEUED` | `CLAIMED`, `PAUSED`, `CANCELLED` | gate pass or explicit pause/cancel reason |
| `CLAIMED` | `RUNNING`, `PAUSE_REQUESTED`, `RETRY_WAIT` | live claim lease; pause intent or lease-loss evidence |
| `RUNNING` | `SUCCEEDED`, `PAUSE_REQUESTED`, `RETRY_WAIT`, `FAILED` | live lease and `fencing_token`; validated output/checkpoint/error evidence |
| `PAUSE_REQUESTED` | `PAUSED`, `CANCELLED`, `RETRY_WAIT` | checkpoint/quarantine complete; atomically revoke lease/lock and advance fencing before terminal cancellation |
| `PAUSED` | `QUEUED`, `CANCELLED` | owner revalidation and resource gates pass |
| `RETRY_WAIT` | `QUEUED`, `PAUSED`, `DEAD_LETTERED`, `CANCELLED` | `retry_count` and resource gates decide requeue, pause, dead-letter, or cancel |

Required transition examples include `CREATED -> QUEUED`, `QUEUED -> CLAIMED`,
`CLAIMED -> RUNNING`, `RUNNING -> SUCCEEDED`,
`RUNNING -> PAUSE_REQUESTED`, `PAUSE_REQUESTED -> PAUSED`,
`PAUSE_REQUESTED -> CANCELLED`, `PAUSED -> QUEUED`,
`RUNNING -> RETRY_WAIT`, `RETRY_WAIT -> QUEUED`,
`RETRY_WAIT -> PAUSED`, `RETRY_WAIT -> DEAD_LETTERED`, and
`RUNNING -> FAILED`.

RUNNING never transitions directly to CANCELLED. A cancel request first uses
`RUNNING -> PAUSE_REQUESTED`; completion of `PAUSE_REQUESTED -> CANCELLED`
must checkpoint or quarantine attempt-owned partial outputs. The same
cancellation transaction atomically revokes the claim lease and lock,
increments the fencing token, and writes state plus audit in one transaction.
Any later stale worker commit fails. The same revocation path applies to a
claimed job before cancellation. Jobs without an active lease (`CREATED`,
`QUEUED`, `PAUSED`, `RETRY_WAIT`) may cancel directly only after proving that
no claim/lock is active.

The active execution states: CLAIMED, RUNNING, PAUSE_REQUESTED. Every
transition that leaves active execution for `PAUSED`, `RETRY_WAIT`,
`SUCCEEDED`, `FAILED`, or `CANCELLED` uses one deactivation transaction. That
transaction validates the current lease or recorded lease-expiry evidence,
atomically records the destination state and audit, revokes the claim lease and lock,
increments the fencing token, and prevents every stale worker commit. This
applies to `CLAIMED -> RETRY_WAIT`, `RUNNING -> SUCCEEDED`,
`RUNNING -> RETRY_WAIT`, `RUNNING -> FAILED`,
`PAUSE_REQUESTED -> PAUSED`, `PAUSE_REQUESTED -> RETRY_WAIT`, and
`PAUSE_REQUESTED -> CANCELLED`. A transition between active execution states
keeps the same live lease and token; no non-active destination may retain an
active worker lease. A recovery coordinator handling an expired lease performs
the same compare-and-set deactivation with expiry evidence and a new fencing
token before any retry can be admitted.

Terminal states are immutable. Owner-requested rerun or recovery creates a new
job linked by a future `supersedes_job_id`/`parent_job_id`; it does not rewrite
historical terminal evidence.

## Job Control Envelope
The future `job_control_envelope` is bounded metadata, never source content. It
must include or reference:

- identity: `job_id`, `job_type`, `job_state`, `state_version`,
  `idempotency_key`, `transition_request_id`, `parent_job_id`, and optional
  dependency refs;
- attempt: `attempt_id`, `retry_count`, `max_retries`, `retry_pending`,
  `next_eligible_at`;
- work refs: `input_refs`, `output_refs`, `checkpoint_ref`, and contract/model
  versions without raw bodies or plaintext secrets;
- worker claim: `lease_owner_ref`, `lease_expires_at`, `fencing_token`, and
  `lock_key`;
- control: priority ref, `pause_reason_code`, stop reason, owner action ref,
  and expected resource-gate refs;
- failure/audit: safe error code, `error_ref`, `audit_ref`, transition actor,
  timestamps, and a future `cleanup_manifest_ref`.

The associated outputs are:
- `job_transition_event`: unique `transition_request_id`, previous/current
  state, state version, safe reason, actor ref, timestamp, and audit ref; replay
  of the same request returns the original result and cannot emit a second
  transition;
- `job_checkpoint_payload`: resumable cursor refs and attempt ownership without
  raw source content;
- `job_error_payload`: error class/code, retryable flag, safe Chinese message,
  evidence ref, and no source body/secret;
- `job_cleanup_manifest`: exact attempt-owned paths/refs eligible for cleanup;
- `human_status_projection`: Chinese enterprise-facing state, reason, next
  action, and whether owner attention is required;
- `phase2_ready_contract`: authorizes only a later machine-readable static
  contract/checker slice after this Phase 1 evidence passes.

## Worker Claim, Retry, And Dead-Letter Boundary
- A future worker must atomically acquire one claim lease and lock before
  `QUEUED -> CLAIMED`; only the live `fencing_token` may commit a transition or
  output reference.
- Lease renewal cannot change job state. After `lease_expires_at`, a
  stale worker cannot write, publish output, release a newer lock, or mark
  success.
- Worker loss records an audit event and routes an unfinished claim/attempt to
  `RETRY_WAIT`; it never silently returns to success. When budget remains and
  an `attempt_id` has been claimed, worker loss consumes one retry opportunity
  by reserving exactly one pending admission. Exhausted worker loss follows the
  no-pending exhaustion route below. A duplicate lease-expiry event with the
  same `transition_request_id` is idempotent and cannot reserve or consume the
  budget twice.
- `max_retries is the number of retry attempts after the initial attempt`.
  The initial attempt starts with `retry_count=0`, and
  `total_attempt_limit = 1 + max_retries`. `max_retries` is immutable after job
  creation.
- Every retryable attempt failure first enters `RETRY_WAIT` through the same
  deactivation transaction. When `retry_count < max_retries`, that transaction
  writes `retry_pending=true` and `retry_disposition=eligible` without
  incrementing the counter. Creating the pending reservation is compare-and-set.
  `RETRY_WAIT -> QUEUED increments retry_count atomically` only when
  `retry_count < max_retries`, all resource gates pass, and the transition
  request is new; it also clears `retry_pending`. RETRY_WAIT -> PAUSED preserves retry_pending=true
  when a resource gate remains blocked. PAUSED -> QUEUED with retry_pending=true increments retry_count atomically
  and clears retry_pending under the same admission compare-and-set. An ordinary pause has
  `retry_pending=false` and does not increment the retry counter on resume.
  Therefore the `RETRY_WAIT -> PAUSED -> QUEUED` path cannot bypass total_attempt_limit.
- The exhaustion rule is `retry_count == max_retries enters RETRY_WAIT with retry_pending=false`;
  the same deactivation transaction writes `retry_disposition=exhausted` and
  bounded failure evidence. Its only legal next transition is RETRY_WAIT -> DEAD_LETTERED.
  The fail-closed rule is `resource gates cannot pause an exhausted retry`, and
  an exhausted retry cannot requeue. This
  keeps terminalization explicit and audited; RUNNING -> DEAD_LETTERED remains forbidden.
  A permanent non-retryable failure enters `FAILED`.
- Exact retry delay, jitter, error taxonomy, and dead-letter policy are owned
  by STAGE-039. Phase 1 uses `POLICY_VALUE_DEFERRED_TO_STAGE039_040_041` and
  does not invent numeric policy values.

## Pause, Backpressure, And Automatic Lifecycle Boundary
- STAGE-011 safe-mode codes remain authoritative pause reasons, including
  `SAFE_MODE_DRIVE_OFFLINE`, `SAFE_MODE_STORAGE_BLOCKED`, and
  `SAFE_MODE_API_BUDGET_EXCEEDED`.
- STAGE-009 blocking evidence such as `BUDGET_BLOCKED_LOW_FREE`,
  `EXTERNAL_ROOT_NOT_READY`, and `UNBOUNDED_OUTPUT_RISK` pauses only affected
  jobs before new side effects.
- At `next_eligible_at`, if a resource gate remains blocked, the job records
  the current pause evidence and uses `RETRY_WAIT -> PAUSED`; it does not
  requeue, consume another retry, or remain misleadingly eligible. Resume still
  requires the normal owner/resource revalidation path.
- Drive reconnect does not resume work by itself. STAGE-008 and STAGE-011
  remain `auto_resume=false`; owner revalidation plus a fresh storage/path/
  permission/budget check is required before `PAUSED -> QUEUED`.
- Queue pressure, dependency unavailability, lock contention, index failure,
  owner hold, and safe shutdown use reason/evidence fields, not new states.
- `RUNNING -> PAUSE_REQUESTED` requires a bounded checkpoint deadline. If a
  worker cannot checkpoint safely, the attempt fails closed into recovery/
  retry handling; it must not continue uncontrolled.
- STAGE-040 and STAGE-042 own runtime backpressure and automatic lifecycle
  policy. Phase 1 does not enable auto run, resume, shutdown, or cleanup.

## Idempotency And Lock Granularity
- `IMPORT` must preserve the STAGE-016 key
  `ids-import-file-sha256-{sha256}` and may not substitute a path/name-only key.
- Other jobs derive `idempotency_key` from `job_type`, stable source/output
  identity ref, `operation_contract_version`,
  `normalized_parameters_sha256`, and parent/output version. The future digest
  must be deterministic and must not contain raw data or secrets.
- Duplicate creation with the same key returns the existing active/succeeded
  job reference; it does not enqueue duplicate work. A deliberate rerun uses a
  new operation/output version and an explicit lineage link.
- The required lock granularity is the smallest target whose concurrent mutation would
  conflict: import fingerprint/batch, archive hash+generation, document+
  processing stage/version, index id+version or index-switch scope, and report
  subject+snapshot version. A global project lock is not the default.
- Lock acquisition/renewal/release is compare-and-set, lease-bound, audited,
  and fenced. STAGE-041 owns implementation and exact timeouts.

## Half-Product Cleanup Rules
The cleanup allowlist contains only attempt-owned temporary artifacts created
under an approved staging/cache boundary. Every candidate binds `attempt_id`,
creator job, `approved_root_id`, canonical approved-root identity, root-relative
path, artifact class, rebuildability, retention/hold status,
`cleanup_manifest_ref`, and immutable `lstat identity` fields including
`st_dev`, `st_ino`, and `file_type`.

The following are never cleanup targets: `00_ORIGINAL_RAW_DATA`, source files,
source/runtime databases, manifest, evidence ledger, audit log, report snapshot,
active index, validated checkpoint needed for retry, owner-held artifact, or an
output referenced by a succeeded job.

Unknown ownership, path escape, missing manifest, active lease, legal/owner
hold, or a reference from durable evidence blocks cleanup. A symlink is never
an eligible cleanup target and no path component may be followed through a
symlink. Before validation, STAGE-044 must acquire an exclusive cleanup namespace lock
keyed by `approved_root_id` and the candidate parent directory. It must prove
writer quiescence: every producer/cleanup lease for that namespace is absent or
fenced, and no creation, rename, replacement, or deletion can enter the
namespace while the lock is held. The fail-closed rule is
`cannot prove writer quiescence blocks cleanup`; an unmanaged or advisory-only
namespace is never deletion eligible.

With that exclusion active, STAGE-044 must open the approved root as a trusted
`dirfd`, traverse the root-relative path with `openat` plus `O_NOFOLLOW`, and
use `unlinkat` relative to that same directory descriptor. It must revalidate immediately before deletion
that canonical containment, owner attempt, file
type, and `lstat` identity still match the manifest. The lock remains held through unlinkat,
so the validated directory entry cannot be swapped in the final TOCTOU window.
Any TOCTOU change or identity mismatch blocks deletion. Cleanup must be
idempotent, separately audited, and unable to change the terminal job result.
STAGE-044 implements it; Phase 1 deletes nothing.

## Human Status Projection
Machine state remains canonical while Chinese UI/report text is a projection:

| Machine state | Owner-facing label | Default owner action |
|---|---|---|
| `CREATED`, `QUEUED` | `等待处理` | 查看优先级或暂停 |
| `CLAIMED`, `RUNNING` | `处理中` | 查看进度；必要时安全暂停 |
| `PAUSE_REQUESTED`, `PAUSED` | `已暂停` | 查看原因并完成复核 |
| `RETRY_WAIT` | `等待重试` | 查看安全错误与下次资格时间 |
| `SUCCEEDED` | `已完成` | 查看已验证输出引用 |
| `FAILED` | `处理失败` | 查看原因并决定是否新建重跑 |
| `DEAD_LETTERED` | `需要人工处理` | 人工复核，不自动继续 |
| `CANCELLED` | `已取消` | 无自动副作用 |

Feedback must state what stopped, which safe evidence exists, what was not
executed, and the next owner action. It must not claim readiness or success
without real runtime evidence.

## Boundary And Stop Conditions
- `NO_PHASE2`, `NO_QUEUE_IMPLEMENTATION`, `NO_WORKER_EXECUTION`,
  `NO_STATE_REGISTRY_WRITE`, `NO_SCHEMA_CHANGE`, `NO_POSTGRES_CONNECTION`,
  `NO_RUNTIME_OUTPUT`, `NO_FAKE_DATA`, and `NO_STAGE038` are mandatory.
- PostgreSQL remains control-plane only; no raw file, raw row, document/OCR
  body, vector payload, report binary, raw log, secret, or unbounded artifact.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and untouched.
- 不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据.
- Do not move, delete, or overwrite `00_ORIGINAL_RAW_DATA`, source data,
  manifest, evidence ledger, audit log, report snapshot, or active index.
- Do not enter STAGE-038, STAGE-039, STAGE-040, STAGE-041, STAGE-042,
  STAGE-043, or STAGE-044 implementation; install dependencies; start services;
  call APIs; upload GitHub; create/merge PRs; reinstall app entries; or run
  stage/batch review or an upload gate.
- Stop if real task execution is required without owner authorization, cleanup
  ownership is uncertain, a schema cannot roll back, a shared contract
  conflicts, or a test fails for an unexplained reason.

## Rollback
Revert only the Phase 1 entry/scope documents, focused tests, Stage005
validator/test changes, batch lock, roadmap/event, narrow compatibility changes,
and rendered owner views. Do not touch prior Stage evidence, SQL, state registry,
raw metadata, source/runtime data, manifests, evidence, audit logs, reports,
indexes, app entries, or GitHub state.
